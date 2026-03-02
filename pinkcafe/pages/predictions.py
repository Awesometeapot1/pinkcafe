# pages/predictions.py
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
# Small UI helpers (friendly)
# ----------------------------
def _section(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.write("")


def _info_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="bp-card" style="padding:16px;">
            <div class="bp-badge">{title}</div>
            <div style="color: var(--bp-text-dim); line-height:1.5;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def _metric_help_block() -> None:
    with st.expander("What do MAE / RMSE / MAPE mean? (simple)"):
        st.markdown(
            """
**MAE (Mean Absolute Error)**  
- Average “how far off” the predictions are.  
- Lower = better.

**RMSE (Root Mean Squared Error)**  
- Like MAE, but punishes big mistakes more.

**MAPE (%) (Mean Absolute Percentage Error)**  
- Error as a percentage (lower = better).  
- Can be unstable when actual values are 0 (handled safely here).
            """
        )


def _model_explanations() -> dict[str, str]:
    return {
        "AI (Heuristic)": (
            "A simple baseline using recent averages + trend.\n"
            "- Stable with small or noisy data."
        ),
        "ML (Linear Regression)": (
            "Fits a straight-line trend over time.\n"
            "- Works well for steady growth/decline."
        ),
        "AI (Random Forest)": (
            "Learns non-linear patterns using lag + weekday features.\n"
            "- Often strong for weekday/weekend effects."
        ),
        "ML (Gradient Boosting)": (
            "Boosted trees using the same features.\n"
            "- Powerful but less intuitive."
        ),
    }


def _recommendation_text(best_mode: str, holdout_days: int) -> str:
    if not best_mode:
        return (
            "Not enough data to fairly compare models yet. "
            "Use **AI (Heuristic)** for now."
        )
    return (
        f"Based on the **last {holdout_days} days**, the most accurate model was:\n\n"
        f"### ✅ Recommended: **{best_mode}**"
    )


# ----------------------------
# Page
# ----------------------------
def page_predictions_dashboard() -> None:
    render_pink_header(
        "Predictions",
        "Upload café CSVs → understand trends → generate an actionable forecast.",
    )

    mode_help = _model_explanations()
    modes = list(mode_help.keys())

    # =========================
    # STEP 1 — UPLOAD
    # =========================
    _section("Step 1 — Upload your sales files", "Upload BOTH files to continue.")
    c1, c2 = st.columns(2)
    with c1:
        coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"])
    with c2:
        croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"])

    if not coffee_file or not croissant_file:
        st.info("Upload both CSV files to continue.")
        return

    # =========================
    # LOAD DATA
    # =========================
    coffee_long = load_coffee_weird_layout(coffee_file)
    croissant_long = load_simple_product_file(croissant_file, "Croissant")

    df_all = pd.concat([coffee_long, croissant_long], ignore_index=True)
    df_all["units_sold"] = pd.to_numeric(df_all["units_sold"], errors="coerce").fillna(0)
    df_all = df_all.dropna(subset=["date"]).sort_values("date")

    daily_total = df_all.groupby("date")["units_sold"].sum().asfreq("D").fillna(0)
    daily_ma7 = moving_average(daily_total, 7)

    tab_overview, tab_forecast, tab_explain = st.tabs(
        ["Overview", "Forecast", "Explain"]
    )

    # =========================
    # OVERVIEW TAB
    # =========================
    with tab_overview:
        _section("Step 2 — Understand your sales", "Patterns and weekly behaviour.")

        colL, colR = st.columns([3, 2])

        with colL:
            _section("Daily total sales", "Bars = daily sales, line = 7-day average.")
            st.bar_chart(daily_total)
            st.line_chart(daily_ma7)

            _section("Top products", "Best-selling items overall.")
            totals = df_all.groupby("product")["units_sold"].sum().sort_values(ascending=False)
            st.bar_chart(totals.head(10))

        with colR:
            _section("Weekday pattern", "Average units sold per weekday.")

            weekday_order = [
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday",
            ]

            df_weekday = df_all.copy()
            df_weekday["weekday"] = pd.Categorical(
                df_weekday["date"].dt.day_name(),
                categories=weekday_order,
                ordered=True,
            )

            weekday_sales = (
                df_weekday
                .groupby("weekday", observed=False)["units_sold"]
                .mean()
                .fillna(0)
            )

            st.bar_chart(weekday_sales)

            st.write("")
            _section("Practical weekly target", "Simple planning number.")
            suggested_weekly = int(daily_total.tail(14).mean() * 7) if len(daily_total) else 0
            st.markdown(f"### Suggested weekly target: **{suggested_weekly:,} units**")

    # =========================
    # FORECAST TAB
    # =========================
    with tab_forecast:
        _section("Step 3 — Forecast horizon")
        horizon_weeks = st.radio("Forecast horizon", [4, 8], horizontal=True)
        forecast_days = horizon_weeks * 7

        holdout_days = st.slider("Days to test models on", 7, 28, 14, step=7)
        metrics_df, best_mode = evaluate_models_time_holdout(
            daily_total, holdout_days, modes
        )

        st.markdown(_recommendation_text(best_mode, holdout_days))

        use_recommended = st.toggle("Use recommended model", value=True)
        chosen_mode = best_mode if use_recommended and best_mode else st.radio(
            "Model", modes, horizontal=True
        )

        _metric_help_block()
        if not metrics_df.empty:
            st.dataframe(metrics_df, use_container_width=True)

        pred_series, model_info = forecast_series_for_mode(
            daily_total, forecast_days, chosen_mode
        )
        band_df = make_pred_band(pred_series, daily_total)

        st.line_chart(band_df[["predicted", "lower", "upper"]])

    # =========================
    # EXPLAIN TAB
    # =========================
    with tab_explain:
        _section("Explain the forecasting", "Plain-English explanation.")
        for k, v in mode_help.items():
            st.markdown(f"**{k}**")
            st.write(v)