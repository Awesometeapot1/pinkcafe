# pages/predictions.py
from __future__ import annotations

import math
import pandas as pd
import streamlit as st

from theme import render_pink_header
from forecasting import (
    load_coffee_weird_layout,
    load_simple_product_file,
    moving_average,
    forecast_series_for_mode,
    make_pred_band,
    evaluate_models_time_holdout,
)

# ----------------------------
# Helpers
# ----------------------------
def _section(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.write("")


def _metric_help_block() -> None:
    with st.expander("What do MAE / RMSE / MAPE mean?"):
        st.markdown(
            """
**MAE (Mean Absolute Error)**  
Average “how far off” the predictions are. Lower = better.

**RMSE (Root Mean Squared Error)**  
Like MAE, but punishes big mistakes more.

**MAPE (%) (Mean Absolute Percentage Error)**  
Error as a percentage. Lower = better. (Can be unstable when actual values are 0.)
            """
        )


def _model_explanations() -> dict[str, str]:
    return {
        "AI (Heuristic)": "Baseline using recent averages + a simple trend. Stable on small/noisy data.",
        "ML (Linear Regression)": "Fits a straight-line time trend. Good for steady growth/decline.",
        "AI (Random Forest)": "Non-linear trees with lag + weekday features. Often strong for weekday/weekend effects.",
        "ML (Gradient Boosting)": "Boosted trees with the same features. Powerful for complex patterns.",
    }


def _model_label_map() -> dict[str, str]:
    return {
        "AI (Heuristic)": "Heuristic (AI)",
        "ML (Linear Regression)": "Linear Regression (ML)",
        "AI (Random Forest)": "Random Forest (AI)",
        "ML (Gradient Boosting)": "Gradient Boosting (ML)",
    }


def _recommendation_text(best_mode: str, holdout_days: int, label_map: dict[str, str]) -> str:
    if not best_mode:
        return (
            "Not enough data to compare models fairly yet. "
            "Use **Heuristic (AI)** for now."
        )
    return (
        f"Based on the **last {holdout_days} days**, the most accurate model was:\n\n"
        f"### ✅ Recommended: **{label_map.get(best_mode, best_mode)}**"
    )


def _download_csv_button(label: str, df: pd.DataFrame, filename: str) -> None:
    if df is None or df.empty:
        st.caption("Nothing to download yet.")
        return
    csv_bytes = df.to_csv(index=True).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def _detect_coffee_layout(uploaded_file) -> str:
    try:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        df = pd.read_csv(uploaded_file, nrows=2)
        cols = [str(c).strip() for c in df.columns]
        has_unnamed = any(str(c).lower().startswith("unnamed") for c in cols)

        if "Date" in cols:
            first_date = df.loc[0, "Date"] if len(df) else None
            if pd.isna(first_date) and has_unnamed:
                return "Coffee format detected: Weird wide layout (product names in first row)."
            lower_cols = [c.lower() for c in cols]
            if "product" in lower_cols and any(
                x in lower_cols for x in ["number sold", "units sold", "units_sold", "sold"]
            ):
                return "Coffee format detected: Long/stacked layout (Date, Product, Units)."
            return "Coffee format detected: Standard layout."
        return "Coffee format: Unknown (no 'Date' column found in first rows)."
    except Exception:
        return "Coffee format: Could not detect (read error)."
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def _data_quality_checks(df_all: pd.DataFrame, daily_total: pd.Series) -> dict[str, str | int | float]:
    checks: dict[str, str | int | float] = {}

    if df_all.empty or daily_total.empty:
        checks["status"] = "No data loaded."
        return checks

    checks["rows_loaded"] = int(len(df_all))
    checks["unique_dates"] = int(df_all["date"].nunique()) if "date" in df_all.columns else 0
    checks["unique_products"] = int(df_all["product"].nunique()) if "product" in df_all.columns else 0

    start = pd.to_datetime(df_all["date"]).min()
    end = pd.to_datetime(df_all["date"]).max()
    checks["date_range"] = f"{start.date()} → {end.date()}"

    if all(c in df_all.columns for c in ["date", "product"]):
        checks["duplicate_date_product_rows"] = int(df_all.duplicated(subset=["date", "product"]).sum())

    if "units_sold" in df_all.columns:
        neg = (pd.to_numeric(df_all["units_sold"], errors="coerce").fillna(0) < 0).sum()
        checks["negative_units_rows"] = int(neg)

    raw_days = pd.to_datetime(df_all["date"]).dt.normalize().unique()
    raw_days = pd.DatetimeIndex(raw_days).sort_values()
    if len(raw_days):
        full_raw = pd.date_range(raw_days.min(), raw_days.max(), freq="D")
        checks["missing_days_filled_with_0"] = int(len(full_raw) - len(raw_days))
    else:
        checks["missing_days_filled_with_0"] = 0

    s = daily_total.copy().sort_index()
    zeros = int((s.values == 0).sum())
    checks["days_with_zero_total"] = zeros
    checks["pct_days_zero_total"] = float((zeros / len(s) * 100.0) if len(s) else 0.0)

    return checks


def _buffer_from_disagreement(future_models_df: pd.DataFrame, next_days: int = 7) -> tuple[float, str]:
    if future_models_df is None or future_models_df.empty:
        return 0.10, "Default buffer (no disagreement data)."

    df = future_models_df.head(next_days).copy()
    mean = df.mean(axis=1)
    std = df.std(axis=1)
    ratio = (std / mean.replace(0, pd.NA)).fillna(0)

    avg_cv = float(ratio.mean()) if len(ratio) else 0.0

    if avg_cv < 0.10:
        return 0.05, "Low model disagreement (stable forecast)."
    if avg_cv < 0.25:
        return 0.10, "Moderate disagreement (normal uncertainty)."
    if avg_cv < 0.50:
        return 0.15, "High disagreement (be more cautious)."
    return 0.25, "Very high disagreement (forecast varies a lot by model)."


def _apply_filters(
    df_all: pd.DataFrame,
    selected_products: list[str],
    selected_days: list[int],
    date_start,
    date_end,
) -> pd.DataFrame:
    """
    selected_days: list of integers 0=Monday ... 6=Sunday
    selected_products: list of product names (exact match)
    """
    df = df_all.copy()

    # Date range
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df[df["date"].notna()].copy()
    df = df[(df["date"] >= pd.to_datetime(date_start)) & (df["date"] <= pd.to_datetime(date_end))].copy()

    # Weekday filter
    if selected_days:
        df = df[df["date"].dt.dayofweek.isin(selected_days)].copy()
    else:
        # no days selected — return empty so UI can warn
        return df.iloc[0:0].copy()

    # Product filter
    if selected_products:
        df = df[df["product"].isin(selected_products)].copy()
    else:
        # no products selected — return empty so UI can warn
        return df.iloc[0:0].copy()

    return df


# ----------------------------
# Page
# ----------------------------
def page_predictions_dashboard() -> None:
    # Role safety check (defense in depth)
    role = st.session_state.get("role")
    if role not in {"admin", "manager", "staff"}:
        st.error("Access denied. Please log in again.")
        st.stop()

    render_pink_header(
        "Predictions",
        "Upload café CSVs → understand trends → compare models → export forecasts.",
    )

    mode_help = _model_explanations()
    modes = list(mode_help.keys())
    label_map = _model_label_map()

    # STEP 1 — UPLOAD
    _section("Step 1 — Upload your sales files", "Upload BOTH files to continue.")
    c1, c2 = st.columns(2)
    with c1:
        coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"])
    with c2:
        croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"])

    if not coffee_file or not croissant_file:
        st.info("Upload both CSV files to continue.")
        return

    coffee_format_note = _detect_coffee_layout(coffee_file)

    # LOAD DATA
    coffee_long = load_coffee_weird_layout(coffee_file)
    croissant_long = load_simple_product_file(croissant_file, "Croissant")

    df_all = pd.concat([coffee_long, croissant_long], ignore_index=True)
    df_all["units_sold"] = pd.to_numeric(df_all["units_sold"], errors="coerce").fillna(0)
    df_all = df_all.dropna(subset=["date"]).sort_values("date")
    df_all["date"] = pd.to_datetime(df_all["date"]).dt.normalize()
    df_all["product"] = df_all["product"].astype(str).str.strip()

    # Filters header
    _section("Filters", "Pick days and products to include (applies to Overview + Forecast).")

    # Date range defaults
    min_date = df_all["date"].min().date()
    max_date = df_all["date"].max().date()

    # PRODUCTS: show a checkbox per product with a "Select all" control
    all_products = sorted(df_all["product"].dropna().unique().tolist())
    st.markdown("**Products** — pick one or multiple")
    prod_cols = st.columns(4)
    select_all_prod = st.checkbox("Select all products", value=True, key="prod_select_all")
    selected_products = []

    # create product checkboxes (unique keys)
    for i, p in enumerate(all_products):
        col = prod_cols[i % len(prod_cols)]
        default = True if select_all_prod else False
        checked = col.checkbox(p, value=default, key=f"prod_chk_{i}_{p}")
        if checked:
            selected_products.append(p)

    # DAY-OF-WEEK: checkboxes for every day
    st.markdown("**Days of week** — pick any combination")
    dow_cols = st.columns(4)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_selected_indexes: list[int] = []
    for i, d in enumerate(days):
        col = dow_cols[i % len(dow_cols)]
        # default all True
        checked = col.checkbox(d, value=True, key=f"dow_chk_{i}_{d}")
        if checked:
            dow_selected_indexes.append(i)  # 0 = Monday ... 6 = Sunday

    # Date range picker
    dr = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(dr, tuple) and len(dr) == 2:
        date_start, date_end = dr
    else:
        date_start, date_end = min_date, max_date

    # Guardrails
    if not selected_products:
        st.warning("No product selected — please pick at least one product.")
        return
    if not dow_selected_indexes:
        st.warning("No day of week selected — please pick at least one day.")
        return

    # Apply filters
    df_filtered = _apply_filters(df_all, selected_products, dow_selected_indexes, date_start, date_end)
    if df_filtered.empty:
        st.warning("No data matches your filters. Adjust the filters and try again.")
        return

    # Build daily series from filtered data
    daily_total = df_filtered.groupby("date")["units_sold"].sum().asfreq("D").fillna(0)
    daily_ma7 = moving_average(daily_total, 7)

    # DATA CHECKS
    with st.expander("Data checks (quality & parsing)"):
        st.write(coffee_format_note)
        st.caption("Checks shown below are based on your CURRENT filtered view.")

        checks = _data_quality_checks(df_filtered, daily_total)
        if checks.get("status"):
            st.info(str(checks["status"]))
        else:
            st.markdown(
                f"""
- **Rows loaded (filtered):** {checks['rows_loaded']:,}
- **Date range (filtered):** {checks['date_range']}
- **Unique dates:** {checks['unique_dates']:,}
- **Products:** {checks['unique_products']:,}
- **Duplicate (date+product) rows:** {checks.get('duplicate_date_product_rows', 0):,}
- **Negative unit rows:** {checks.get('negative_units_rows', 0):,}
- **Missing days filled with 0:** {checks['missing_days_filled_with_0']:,}
- **Days with zero total:** {checks['days_with_zero_total']:,} ({checks['pct_days_zero_total']:.1f}%)
"""
            )

    tab_overview, tab_forecast, tab_explain = st.tabs(["Overview", "Forecast", "Explain"])

    # OVERVIEW TAB
    with tab_overview:
        _section("Step 2 — Understand your sales", "Patterns and weekly behaviour (filtered).")

        colL, colR = st.columns([3, 2])

        with colL:
            _section("Daily total units sold", "Bars = daily units, line = 7-day moving average.")
            st.bar_chart(daily_total)
            st.line_chart(daily_ma7)

            _section("Top products (filtered)", "Best-selling items in current view.")
            totals = df_filtered.groupby("product")["units_sold"].sum().sort_values(ascending=False)
            st.bar_chart(totals.head(10))

        with colR:
            _section("Weekday pattern (filtered)", "Average units sold by day of week.")
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            df_weekday = df_filtered.copy()
            df_weekday["weekday"] = pd.Categorical(df_weekday["date"].dt.day_name(), categories=weekday_order, ordered=True)
            weekday_sales = df_weekday.groupby("weekday", observed=False)["units_sold"].mean().fillna(0)
            st.bar_chart(weekday_sales)

            st.write("")
            _section("Practical weekly target", "A simple planning figure (based on last 14 days, filtered).")
            suggested_weekly = int(daily_total.tail(14).mean() * 7) if len(daily_total) else 0
            st.markdown(f"### Suggested weekly target: **{suggested_weekly:,} units**")
            st.caption("Use this as a starting point when ordering ingredients / staffing.")

    # FORECAST TAB
    with tab_forecast:
        _section("Forecast settings")

        horizon_weeks = st.radio("Forecast horizon", [4, 8], horizontal=True)
        forecast_days = horizon_weeks * 7

        holdout_days = st.slider("Days to test models on (holdout)", 7, 28, 14, step=7)

        metrics_df, best_mode = evaluate_models_time_holdout(daily_total, holdout_days, modes)
        st.markdown(_recommendation_text(best_mode, holdout_days, label_map))

        _metric_help_block()

        if not metrics_df.empty:
            metrics_show = metrics_df.copy()
            if "Model" in metrics_show.columns:
                metrics_show["Model"] = metrics_show["Model"].map(lambda x: label_map.get(x, x))
            st.dataframe(metrics_show, use_container_width=True)

        s = daily_total.copy().sort_index().asfreq("D").fillna(0)

        _section("Compare all models on one graph", "Switch between Holdout (vs actual) and Future (model forecasts).")

        compare_mode = st.radio("Comparison view", ["Holdout (compare to actual)", "Future (compare forecasts)"], horizontal=True)

        holdout_compare_df = pd.DataFrame()
        future_compare_df = pd.DataFrame()

        if compare_mode == "Holdout (compare to actual)":
            if len(s) >= (holdout_days + 10):
                train = s.iloc[:-holdout_days]
                test = s.iloc[-holdout_days:]

                holdout_compare_df = pd.DataFrame(index=test.index)
                holdout_compare_df["Actual"] = test.values.astype(float)

                for m in modes:
                    pred_s, _ = forecast_series_for_mode(train, holdout_days, m)
                    pred_s = pred_s.reindex(test.index).fillna(0)
                    holdout_compare_df[label_map.get(m, m)] = pred_s.values.astype(float)

                st.line_chart(holdout_compare_df)
                st.caption("Closer lines to **Actual** = better performance on the holdout window.")
            else:
                st.info("Not enough data yet for a fair holdout comparison (need more days).")
        else:
            for m in modes:
                ps, _ = forecast_series_for_mode(s, forecast_days, m)
                future_compare_df[label_map.get(m, m)] = ps.values.astype(float)

            if not future_compare_df.empty:
                future_compare_df.index = ps.index
                st.line_chart(future_compare_df)
                st.caption("Model disagreement indicates uncertainty (useful for planning buffers).")

        # ACTION RECOMMENDATIONS
        st.write("")
        _section("Action recommendations", "Turn the forecast into a practical plan (filtered).")

        all_future_models = pd.DataFrame()
        for m in modes:
            ps, _ = forecast_series_for_mode(s, forecast_days, m)
            all_future_models[label_map.get(m, m)] = ps.values.astype(float)
        if not all_future_models.empty:
            all_future_models.index = ps.index

        use_recommended = st.toggle("Use recommended model for actions", value=True)
        if use_recommended and best_mode:
            chosen_mode = best_mode
        else:
            pretty_choices = [label_map.get(m, m) for m in modes]
            chosen_pretty = st.radio("Model for actions", pretty_choices, horizontal=True)
            rev = {label_map.get(m, m): m for m in modes}
            chosen_mode = rev.get(chosen_pretty, modes[0])

        chosen_label = label_map.get(chosen_mode, chosen_mode)
        chosen_pred, _ = forecast_series_for_mode(s, forecast_days, chosen_mode)

        next7 = min(7, len(chosen_pred))
        next7_total = float(chosen_pred.head(next7).sum()) if next7 else 0.0

        buffer_pct, buffer_reason = _buffer_from_disagreement(all_future_models, next_days=7)
        buffered_week = math.ceil(next7_total * (1.0 + buffer_pct))

        recent_week_avg = float(s.tail(28).mean() * 7) if len(s) else 0.0

        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown(f"### Next 7 days (forecast)\n**{next7_total:,.0f} units**")
            st.caption(f"Model used: {chosen_label}")
        with a2:
            st.markdown(f"### Suggested plan (with buffer)\n**{buffered_week:,.0f} units**")
            st.caption(f"Buffer: +{int(buffer_pct*100)}% — {buffer_reason}")
        with a3:
            st.markdown(f"### Recent weekly baseline\n**{recent_week_avg:,.0f} units**")
            st.caption("Based on average daily sales over the last 28 days.")

        # DOWNLOADS
        st.write("")
        _section("Download CSV exports", "Export charts and forecasts for reports / submission.")

        d1, d2, d3 = st.columns(3)

        with d1:
            if not holdout_compare_df.empty:
                export_holdout = holdout_compare_df.copy()
                export_holdout.index.name = "date"
                _download_csv_button(
                    "Download holdout comparison CSV",
                    export_holdout,
                    f"holdout_model_comparison_{holdout_days}d.csv",
                )
            else:
                st.caption("Generate the Holdout chart to enable this download.")

        with d2:
            if not future_compare_df.empty:
                export_future = future_compare_df.copy()
                export_future.index.name = "date"
                _download_csv_button(
                    "Download future comparison CSV",
                    export_future,
                    f"future_model_comparison_{horizon_weeks}w.csv",
                )
            else:
                st.caption("Generate the Future chart to enable this download.")

        st.write("")
        _section("Chosen model forecast", "Forecast with an uncertainty band for planning.")

        pred_series, _ = forecast_series_for_mode(s, forecast_days, chosen_mode)
        band_df = make_pred_band(pred_series, s)

        band_show = band_df.rename(
            columns={
                "predicted": f"Predicted ({chosen_label})",
                "lower": "Lower bound",
                "upper": "Upper bound",
            }
        )

        st.line_chart(band_show[[f"Predicted ({chosen_label})", "Lower bound", "Upper bound"]])

        with d3:
            export_band = band_show.copy()
            export_band.index.name = "date"
            _download_csv_button(
                "Download chosen forecast CSV",
                export_band,
                f"forecast_{chosen_label.replace(' ', '_').replace('(', '').replace(')', '').lower()}_{horizon_weeks}w.csv",
            )

    # EXPLAIN TAB
    with tab_explain:
        _section("Explain the forecasting", "Plain-English summary of each model.")
        for k, v in mode_help.items():
            st.markdown(f"**{label_map.get(k, k)}**")
            st.write(v)