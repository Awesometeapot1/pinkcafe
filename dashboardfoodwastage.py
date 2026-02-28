# dashboardfoodwastage.py
# Bristol Pink Café – Streamlit Dashboard (with BLACKPINK login + Manager/Staff roles + Sales entry)
#
# What you need in the project folder:
#   - dashboardfoodwastage.py  (this file)
#   - product_prices.csv       (teacher-provided prices; auto-template created if missing)
#
# Your prediction dashboard still expects TWO CSV uploads:
#   1) Coffee CSV: "Pink CoffeeSales March - Oct 2025.csv"  (weird first-row product names)
#   2) Croissant CSV: "Pink CroissantSales March - Oct 2025.csv" (normal Date + Number Sold)

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import streamlit as st

# ---- ML import (safe) ----
try:
    from sklearn.linear_model import LinearRegression

    SKLEARN_OK = True
except Exception:
    LinearRegression = None
    SKLEARN_OK = False


# ----------------------------
# Config / Paths
# ----------------------------
FORECAST_DAYS = 28
PRICE_FILE = Path("product_prices.csv")
SALES_LOG = Path("sales_entries.csv")

# Demo users (replace later with secrets/hashes if needed)
# username is case-insensitive
DEMO_USERS = {
    "manager": {"password": "manager123", "role": "manager"},
    "staff": {"password": "staff123", "role": "staff"},
}


# ----------------------------
# BLACKPINK Theme
# ----------------------------
def inject_blackpink_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top, #1a1a1a 0%, #000000 55%, #000000 100%);
            color: #ffe6f2;
        }
        html, body, [class*="css"]  {
            color: #ffe6f2;
        }
        section[data-testid="stSidebar"] {
            background: #0b0b0b;
            border-right: 1px solid rgba(255,105,180,0.35);
        }
        h1, h2, h3, h4 {
            color: #ff69b4 !important;
            letter-spacing: 0.5px;
        }
        .stButton > button {
            background: linear-gradient(90deg, #ff69b4 0%, #ff2d95 100%);
            color: black;
            border: none;
            border-radius: 12px;
            padding: 0.6rem 1rem;
            font-weight: 800;
        }
        .stButton > button:hover { filter: brightness(1.05); }
        .stTextInput input, .stSelectbox div, .stNumberInput input, .stDateInput input {
            border-radius: 12px !important;
        }
        .bp-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,105,180,0.35);
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }
        .bp-badge {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(255,105,180,0.45);
            color: #ffb6d9;
            font-size: 12px;
            margin-bottom: 12px;
        }
        .bp-divider {
            height: 1px;
            background: rgba(255,105,180,0.25);
            margin: 14px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_pink_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="bp-card">
            <div class="bp-badge">BLACKPINK • Bristol Pink Café</div>
            <h1 style="margin:0;">{title}</h1>
            <p style="margin:6px 0 0 0; color:#ffb6d9;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


# ----------------------------
# Beginner-friendly chart helpers (NEW)
# ----------------------------
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["day"] = df["date"].dt.date
    df["week"] = df["date"].dt.to_period("W").astype(str)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["weekday"] = df["date"].dt.day_name()
    return df


def moving_average(s: pd.Series, window: int = 7) -> pd.Series:
    s = s.sort_index()
    return s.rolling(window=window, min_periods=max(1, window // 2)).mean()


def friendly_kpi_help(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="bp-card" style="padding:16px;">
            <div class="bp-badge">{title}</div>
            <div style="color:#ffb6d9; line-height:1.4;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def chart_section_title(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)
    st.write("")


def make_pred_band(pred: pd.Series, recent_actual: pd.Series) -> pd.DataFrame:
    """
    Friendly 'range' band using recent variability (NOT a statistical confidence interval).
    """
    recent = recent_actual.dropna().tail(21)
    if len(recent) < 5:
        spread = 0.0
    else:
        spread = float(recent.std())

    lower = (pred - spread).clip(lower=0)
    upper = (pred + spread).clip(lower=0)
    return pd.DataFrame({"predicted": pred, "lower": lower, "upper": upper})


# ----------------------------
# Auth (simple, demo)
# ----------------------------
def login_gate() -> bool:
    """
    Demo login gate:
    - Stores logged_in, username, role in st.session_state
    - Uses DEMO_USERS dict (change later if needed)
    """
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

    if st.session_state.logged_in:
        return True

    # login UI
    left, mid, right = st.columns([1.2, 1, 1.2])
    with mid:
        st.markdown('<div class="bp-card">', unsafe_allow_html=True)
        st.markdown('<div class="bp-badge">BLACKPINK • Café Portal</div>', unsafe_allow_html=True)
        st.markdown("## 🔐 Login")

        with st.form("bp_login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="manager or staff")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Log in")

        if submit:
            u = (username or "").strip().lower()
            user = DEMO_USERS.get(u)
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                st.success(f"Welcome, {st.session_state.role.title()} ✨")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown('<div class="bp-divider"></div>', unsafe_allow_html=True)
        st.caption("Demo accounts (change later): manager/manager123 and staff/staff123")
        st.markdown("</div>", unsafe_allow_html=True)

    return False


def logout_button() -> None:
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()


# ----------------------------
# Price list + Sales log (CSV persistence)
# ----------------------------
def ensure_price_file_template() -> None:
    if PRICE_FILE.exists():
        return

    template = pd.DataFrame(
        {
            "product": ["Cappuccino", "Americano", "Croissant"],
            "unit_price": [3.50, 3.00, 2.20],
        }
    )
    template.to_csv(PRICE_FILE, index=False)


@st.cache_data
def load_price_map() -> Dict[str, float]:
    ensure_price_file_template()
    dfp = pd.read_csv(PRICE_FILE)
    dfp["product"] = dfp["product"].astype(str).str.strip()
    dfp["unit_price"] = pd.to_numeric(dfp["unit_price"], errors="coerce")
    dfp = dfp.dropna(subset=["product", "unit_price"])

    price_map = dict(zip(dfp["product"], dfp["unit_price"]))
    if not price_map:
        st.error("product_prices.csv has no valid rows. Please fill it with teacher prices.")
        st.stop()
    return price_map


def append_sale(row: dict) -> None:
    df = pd.DataFrame([row])
    if SALES_LOG.exists():
        df.to_csv(SALES_LOG, mode="a", header=False, index=False)
    else:
        df.to_csv(SALES_LOG, index=False)


def load_sales_log() -> pd.DataFrame:
    cols = ["date", "product", "qty", "unit_price", "staff_user", "created_at"]
    if not SALES_LOG.exists():
        return pd.DataFrame(columns=cols + ["total"])

    df = pd.read_csv(SALES_LOG)
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
    df["total"] = df["qty"] * df["unit_price"]
    return df


# ----------------------------
# Original helpers (CSV loaders + forecasting)
# ----------------------------
def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_date_series(s: pd.Series) -> pd.Series:
    # UK-style (dd/mm/yyyy)
    return pd.to_datetime(s, dayfirst=True, errors="coerce")


def load_coffee_weird_layout(uploaded_file) -> pd.DataFrame:
    """
    Handles Coffee CSV format:
      Columns: Date, Number Sold, Unnamed: 2
      Row 0: Date is NaN, other columns contain product names (e.g., Cappuccino, Americano)
      Remaining rows: Date + numeric sales for each product
    Returns long format: date, product, units_sold
    """
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
    else:
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


def load_simple_product_file(uploaded_file, product_name: str) -> pd.DataFrame:
    """
    Croissant CSV: Date, Number Sold
    Returns long format: date, product, units_sold
    """
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


def simple_forecast(series: pd.Series, days: int = FORECAST_DAYS) -> pd.DataFrame:
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


def linear_regression_forecast(series: pd.Series, days: int = FORECAST_DAYS):
    if not SKLEARN_OK:
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
    y_future = model.predict(X_future)
    y_future = np.clip(y_future, 0, None)

    pred_df = pd.DataFrame({"predicted": y_future})
    info = {
        "ok": True,
        "slope_per_day": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r2_train": r2,
    }
    return pred_df, info


# ----------------------------
# Pages
# ----------------------------
def page_staff_record_sale() -> None:
    render_pink_header("Staff • Record Sales", "Enter daily sales. Unit price is fixed from teacher price list.")

    price_map = load_price_map()
    products = list(price_map.keys())

    st.info(
        "Prices come from product_prices.csv (teacher list). If you need to update prices, ask a manager to edit the CSV.",
        icon="💗",
    )

    with st.form("sale_form"):
        d = st.date_input("Date", value=date.today())
        product = st.selectbox("Product", products)
        unit_price = float(price_map[product])

        st.text_input("Unit price", value=f"£{unit_price:.2f}", disabled=True)
        qty = st.number_input("Quantity sold", min_value=1, step=1, value=1)

        submitted = st.form_submit_button("Save sale")

    if submitted:
        row = {
            "date": str(d),
            "product": product,
            "qty": int(qty),
            "unit_price": float(unit_price),
            "staff_user": st.session_state.username,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        append_sale(row)
        st.success("Saved!")

    st.write("")
    st.subheader("🧾 Your recent entries")
    df = load_sales_log()
    mine = df[df["staff_user"] == st.session_state.username].copy()
    if mine.empty:
        st.caption("No entries yet.")
    else:
        mine = mine.sort_values("created_at", ascending=False).head(20)
        show = mine[["date", "product", "qty", "unit_price", "total", "created_at"]].copy()
        show["unit_price"] = show["unit_price"].map(lambda x: f"£{x:.2f}")
        show["total"] = show["total"].map(lambda x: f"£{x:.2f}")
        st.dataframe(show, use_container_width=True)


def page_manager_sales_overview() -> None:
    render_pink_header("Manager • Sales Overview", "Totals, trends, and top products from staff-entered records.")

    df = load_sales_log()
    if df.empty or df["date"].isna().all():
        st.info("No sales recorded yet.")
        return

    df = df.dropna(subset=["date"])
    df["day"] = df["date"].dt.date

    c1, c2, c3 = st.columns(3)
    c1.metric("Total units", int(df["qty"].sum()))
    c2.metric("Total revenue", f"£{df['total'].sum():.2f}")
    c3.metric("Transactions", int(len(df)))

    st.write("")

    # Beginner-friendly revenue charts (NEW)
    revenue_daily = df.groupby("day")["total"].sum().sort_index()
    rev_ma7 = moving_average(revenue_daily, 7)

    chart_section_title(
        "📈 Revenue by day (easy view)",
        "Bars = revenue each day • Line = 7-day average (smooth trend)",
    )
    st.bar_chart(pd.DataFrame({"Daily revenue": revenue_daily}))
    st.line_chart(pd.DataFrame({"7-day average": rev_ma7}))

    chart_section_title(
        "📅 Weekly revenue (less noise)",
        "Summarises performance week-by-week.",
    )
    weekly_rev = df.groupby(df["date"].dt.to_period("W"))["total"].sum()
    weekly_rev.index = weekly_rev.index.astype(str)
    st.bar_chart(weekly_rev)

    st.write("")
    st.subheader("📦 Units by day")
    units_daily = df.groupby("day")["qty"].sum().sort_index()
    units_ma7 = moving_average(units_daily, 7)
    st.bar_chart(pd.DataFrame({"Daily units": units_daily}))
    st.line_chart(pd.DataFrame({"7-day average": units_ma7}))

    st.subheader("🏆 Top products (revenue)")
    by_prod = df.groupby("product")["total"].sum().sort_values(ascending=False)
    st.bar_chart(by_prod)


def page_manager_sales_records() -> None:
    render_pink_header("Manager • Sales Records", "Filter, review, and export the sales log.")

    df = load_sales_log()
    if df.empty:
        st.info("No sales recorded yet.")
        return

    df = df.dropna(subset=["date"]).copy()
    df["day"] = df["date"].dt.date

    with st.sidebar:
        st.markdown("### Filters")
        products = ["(All)"] + sorted(df["product"].dropna().unique().tolist())
        staff_users = ["(All)"] + sorted(df["staff_user"].dropna().unique().tolist())

        f_product = st.selectbox("Product", products)
        f_staff = st.selectbox("Staff user", staff_users)

        dmin = df["day"].min()
        dmax = df["day"].max()
        d_from, d_to = st.date_input("Date range", value=(dmin, dmax))

    out = df.copy()
    if f_product != "(All)":
        out = out[out["product"] == f_product]
    if f_staff != "(All)":
        out = out[out["staff_user"] == f_staff]

    out = out[(out["day"] >= d_from) & (out["day"] <= d_to)]

    st.subheader("Records")
    show = out[["date", "product", "qty", "unit_price", "total", "staff_user", "created_at"]].copy()
    show["unit_price"] = show["unit_price"].map(lambda x: f"£{x:.2f}")
    show["total"] = show["total"].map(lambda x: f"£{x:.2f}")
    st.dataframe(show, use_container_width=True)

    st.write("")
    csv_bytes = out.drop(columns=["day"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered sales (CSV)",
        data=csv_bytes,
        file_name="sales_filtered.csv",
        mime="text/csv",
    )


def page_predictions_dashboard() -> None:
    render_pink_header("Prediction Dashboard", "Upload café CSVs to view trends and predict the next 4 weeks.")

    st.markdown("### Upload files")
    coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"], key="coffee_upload")
    croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"], key="croissant_upload")

    mode = st.radio("Prediction mode", ["AI", "ML"], horizontal=True)
    st.caption("ML = Linear Regression forecast on daily totals.")

    if not coffee_file or not croissant_file:
        st.info("Upload BOTH CSV files to continue.")
        return

    try:
        coffee_long = load_coffee_weird_layout(coffee_file)
        croissant_long = load_simple_product_file(croissant_file, "Croissant")
    except Exception as e:
        st.error(f"Error loading CSVs: {e}")
        return

    df_all = pd.concat([coffee_long, croissant_long], ignore_index=True)
    df_all["product"] = df_all["product"].astype(str).str.strip()
    df_all["units_sold"] = pd.to_numeric(df_all["units_sold"], errors="coerce").fillna(0)
    df_all = df_all.dropna(subset=["date"]).sort_values("date")

    with st.expander("🔎 Debug (cleaned data preview)"):
        st.write("Coffee (long format):")
        st.dataframe(coffee_long.head(10), use_container_width=True)
        st.write("Croissant (long format):")
        st.dataframe(croissant_long.head(10), use_container_width=True)
        st.write("Combined:")
        st.dataframe(df_all.head(10), use_container_width=True)

    st.subheader("🏆 Best selling products (overall)")
    totals = df_all.groupby("product")["units_sold"].sum().sort_values(ascending=False)
    top3 = totals.head(3)

    cols = st.columns(3)
    medals = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    for i in range(3):
        if i < len(top3):
            product = top3.index[i]
            units = int(top3.iloc[i])
            cols[i].metric(medals[i], product, f"{units:,} sold")
        else:
            cols[i].metric(medals[i], "-", "-")

    left, right = st.columns([3, 2])

    daily_total = df_all.groupby("date")["units_sold"].sum().sort_index()
    daily_ma7 = moving_average(daily_total, 7)

    with left:
        chart_section_title(
            "📈 Daily total sales (easy view)",
            "Bars = sales each day • Line = 7-day average (smooth trend)",
        )

        daily_chart_df = pd.DataFrame({"Daily sales": daily_total, "7-day average": daily_ma7})
        st.bar_chart(daily_chart_df[["Daily sales"]])
        st.line_chart(daily_chart_df[["7-day average"]])

        friendly_kpi_help(
            "How to read this",
            "If the bars go up and the 7-day average line rises, sales are increasing. "
            "If the line falls, sales are decreasing. The line is there so you don’t overreact to one weird day.",
        )

        chart_section_title(
            "🧁 Sales by product (top 5)",
            "Shows the products with the most total sales in the period.",
        )
        pivot = (
            df_all.pivot_table(index="date", columns="product", values="units_sold", aggfunc="sum")
            .fillna(0)
            .sort_index()
        )
        top_products = pivot.sum().sort_values(ascending=False).head(5).index.tolist()
        if top_products:
            st.line_chart(pivot[top_products])
        else:
            st.info("No product data to chart.")

        st.caption("Tip: If one product line is flat/near zero most of the time, it may be overstock risk.")

    with right:
        chart_section_title(
            "🗓️ Weekday pattern",
            "Helps spot which days are naturally busier (useful for staffing & stock).",
        )

        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_sales = (
            df_all.copy()
            .assign(weekday=df_all["date"].dt.day_name())
            .groupby("weekday")["units_sold"]
            .mean()
            .reindex(weekday_order)
            .fillna(0)
        )
        st.bar_chart(weekday_sales)

        st.write("")
        chart_section_title(
            "⚠️ Low-average products (simple risk list)",
            "Below-average daily sales compared to the overall mean (very basic rule).",
        )
        avg = df_all.groupby("product")["units_sold"].mean().sort_values()
        threshold = float(avg.mean()) if len(avg) else 0.0
        risky = avg[avg < threshold].head(8)

        if risky.empty:
            st.success("No obvious low-average products using this simple rule.")
        else:
            st.dataframe(risky.rename("Average units/day").to_frame(), use_container_width=True)
            friendly_kpi_help(
                "What this means",
                "These items sell less than the overall average. They’re candidates for smaller batches, "
                "promotions, or reviewing whether they’re worth stocking as much.",
            )

        st.write("")
        chart_section_title(
            "✅ Simple weekly target suggestion",
            "Based on your last 14 days average (not a guarantee).",
        )
        amount_to_sell = int(max(0, daily_total.tail(14).mean() * 7)) if len(daily_total) else 0
        st.markdown(f"### Suggested weekly stock target: **{amount_to_sell:,} units**")

    st.subheader("🔮 Prediction for next 4 weeks (easy view)")

    if mode == "AI":
        pred_raw = simple_forecast(daily_total, days=FORECAST_DAYS)
        model_info = {"ok": True, "type": "heuristic"}
    else:
        pred_raw, model_info = linear_regression_forecast(daily_total, days=FORECAST_DAYS)

    last_date = daily_total.index.max()
    future_index = pd.date_range(last_date + pd.Timedelta(days=1), periods=FORECAST_DAYS, freq="D")

    pred_series = pd.Series(pred_raw["predicted"].values, index=future_index)
    band_df = make_pred_band(pred_series, daily_total)

    st.caption("Line = predicted daily sales • Band = typical variation based on recent days (friendly range)")
    st.line_chart(band_df[["predicted", "lower", "upper"]])

    friendly_kpi_help(
        "How to use this",
        "Use the prediction as a planning guide, not a promise. If your real sales start tracking near the upper band, "
        "you may need more stock. If they’re near the lower band, reduce waste risk.",
    )

    with st.expander("🧠 Prediction details"):
        if mode == "AI":
            st.write("**AI mode**: rolling mean + light recent trend (heuristic baseline).")
        else:
            st.write("**ML mode**: Linear Regression trained on daily total sales vs time index.")
            if not model_info.get("ok", False):
                st.warning(f"ML fallback used: {model_info.get('reason', 'unknown reason')}")
                if not SKLEARN_OK:
                    st.code("pip install scikit-learn", language="bash")
            else:
                st.write(f"- Slope (units/day): **{model_info['slope_per_day']:.4f}**")
                st.write(f"- Intercept: **{model_info['intercept']:.4f}**")
                st.write(f"- R² (training fit): **{model_info['r2_train']:.3f}**")
                st.caption("R² shown is on training data (simple baseline for coursework).")

    out = band_df.reset_index().rename(columns={"index": "date"})
    csv_bytes = out.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download 4-week prediction (CSV)",
        data=csv_bytes,
        file_name="prediction_next_4_weeks.csv",
        mime="text/csv",
    )


# ----------------------------
# App start
# ----------------------------
st.set_page_config(page_title="Bristol Pink Café Dashboard", layout="wide")
inject_blackpink_theme()

if not login_gate():
    st.stop()

# Sidebar (session + navigation)
with st.sidebar:
    st.markdown("### 👤 Session")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")
    logout_button()

    st.markdown("---")

    # Menu depends on role
    if st.session_state.role == "manager":
        page = st.radio(
            "Navigation",
            ["Sales Overview", "Sales Records", "Predictions"],
            index=0,
        )
    else:
        page = st.radio(
            "Navigation",
            ["Record Sale", "Predictions"],
            index=0,
        )

# Route pages
if st.session_state.role == "manager" and page == "Sales Overview":
    page_manager_sales_overview()
elif st.session_state.role == "manager" and page == "Sales Records":
    page_manager_sales_records()
elif st.session_state.role == "staff" and page == "Record Sale":
    page_staff_record_sale()
else:
    page_predictions_dashboard()

# Footer note about prices template
if not PRICE_FILE.exists():
    st.warning("product_prices.csv was not found and a template should have been created. Please check your folder.")
else:
    pass