# pages/predictions.py
from __future__ import annotations

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
# Small UI helpers
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
    # Professional labels for legends + CSV headers
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


# ----------------------------
# Page
# ----------------------------
def page_predictions_dashboard() -> None:
    render_pink_header(
        "Predictions",
        "Upload café CSVs → understand trends → compare models → export forecasts.",
    )

    mode_help = _model_explanations()
    modes = list(mode_help.keys())
    label_map = _model_label_map()

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

    tab_overview, tab_forecast, tab_explain = st.tabs(["Overview", "Forecast", "Explain"])

    # =========================
    # OVERVIEW TAB (your original layout, lightly polished)
    # =========================
    with tab_overview:
        _section("Step 2 — Understand your sales", "Patterns and weekly behaviour.")

        colL, colR = st.columns([3, 2])

        with colL:
            _section("Daily total units sold", "Bars = daily units, line = 7-day moving average.")
            st.bar_chart(daily_total)
            st.line_chart(daily_ma7)

            _section("Top products", "Best-selling items overall.")
            totals = (
                df_all.groupby("product")["units_sold"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(totals.head(10))

        with colR:
            _section("Weekday pattern", "Average units sold by day of week.")

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
            _section("Practical weekly target", "A simple planning figure (based on last 14 days).")
            suggested_weekly = int(daily_total.tail(14).mean() * 7) if len(daily_total) else 0
            st.markdown(f"### Suggested weekly target: **{suggested_weekly:,} units**")
            st.caption("Use this as a starting point when ordering ingredients / staffing.")

    # =========================
    # FORECAST TAB (new design)
    # =========================
    with tab_forecast:
        _section("Forecast settings")

        horizon_weeks = st.radio("Forecast horizon", [4, 8], horizontal=True)
        forecast_days = horizon_weeks * 7

        holdout_days = st.slider("Days to test models on (holdout)", 7, 28, 14, step=7)

        # Evaluate models on holdout
        metrics_df, best_mode = evaluate_models_time_holdout(daily_total, holdout_days, modes)
        st.markdown(_recommendation_text(best_mode, holdout_days, label_map))

        _metric_help_block()

        if not metrics_df.empty:
            metrics_show = metrics_df.copy()
            if "Model" in metrics_show.columns:
                metrics_show["Model"] = metrics_show["Model"].map(lambda x: label_map.get(x, x))
            st.dataframe(metrics_show, use_container_width=True)

        # Normalised daily series
        s = daily_total.copy().sort_index().asfreq("D").fillna(0)

        # =====================================================
        # Main comparison chart (ALL models)
        # =====================================================
        st.write("")
        _section(
            "Compare all models on one graph",
            "Switch between Holdout (vs actual) and Future (model forecasts).",
        )

        compare_mode = st.radio(
            "Comparison view",
            ["Holdout (compare to actual)", "Future (compare forecasts)"],
            horizontal=True,
        )

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

        # =====================================================
        # Downloads
        # =====================================================
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

        # =====================================================
        # Chosen model forecast + band + download
        # =====================================================
        st.write("")
        _section("Chosen model forecast", "Forecast with an uncertainty band for planning.")

        use_recommended = st.toggle("Use recommended model", value=True)
        if use_recommended and best_mode:
            chosen_mode = best_mode
        else:
            pretty_choices = [label_map.get(m, m) for m in modes]
            chosen_pretty = st.radio("Model", pretty_choices, horizontal=True)
            rev = {label_map.get(m, m): m for m in modes}
            chosen_mode = rev.get(chosen_pretty, modes[0])

        pred_series, _ = forecast_series_for_mode(s, forecast_days, chosen_mode)
        band_df = make_pred_band(pred_series, s)

        chosen_label = label_map.get(chosen_mode, chosen_mode)
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

    # =========================
    # EXPLAIN TAB
    # =========================
    with tab_explain:
        _section("Explain the forecasting", "Plain-English summary of each model.")
        for k, v in mode_help.items():
            st.markdown(f"**{label_map.get(k, k)}**")
            st.write(v)