# forecasting.py
from __future__ import annotations

from typing import Tuple
import numpy as np
import pandas as pd

# ---- ML imports (safe) ----
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    SKLEARN_OK = True
except Exception:
    LinearRegression = None
    RandomForestRegressor = None
    GradientBoostingRegressor = None
    SKLEARN_OK = False


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_date_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, dayfirst=True, errors="coerce")


def load_coffee_weird_layout(uploaded_file) -> pd.DataFrame:
    df = pd.read_csv(uploaded_file)
    df = normalize_cols(df)

    if "Date" not in df.columns:
        raise ValueError("Coffee file must contain a 'Date' column (as in your file).")

    first_date = df.loc[0, "Date"] if len(df) > 0 else None
    has_unnamed = any(str(c).lower().startswith("unnamed") for c in df.columns)

    if pd.isna(first_date) and has_unnamed and len(df.columns) >= 3:
        sales_cols = [c for c in df.columns if c != "Date"]
        product_names = [str(df.loc[0, c]).strip() for c in sales_cols]

        df = df[["Date"] + sales_cols].copy()
        df.columns = ["Date"] + product_names
        df = df.iloc[1:].copy()

        df["Date"] = parse_date_series(df["Date"])
        df = df.dropna(subset=["Date"])

        for c in df.columns:
            if c != "Date":
                df[c] = pd.to_numeric(df[c], errors="coerce")

        long = df.melt(id_vars=["Date"], var_name="product", value_name="units_sold")
        long = long.dropna(subset=["units_sold"])
        long["product"] = long["product"].astype(str).str.strip()
        long = long.rename(columns={"Date": "date"})
        return long[["date", "product", "units_sold"]]

    lower_cols = [c.lower().strip() for c in df.columns]
    if "product" in lower_cols and any(x in lower_cols for x in ["number sold", "units_sold", "units sold", "sold"]):
        colmap = {}
        for c in df.columns:
            cl = c.lower().strip()
            if cl == "date":
                colmap[c] = "Date"
            elif cl == "product":
                colmap[c] = "Product"
            elif cl in ["number sold", "units_sold", "units sold", "sold"]:
                colmap[c] = "Number Sold"
        df = df.rename(columns=colmap)

        df["Date"] = parse_date_series(df["Date"])
        df["Number Sold"] = pd.to_numeric(df["Number Sold"], errors="coerce")
        df = df.dropna(subset=["Date"])

        out = df[["Date", "Product", "Number Sold"]].copy()
        out.columns = ["date", "product", "units_sold"]
        out["product"] = out["product"].astype(str).str.strip()
        return out

    raise ValueError("Coffee file format not recognised.")


def load_simple_product_file(uploaded_file, product_name: str) -> pd.DataFrame:
    df = pd.read_csv(uploaded_file)
    df = normalize_cols(df)

    date_col = None
    for cand in ["Date", "date", "DATE"]:
        if cand in df.columns:
            date_col = cand
            break
    if date_col is None:
        raise ValueError(f"{product_name} file must contain a Date column.")

    sold_col = None
    for cand in ["Number Sold", "number sold", "Units Sold", "units_sold", "Units", "Sold", "sold"]:
        if cand in df.columns:
            sold_col = cand
            break
    if sold_col is None:
        raise ValueError(f"{product_name} file must contain a Number Sold / Units Sold column.")

    df[date_col] = parse_date_series(df[date_col])
    df[sold_col] = pd.to_numeric(df[sold_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    out = df[[date_col, sold_col]].copy()
    out.columns = ["date", "units_sold"]
    out["product"] = product_name
    return out[["date", "product", "units_sold"]]


def moving_average(s: pd.Series, window: int = 7) -> pd.Series:
    s = s.sort_index()
    return s.rolling(window=window, min_periods=max(1, window // 2)).mean()


def simple_forecast(series: pd.Series, days: int) -> pd.DataFrame:
    s = series.dropna()
    if len(s) < 2:
        future = np.repeat(float(s.iloc[-1]) if len(s) else 0.0, days)
        return pd.DataFrame({"predicted": future})

    window = min(14, max(3, len(s) // 5))
    base = s.rolling(window=window).mean().dropna()
    last = float(base.iloc[-1]) if len(base) else float(s.iloc[-1])

    n = min(21, len(s))
    y = s.iloc[-n:].values.astype(float)
    x = np.arange(len(y))
    slope = np.polyfit(x, y, 1)[0] if len(y) >= 2 else 0.0

    future = [max(0.0, last + slope * i) for i in range(1, days + 1)]
    return pd.DataFrame({"predicted": future})


def linear_regression_forecast(series: pd.Series, days: int) -> Tuple[pd.DataFrame, dict]:
    if not SKLEARN_OK or LinearRegression is None:
        return simple_forecast(series, days), {"ok": False, "reason": "scikit-learn not installed"}

    s = series.dropna()
    if len(s) < 5:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough data (need ~5+ points)"}

    X = np.arange(len(s)).reshape(-1, 1)
    y = s.values.astype(float)

    model = LinearRegression()
    model.fit(X, y)
    r2 = float(model.score(X, y))

    X_future = np.arange(len(s), len(s) + days).reshape(-1, 1)
    y_future = np.clip(model.predict(X_future), 0, None)

    pred_df = pd.DataFrame({"predicted": y_future})
    info = {
        "ok": True,
        "type": "linear_regression",
        "slope_per_day": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r2_train": r2,
    }
    return pred_df, info


def make_rf_features(series: pd.Series) -> pd.DataFrame:
    s = series.copy()
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("D").fillna(0)

    df = pd.DataFrame({"y": s})
    for lag in [1, 2, 3, 7, 14]:
        df[f"lag_{lag}"] = df["y"].shift(lag)

    df["roll_mean_7"] = df["y"].shift(1).rolling(7).mean()
    df["roll_mean_14"] = df["y"].shift(1).rolling(14).mean()

    df["dow"] = df.index.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["day_of_month"] = df.index.day
    df["month"] = df.index.month
    return df.dropna()


def random_forest_forecast(series: pd.Series, days: int) -> Tuple[pd.DataFrame, dict]:
    if not SKLEARN_OK or RandomForestRegressor is None:
        return simple_forecast(series, days), {"ok": False, "reason": "scikit-learn not installed"}

    s = series.dropna()
    if len(s) < 30:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough data (need ~30+ days)"}

    s = s.copy()
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("D").fillna(0)

    df = make_rf_features(s)
    if len(df) < 20:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough feature rows after lags"}

    X = df.drop(columns=["y"])
    y = df["y"].astype(float)

    model = RandomForestRegressor(
        n_estimators=400, random_state=42, min_samples_leaf=2, n_jobs=-1
    )
    model.fit(X, y)
    r2 = float(model.score(X, y))

    current = s.copy()
    last_date = current.index.max()
    preds = []

    def get_val(d: pd.Timestamp) -> float:
        return float(current.loc[d]) if d in current.index else 0.0

    for i in range(1, days + 1):
        next_date = last_date + pd.Timedelta(days=i)
        prev_7 = current.loc[(next_date - pd.Timedelta(days=7)) : (next_date - pd.Timedelta(days=1))]
        prev_14 = current.loc[(next_date - pd.Timedelta(days=14)) : (next_date - pd.Timedelta(days=1))]

        row = {
            "lag_1": get_val(next_date - pd.Timedelta(days=1)),
            "lag_2": get_val(next_date - pd.Timedelta(days=2)),
            "lag_3": get_val(next_date - pd.Timedelta(days=3)),
            "lag_7": get_val(next_date - pd.Timedelta(days=7)),
            "lag_14": get_val(next_date - pd.Timedelta(days=14)),
            "roll_mean_7": float(prev_7.mean()) if len(prev_7) else 0.0,
            "roll_mean_14": float(prev_14.mean()) if len(prev_14) else 0.0,
            "dow": int(next_date.dayofweek),
            "is_weekend": int(next_date.dayofweek >= 5),
            "day_of_month": int(next_date.day),
            "month": int(next_date.month),
        }

        y_next = float(model.predict(pd.DataFrame([row]))[0])
        y_next = max(0.0, y_next)
        preds.append(y_next)
        current.loc[next_date] = y_next

    pred_df = pd.DataFrame({"predicted": np.array(preds, dtype=float)})
    info = {"ok": True, "type": "random_forest", "r2_train": r2}
    return pred_df, info


def gradient_boosting_forecast(series: pd.Series, days: int) -> Tuple[pd.DataFrame, dict]:
    if not SKLEARN_OK or GradientBoostingRegressor is None:
        return simple_forecast(series, days), {"ok": False, "reason": "scikit-learn not installed"}

    s = series.dropna()
    if len(s) < 30:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough data (need ~30+ days)"}

    s = s.copy()
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("D").fillna(0)

    df = make_rf_features(s)
    if len(df) < 20:
        return simple_forecast(series, days), {"ok": False, "reason": "not enough feature rows after lags"}

    X = df.drop(columns=["y"])
    y = df["y"].astype(float)

    model = GradientBoostingRegressor(
        random_state=42, n_estimators=400, learning_rate=0.05, max_depth=3
    )
    model.fit(X, y)
    r2 = float(model.score(X, y))

    current = s.copy()
    last_date = current.index.max()
    preds = []

    def get_val(d: pd.Timestamp) -> float:
        return float(current.loc[d]) if d in current.index else 0.0

    for i in range(1, days + 1):
        next_date = last_date + pd.Timedelta(days=i)
        prev_7 = current.loc[(next_date - pd.Timedelta(days=7)) : (next_date - pd.Timedelta(days=1))]
        prev_14 = current.loc[(next_date - pd.Timedelta(days=14)) : (next_date - pd.Timedelta(days=1))]

        row = {
            "lag_1": get_val(next_date - pd.Timedelta(days=1)),
            "lag_2": get_val(next_date - pd.Timedelta(days=2)),
            "lag_3": get_val(next_date - pd.Timedelta(days=3)),
            "lag_7": get_val(next_date - pd.Timedelta(days=7)),
            "lag_14": get_val(next_date - pd.Timedelta(days=14)),
            "roll_mean_7": float(prev_7.mean()) if len(prev_7) else 0.0,
            "roll_mean_14": float(prev_14.mean()) if len(prev_14) else 0.0,
            "dow": int(next_date.dayofweek),
            "is_weekend": int(next_date.dayofweek >= 5),
            "day_of_month": int(next_date.day),
            "month": int(next_date.month),
        }

        y_next = float(model.predict(pd.DataFrame([row]))[0])
        y_next = max(0.0, y_next)
        preds.append(y_next)
        current.loc[next_date] = y_next

    pred_df = pd.DataFrame({"predicted": np.array(preds, dtype=float)})
    info = {"ok": True, "type": "gradient_boosting", "r2_train": r2}
    return pred_df, info


def forecast_series_for_mode(
    daily_total: pd.Series, forecast_days: int, mode_name: str
) -> tuple[pd.Series, dict]:
    if mode_name == "AI (Heuristic)":
        pred_raw = simple_forecast(daily_total, days=forecast_days)
        model_info = {"ok": True, "type": "heuristic"}
    elif mode_name == "ML (Linear Regression)":
        pred_raw, model_info = linear_regression_forecast(daily_total, days=forecast_days)
    elif mode_name == "AI (Random Forest)":
        pred_raw, model_info = random_forest_forecast(daily_total, days=forecast_days)
    else:
        pred_raw, model_info = gradient_boosting_forecast(daily_total, days=forecast_days)

    last_date = daily_total.index.max()
    future_index = pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_days, freq="D")
    pred_series = pd.Series(pred_raw["predicted"].values, index=future_index)
    return pred_series, model_info


def make_pred_band(pred: pd.Series, recent_actual: pd.Series) -> pd.DataFrame:
    recent = recent_actual.dropna().tail(21)
    spread = float(recent.std()) if len(recent) >= 5 else 0.0
    lower = (pred - spread).clip(lower=0)
    upper = (pred + spread).clip(lower=0)
    return pd.DataFrame({"predicted": pred, "lower": lower, "upper": upper})


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.where(y_true == 0, np.nan, y_true)
    mape = np.nanmean(np.abs((y_true - y_pred) / denom)) * 100.0
    return float(mape) if np.isfinite(mape) else float("nan")


def evaluate_models_time_holdout(
    daily_total: pd.Series,
    holdout_days: int = 14,
    modes: list[str] | None = None,
) -> Tuple[pd.DataFrame, str]:
    if modes is None:
        modes = [
            "AI (Heuristic)",
            "ML (Linear Regression)",
            "AI (Random Forest)",
            "ML (Gradient Boosting)",
        ]

    s = daily_total.copy().sort_index()
    s = s.asfreq("D").fillna(0)

    if len(s) < (holdout_days + 10):
        cols = ["MAE", "RMSE", "MAPE_%", "Notes"]
        df = pd.DataFrame(index=modes, columns=cols)
        df["Notes"] = f"Not enough data for holdout ({holdout_days}d). Need ~{holdout_days+10}+ days."
        return df.reset_index(names="Model"), ""

    train = s.iloc[:-holdout_days]
    test = s.iloc[-holdout_days:]

    rows = []
    for m in modes:
        pred_s, info = forecast_series_for_mode(train, holdout_days, m)
        pred_s = pred_s.reindex(test.index).fillna(0)

        y_true = test.values.astype(float)
        y_pred = pred_s.values.astype(float)

        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mape = _safe_mape(y_true, y_pred)

        note = ""
        if isinstance(info, dict) and not info.get("ok", True):
            note = str(info.get("reason", ""))

        rows.append({"Model": m, "MAE": mae, "RMSE": rmse, "MAPE_%": mape, "Notes": note})

    metrics = pd.DataFrame(rows).sort_values("RMSE", ascending=True).reset_index(drop=True)
    best_mode = str(metrics.iloc[0]["Model"]) if not metrics.empty else ""
    return metrics, best_mode