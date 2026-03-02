# app.py
import streamlit as st

from constants import APP_TITLE, PRICE_FILE, DEFAULT_THEME
from theme import (
    apply_theme,
    hide_native_multipage_nav,
    inject_header_gap_fix,
)
from auth import login_gate, logout_button
from pages.staff import page_staff_record_sale
from pages.manager import page_manager_sales_overview, page_manager_sales_records
from pages.admin import page_admin_user_management
from pages.predictions import page_predictions_dashboard

st.set_page_config(page_title=APP_TITLE, layout="wide")

hide_native_multipage_nav()
inject_header_gap_fix()

if "theme_key" not in st.session_state:
    st.session_state.theme_key = DEFAULT_THEME

# Apply theme immediately (login page included)
apply_theme(st.session_state.theme_key)

if not login_gate():
    st.stop()

with st.sidebar:
    st.markdown("### Session")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")
    logout_button()
    st.markdown("---")

    if st.session_state.role == "admin":
        page = st.radio("Navigation", ["User Management", "Sales Overview", "Sales Records", "Predictions"], index=0)
    elif st.session_state.role == "manager":
        page = st.radio("Navigation", ["Sales Overview", "Sales Records", "Predictions"], index=0)
    else:
        page = st.radio("Navigation", ["Record Sale", "Predictions"], index=0)

if st.session_state.role == "admin" and page == "User Management":
    page_admin_user_management()
elif st.session_state.role in {"admin", "manager"} and page == "Sales Overview":
    page_manager_sales_overview()
elif st.session_state.role in {"admin", "manager"} and page == "Sales Records":
    page_manager_sales_records()
elif st.session_state.role == "staff" and page == "Record Sale":
    page_staff_record_sale()
else:
    page_predictions_dashboard()

if not PRICE_FILE.exists():
    st.warning("product_prices.csv was not found and a template should have been created. Please check your folder.")