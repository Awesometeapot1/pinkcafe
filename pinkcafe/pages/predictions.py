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
- Example: MAE = 5 means “on average we’re off by ~5 units per day”.

**RMSE (Root Mean Squared Error)**  
- Like MAE, but it **punishes big mistakes more**.  
- Lower = better.  
- Useful if you really want to avoid occasional large errors.

**MAPE (%) (Mean Absolute Percentage Error)**  
- Error as a **percentage**.  
- Lower = better.  
- Example: MAPE = 10% means “we’re off by ~10% on average”.  
⚠️ If actual sales are often 0, MAPE can be unstable (we handle zeros safely).
            """
        )


def _model_explanations() -> dict[str, str]:
    return {
        "AI (Heuristic)": (
            "A simple baseline: uses a recent average + trend.\n"
            "- Best when data is small or noisy.\n"
            "- Easy to explain, but can miss complex patterns."
        ),
        "ML (Linear Regression)": (
            "Fits a straight-line trend over time.\n"
            "- Great if demand steadily rises/falls.\n"
            "- Not great if weekday patterns are strong."
        ),
        "AI (Random Forest)": (
            "Learns non-linear patterns using 'lags' (yesterday/last week) + weekday features.\n"
            "- Often strong when weekends differ from weekdays.\n"
            "- Needs more data."
        ),
        "ML (Gradient Boosting)": (
            "A powerful tree-boosting model using the same lag + weekday features.\n"
            "- Often very accurate with enough history.\n"
            "- Less intuitive than Linear Regression."
        ),
    }


def _recommendation_text(best_mode: str, holdout_days: int) -> str:
    if not best_mode:
        return (
            "We don’t have enough historical data to fairly test models yet. "
            "Use **AI (Heuristic)** for now (it’s stable with small data)."
        )
    return (
        f"Based on the **last {holdout_days} days**, the most accurate model was:\n\n"
        f"### ✅ Recommended: **{best_mode}**\n\n"
        "This recommendation is made by comparing model errors on recent real sales."
    )


# ----------------------------
# Page
# ----------------------------
def page_predictions_dashboard() -> None:
    render_pink_header("Predictions", "Upload café CSVs → see trends → generate a forecast you can act on.")

    # --- Friendly mode descriptions
    mode_help = _model_explanations()
    modes = list(mode_help.keys())

    # --- Top layout: STEP 1 Upload
    _section("Step 1 — Upload your sales files", "You must upload BOTH files to continue.")
    c1, c2 = st.columns(2)
    with c1:
        coffee_file = st.file_uploader("Coffee Sales CSV", type=["csv"], key="coffee_upload")
    with c2:
        croissant_file = st.file_uploader("Croissant Sales CSV", type=["csv"], key="croissant_upload")

    _info_card(
        "What happens after upload?",
        "We convert your files into a consistent table with columns: **date, product, units_sold**. "
        "Then we build simple charts and forecasts from daily totals.",
    )

    if not coffee_file or not croissant_file:
        st.info("Upload both CSV files to continue.")
        return

    # --- Load and clean data
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

    # --- Add daily totals
    daily_total = df_all.groupby("date")["units_sold"].sum().sort_index()
    daily_total = daily_total.asfreq("D").fillna(0)
    daily_ma7 = moving_average(daily_total, 7)

    # --- Tabs: Make it easy
    tab_overview, tab_forecast, tab_explain = st.tabs(["Overview", "Forecast", "Explain"])

    # =========================
    # OVERVIEW TAB
    # =========================
    with tab_overview:
        _section("Step 2 — Understand your sales", "Quick visuals: what sold, when, and patterns by weekday.")

        # Quick stats
        total_units = int(df_all["units_sold"].sum())
        days = int(len(daily_total))
        avg_per_day = float(daily_total.mean()) if days else 0.0
        last_14_avg = float(daily_total.tail(14).mean()) if len(daily_total) else 0.0

        a, b, c, d = st.columns(4)
        a.metric("Total units", f"{total_units:,}")
        b.metric("Days of data", f"{days:,}")
        c.metric("Avg / day", f"{avg_per_day:.1f}")
        d.metric("Avg / day (last 14)", f"{last_14_avg:.1f}")

        st.write("")

        colL, colR = st.columns([3, 2])

        with colL:
            _section("Daily total sales", "Bars = daily sales. Line = smoother 7-day average (trend).")
            st.bar_chart(pd.DataFrame({"Daily sales": daily_total}))
            st.line_chart(pd.DataFrame({"7-day average": daily_ma7}))

            _info_card(
                "How to read this",
                "If the **7-day average** rises, demand is increasing. "
                "If it falls, demand is decreasing. "
                "Spiky bars mean demand varies a lot day-to-day.",
            )

            _section("Top products", "Which products sell the most overall?")
            totals = df_all.groupby("product")["units_sold"].sum().sort_values(ascending=False)
            st.bar_chart(totals.head(10))

        with colR:
            _section("Weekday pattern", "Average units sold per weekday.")
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
            _section("Practical weekly target", "Simple planning number based on recent demand.")
            suggested_weekly = int(max(0, daily_total.tail(14).mean() * 7)) if len(daily_total) else 0
            st.markdown(f"### Suggested weekly target: **{suggested_weekly:,} units**")
            st.caption("This uses the average daily sales from the last 14 days × 7.")

        with st.expander("Data preview (optional)"):
            st.write("Coffee (long format):")
            st.dataframe(coffee_long.head(10), use_container_width=True)
            st.write("Croissant (long format):")
            st.dataframe(croissant_long.head(10), use_container_width=True)
            st.write("Combined:")
            st.dataframe(df_all.head(20), use_container_width=True)

    # =========================
    # FORECAST TAB
    # =========================
    with tab_forecast:
        _section("Step 3 — Choose how far ahead you want to predict", "Shorter horizons are usually more reliable.")
        horizon_weeks = st.radio("Forecast horizon", [4, 8], index=0, horizontal=True)
        forecast_days = int(horizon_weeks) * 7

        st.write("")
        _section("Step 4 — Pick a model (or use the recommended one)", "We can recommend the model by testing on recent days.")

        holdout_days = st.slider("How many recent days to test models on?", 7, 28, 14, step=7)
        metrics_df, best_mode = evaluate_models_time_holdout(daily_total, holdout_days=holdout_days, modes=modes)

        st.markdown(_recommendation_text(best_mode, holdout_days))
        st.write("")

        # Let user decide: recommended vs manual
        use_recommended = st.toggle("Use recommended model automatically", value=True)

        if use_recommended and best_mode:
            chosen_mode = best_mode
        else:
            # manual model select
            chosen_mode = st.radio("Model", modes, horizontal=True, index=0)
            st.caption(mode_help.get(chosen_mode, ""))

        # Show metrics table nicely + help
        st.write("")
        _section("Model accuracy (simple comparison)", "Lower error = better. This compares predictions against real recent sales.")
        _metric_help_block()
        if not metrics_df.empty:
            show_metrics = metrics_df.copy()
            for c in ["MAE", "RMSE", "MAPE_%"]:
                if c in show_metrics.columns:
                    show_metrics[c] = pd.to_numeric(show_metrics[c], errors="coerce")
            st.dataframe(show_metrics, use_container_width=True)
        else:
            st.info("Not enough data to show metrics yet.")

        st.write("")
        _section(f"Forecast output (next {horizon_weeks} weeks)", "We show a predicted line + a simple variability band.")

        # Run forecast
        pred_series, model_info = forecast_series_for_mode(daily_total, forecast_days, chosen_mode)
        band_df = make_pred_band(pred_series, daily_total)

        # Forecast chart
        st.caption(
            "The shaded band is not a statistical confidence interval — it’s a friendly range based on recent volatility."
        )
        st.line_chart(band_df[["predicted", "lower", "upper"]])

        # Plain-English summary
        avg_pred = float(band_df["predicted"].mean()) if len(band_df) else 0.0
        total_pred = float(band_df["predicted"].sum()) if len(band_df) else 0.0
        x1, x2 = st.columns(2)
        x1.metric("Average predicted units/day", f"{avg_pred:.1f}")
        x2.metric(f"Total predicted units ({horizon_weeks} weeks)", f"{total_pred:.0f}")

        with st.expander("Forecast details (technical)"):
            st.write({"chosen_mode": chosen_mode, "model_info": model_info})

        # Download
        out = band_df.reset_index().rename(columns={"index": "date"})
        csv_bytes = out.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"Download {horizon_weeks}-week forecast (CSV)",
            data=csv_bytes,
            file_name=f"prediction_next_{horizon_weeks}_weeks.csv",
            mime="text/csv",
        )

        # Optional: compare models chart (advanced)
        st.write("")
        with st.expander("Advanced: compare all models on the same chart"):
            preds = {}
            for m in modes:
                s_pred, _info = forecast_series_for_mode(daily_total, forecast_days, m)
                preds[m] = s_pred
            comp_df = pd.DataFrame(preds)
            st.line_chart(comp_df)

    # =========================
    # EXPLAIN TAB
    # =========================
    with tab_explain:
        _section("Explain the forecasting in plain English", "This is written so staff/managers can understand it quickly.")

        _info_card(
            "What are we predicting?",
            "We predict **total units sold per day** (coffee + croissants combined), because it’s easiest for planning and waste reduction.",
        )

        _info_card(
            "Why do we test models on recent days?",
            "A model can look good in theory but perform badly in reality. "
            "So we do a simple test: train on older data → predict the most recent days → compare predictions to what actually happened.",
        )

        st.markdown("### What each model is doing")
        for k, v in mode_help.items():
            st.markdown(f"**{k}**")
            st.write(v)
            st.write("")

        _metric_help_block()

        with st.expander("How should we use this in the café? (operational)"):
            st.markdown(
                """
- Use the **weekly target** to plan ordering and prep.
- Use the **forecast total** for the next 4–8 weeks to plan staffing and stock.
- If the forecast band is wide, demand is unstable → plan conservatively (reduce overproduction).
- If the recommended model changes week-to-week, that’s normal; demand patterns shift.
                """
            )