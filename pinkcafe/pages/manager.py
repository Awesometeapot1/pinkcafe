from datetime import date
import pandas as pd
import streamlit as st

from theme import render_pink_header
from storage import load_sales_log, save_sales_log, _row_fingerprint, load_price_map
from forecasting import moving_average


def _chart_section_title(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)
    st.write("")

def _manager_page_css() -> None:
    st.markdown(
        """
        <style>
        /* ===== Manager page filters ===== */

        /* Select wrapper */
        div[data-baseweb="select"] > div {
            background: var(--bp-surface-2) !important;
            border: 1px solid rgba(255,105,180,0.25) !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 12px rgba(255,105,180,0.08) !important;
            transition: all 0.2s ease !important;
        }

        div[data-baseweb="select"] > div:hover {
            border: 1px solid rgba(255,105,180,0.40) !important;
        }

        div[data-baseweb="select"] > div:focus-within {
            border: 1px solid rgba(255,105,180,0.55) !important;
            box-shadow: 0 0 0 3px rgba(255,105,180,0.12) !important;
        }

        /* Closed select text */
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {
            color: var(--bp-text) !important;
            -webkit-text-fill-color: var(--bp-text) !important;
        }

        div[data-baseweb="select"] svg {
            color: var(--bp-text-dim) !important;
            fill: var(--bp-text-dim) !important;
        }

        /* Dropdown portal */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div {
            background: transparent !important;
        }

        /* Dropdown menu */
        ul[role="listbox"],
        div[data-baseweb="menu"],
        div[data-baseweb="popover"] ul {
            background: var(--bp-bg-2) !important;
            border: 1px solid var(--bp-border) !important;
            border-radius: 16px !important;
            box-shadow: 0 16px 36px rgba(0,0,0,0.18) !important;
            padding: 0.35rem !important;
        }

        li[role="option"],
        div[role="option"],
        ul[role="listbox"] li {
            background: transparent !important;
            color: var(--bp-text) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            opacity: 1 !important;
        }

        li[role="option"] *,
        div[role="option"] *,
        ul[role="listbox"] li * {
            color: var(--bp-text) !important;
            opacity: 1 !important;
        }

        li[role="option"]:hover,
        li[role="option"][aria-selected="true"],
        div[role="option"]:hover,
        div[role="option"][aria-selected="true"],
        ul[role="listbox"] li:hover,
        ul[role="listbox"] li[aria-selected="true"] {
            background: rgba(255,105,180,0.14) !important;
            color: var(--bp-text) !important;
        }

        li[role="option"]:hover *,
        li[role="option"][aria-selected="true"] *,
        div[role="option"]:hover *,
        div[role="option"][aria-selected="true"] *,
        ul[role="listbox"] li:hover *,
        ul[role="listbox"] li[aria-selected="true"] * {
            color: var(--bp-text) !important;
            opacity: 1 !important;
        }

        /* Kill weird focus artifacts */
        div[data-baseweb="select"] input:focus,
        div[data-baseweb="select"] input:focus-visible {
            outline: none !important;
            box-shadow: none !important;
            border: none !important;
        }

        div[data-baseweb="select"] div[role="combobox"] {
            box-shadow: none !important;
        }

        /* ===== DISABLE TYPING IN FILTER DROPDOWNS ===== */
        div[data-baseweb="select"] input {
            pointer-events: none !important;
            caret-color: transparent !important;
            user-select: none !important;
        }

        div[data-baseweb="select"] input::selection {
            background: transparent !important;
            color: transparent !important;
        }

        div[data-baseweb="select"] input::-moz-selection {
            background: transparent !important;
            color: transparent !important;
        }

        /* ===== Buttons ===== */
        .stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(90deg, #ff2f92, #f062b5) !important;
            color: white !important;
            border: none !important;
            border-radius: 16px !important;
            min-height: 48px !important;
            font-weight: 700 !important;
            box-shadow: 0 10px 24px rgba(255,47,146,0.22) !important;
        }

        .stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            filter: brightness(1.03);
            transform: translateY(-1px);
        }

        .stButton > button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled {
            opacity: 0.55 !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _safe_date_range_input(label: str, dmin: date, dmax: date):
    picked = st.date_input(label, value=(dmin, dmax))
    if isinstance(picked, tuple) and len(picked) == 2:
        return picked[0], picked[1]
    if isinstance(picked, list) and len(picked) == 2:
        return picked[0], picked[1]
    return dmin, dmax


def _record_label(r: pd.Series) -> str:
    d = pd.to_datetime(r.get("date"), errors="coerce")
    qty = int(r.get("qty", 0)) if pd.notna(r.get("qty", 0)) else 0
    total = float(r.get("total", 0.0)) if pd.notna(r.get("total", 0.0)) else 0.0
    product = str(r.get("product", "")).strip()

    created_at = pd.to_datetime(r.get("created_at"), errors="coerce")

    date_str = d.strftime("%d %b %Y") if pd.notna(d) else "No date"
    time_str = created_at.strftime("%H:%M") if pd.notna(created_at) else "No time"

    return f"{product} — {qty} sold   •   £{total:.2f}   •   {date_str} · {time_str}"


def page_manager_sales_overview() -> None:
    render_pink_header(
        "Manager • Sales Overview",
        "Track sales performance, trends, and top-selling products."
    )

    _manager_page_css()

    df = load_sales_log()
    if df.empty or df["date"].isna().all():
        st.info("No sales recorded yet.")
        return

    df = df.dropna(subset=["date"]).copy()
    df["day"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["day"]).copy()

    dmin = df["day"].min()
    dmax = df["day"].max()

    st.markdown("### Overview filters")
    f1, f2, f3 = st.columns([1, 1, 1])

    with f1:
        date_from, date_to = _safe_date_range_input("Date range", dmin, dmax)

    with f2:
        products = ["All products"] + sorted(df["product"].dropna().astype(str).unique().tolist())
        selected_product = st.selectbox("Product", products, index=0)

    with f3:
        staff_users = ["All staff"] + sorted(df["staff_user"].dropna().astype(str).unique().tolist())
        selected_staff = st.selectbox("Staff user", staff_users, index=0)

    out = df.copy()
    out = out[(out["day"] >= date_from) & (out["day"] <= date_to)]

    if selected_product != "All products":
        out = out[out["product"] == selected_product]

    if selected_staff != "All staff":
        out = out[out["staff_user"] == selected_staff]

    if out.empty:
        st.warning("No sales match the selected filters.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total units", int(out["qty"].sum()))
    c2.metric("Total revenue", f"£{out['total'].sum():.2f}")
    c3.metric("Transactions", int(len(out)))
    c4.metric("Products sold", int(out["product"].nunique()))

    st.write("")

    revenue_daily = out.groupby("day")["total"].sum().sort_index()
    rev_ma7 = moving_average(revenue_daily, 7)

    _chart_section_title(
        "Daily revenue",
        "Daily revenue with a 7-day moving average."
    )
    st.bar_chart(pd.DataFrame({"Daily revenue": revenue_daily}))
    st.line_chart(pd.DataFrame({"7-day average": rev_ma7}))

    _chart_section_title("Weekly revenue", "Revenue aggregated by week.")
    weekly_rev = out.groupby(out["date"].dt.to_period("W"))["total"].sum()
    weekly_rev.index = weekly_rev.index.astype(str)
    st.bar_chart(weekly_rev)

    _chart_section_title("Units sold per day", "Daily units sold, with a 7-day moving average shown as a line.")
    units_daily = out.groupby("day")["qty"].sum().sort_index()
    units_ma7 = moving_average(units_daily, 7)
    st.bar_chart(pd.DataFrame({"Daily units": units_daily}))
    st.line_chart(pd.DataFrame({"7-day average": units_ma7}))

    st.markdown("## Top-performing products")
    by_prod = out.groupby("product")["total"].sum().sort_values(ascending=False)
    st.bar_chart(by_prod)

    st.markdown("### Product performance breakdown")
    top_products = (
        out.groupby("product", as_index=False)
        .agg(
            units_sold=("qty", "sum"),
            revenue=("total", "sum"),
            transactions=("product", "count"),
        )
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    top_products["revenue"] = top_products["revenue"].map(lambda x: f"£{float(x):.2f}")
    st.dataframe(top_products, use_container_width=True)

    st.markdown("### Recent sales")
    recent = out.sort_values(["date", "created_at"], ascending=[False, False]).head(10).copy()
    recent_show = recent[["date", "product", "qty", "unit_price", "total", "staff_user", "created_at"]]
    recent_show["date"] = pd.to_datetime(recent_show["date"], errors="coerce").dt.date.astype(str)
    recent_show["unit_price"] = recent_show["unit_price"].map(lambda x: f"£{float(x):.2f}")
    recent_show["total"] = recent_show["total"].map(lambda x: f"£{float(x):.2f}")
    st.dataframe(recent_show, use_container_width=True)


def page_manager_sales_records() -> None:
    render_pink_header(
        "Manager • Sales Records",
        "Filter, review, export, and manage (edit/delete) the sales log."
    )

    _manager_page_css()

    df = load_sales_log()
    if df.empty:
        st.info("No sales recorded yet.")
        return

    df = df.dropna(subset=["date"]).copy()
    df["day"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["day"]).copy()

    products = sorted(df["product"].dropna().astype(str).unique().tolist())
    staff_users = sorted(df["staff_user"].dropna().astype(str).unique().tolist())

    st.markdown("### Filters")
    f1, f2, f3, f4 = st.columns([1, 1, 1.4, 1])

    with f1:
        f_product = st.selectbox("Product", ["All products"] + products, index=0)

    with f2:
        f_staff = st.selectbox("Staff user", ["All staff"] + staff_users, index=0)

    with f3:
        dmin = df["day"].min()
        dmax = df["day"].max()
        d_from, d_to = _safe_date_range_input("Date range", dmin, dmax)

    with f4:
        search_text = st.text_input("Search", placeholder="Product, staff, date...").strip().lower()

    out = df.copy()

    if f_product != "All products":
        out = out[out["product"] == f_product]

    if f_staff != "All staff":
        out = out[out["staff_user"] == f_staff]

    out = out[(out["day"] >= d_from) & (out["day"] <= d_to)]

    if search_text:
        mask = (
            out["product"].astype(str).str.lower().str.contains(search_text, na=False)
            | out["staff_user"].astype(str).str.lower().str.contains(search_text, na=False)
            | out["created_at"].astype(str).str.lower().str.contains(search_text, na=False)
            | out["day"].astype(str).str.lower().str.contains(search_text, na=False)
        )
        out = out[mask]

    m1, m2, m3 = st.columns(3)
    m1.metric("Filtered rows", int(len(out)))
    m2.metric("Filtered units", int(out["qty"].sum()) if not out.empty else 0)
    m3.metric("Filtered revenue", f"£{out['total'].sum():.2f}" if not out.empty else "£0.00")

    st.write("")
    st.subheader("Records")

    if out.empty:
        st.info("No rows match the current filters.")
        return

    show = out[["date", "product", "qty", "unit_price", "total", "staff_user", "created_at"]].copy()
    show["date"] = pd.to_datetime(show["date"], errors="coerce").dt.date.astype(str)
    show["unit_price"] = show["unit_price"].map(lambda x: f"£{float(x):.2f}")
    show["total"] = show["total"].map(lambda x: f"£{float(x):.2f}")
    st.dataframe(show, use_container_width=True)

    csv_bytes = out.drop(columns=["day"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered sales (CSV)",
        data=csv_bytes,
        file_name="sales_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.write("")
    st.markdown("## Sales records")
    st.caption("Select a record below to review, update, or remove.")

    out = out.copy()
    out["_row_id"] = out.apply(_row_fingerprint, axis=1)

    options = out["_row_id"].tolist()
    label_map = {rid: _record_label(out.loc[idx]) for idx, rid in zip(out.index, options)}

    selected_id = st.selectbox(
        "Choose a record",
        options=options,
        format_func=lambda rid: label_map.get(rid, rid),
    )

    selected_filtered_row = out[out["_row_id"] == selected_id].iloc[0]
    selected_index = selected_filtered_row.name
    current = df.loc[selected_index].copy()

    price_map = load_price_map()
    known_products = sorted(set(list(price_map.keys()) + df["product"].dropna().astype(str).tolist()))

    st.markdown('<div class="bp-badge">Manager actions</div>', unsafe_allow_html=True)

    cA, cB = st.columns([3, 1])

    with cA:
        st.markdown("#### Edit record")

        with st.form("manager_edit_form", clear_on_submit=False):
            cur_date = pd.to_datetime(current["date"], errors="coerce")
            default_date = cur_date.date() if pd.notna(cur_date) else date.today()
            new_date = st.date_input("Date", value=default_date, key="mgr_edit_date")

            cur_product = str(current.get("product", "")).strip()
            if cur_product and cur_product not in known_products:
                known_products = [cur_product] + known_products

            prod_index = known_products.index(cur_product) if cur_product in known_products else 0
            new_product = st.selectbox("Product", known_products, index=prod_index, key="mgr_edit_product")

            suggested_price = (
                float(price_map[new_product])
                if new_product in price_map
                else float(current.get("unit_price", 0.0))
            )
            new_unit_price = st.number_input(
                "Unit price (£)",
                min_value=0.0,
                step=0.05,
                value=float(suggested_price),
                key="mgr_edit_unit_price",
            )

            new_qty = st.number_input(
                "Quantity sold",
                min_value=0,
                step=1,
                value=int(current.get("qty", 0)),
                key="mgr_edit_qty",
            )

            new_staff_user = st.text_input(
                "Recorded by",
                value=str(current.get("staff_user", "")).strip().lower(),
                key="mgr_edit_staff",
            )

            st.text_input(
                "Recorded at",
                value=str(current.get("created_at", "")).strip(),
                key="mgr_edit_created_at",
                disabled=True,
            )

            preview_total = float(new_unit_price) * int(new_qty)
            st.info(f"Updated total will be: £{preview_total:.2f}")

            save_btn = st.form_submit_button("Save changes", use_container_width=True)

        if save_btn:
            df2 = df.copy()
            df2.loc[selected_index, "date"] = pd.to_datetime(str(new_date), errors="coerce")
            df2.loc[selected_index, "product"] = str(new_product).strip()
            df2.loc[selected_index, "qty"] = int(new_qty)
            df2.loc[selected_index, "unit_price"] = float(new_unit_price)
            df2.loc[selected_index, "total"] = float(new_unit_price) * int(new_qty)
            df2.loc[selected_index, "staff_user"] = str(new_staff_user).strip().lower()

            save_sales_log(df2)
            st.success("Entry updated.")
            st.rerun()

    with cB:
        st.markdown("#### Delete record")
        st.caption("This action permanently removes the record and cannot be undone.")

        confirm_delete = st.checkbox(
            "I confirm I want to delete this record",
            key="mgr_delete_confirm"
        )

        delete_btn = st.button(
            "Delete record",
            type="primary",
            use_container_width=True,
            disabled=not confirm_delete,
        )

        if delete_btn:
            df2 = df.drop(index=selected_index).copy()
            save_sales_log(df2)
            st.success("Entry deleted.")
            st.rerun()
