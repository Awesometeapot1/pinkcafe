import streamlit as st
from theme import render_pink_header
from auth import load_users, create_user, update_password, update_role, delete_user


def page_admin_user_management() -> None:
    dfu = load_users()
    show = dfu[["username", "role"]].sort_values(["role", "username"]).reset_index(drop=True)
    users = show["username"].tolist()

    total_users = len(show)
    total_admins = int((show["role"] == "admin").sum())
    total_managers = int((show["role"] == "manager").sum())
    total_staff = int((show["role"] == "staff").sum())

    st.markdown(
        """
        <style>
        /* ===== Base ===== */
        body, .stApp {
            color: var(--bp-text) !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--bp-text) !important;
        }

        p, label, .stCaption, .stMarkdown, .stText {
            color: var(--bp-text-dim) !important;
        }

        .admin-top-note {
            color: var(--bp-text-dim) !important;
        }

        .admin-section-note {
            color: var(--bp-text-mute) !important;
        }

        /* ===== Metric cards ===== */
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,105,180,0.14) !important;
            border-radius: 20px !important;
            padding: 0.9rem !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.26) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--bp-text-mute) !important;
            font-weight: 600 !important;
        }

        div[data-testid="stMetricValue"] {
            color: var(--bp-text) !important;
            font-weight: 800 !important;
        }

        /* ===== Tabs ===== */
        div[data-baseweb="tab-list"] {
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            gap: 0.8rem !important;
            background: transparent !important;
            border-bottom: none !important;
            margin-top: 0.8rem !important;
            margin-bottom: 0.9rem !important;
        }

        button[data-baseweb="tab"] {
            background: rgba(255,255,255,0.06) !important;
            color: var(--bp-text-mute) !important;
            border-radius: 18px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            min-height: 52px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease !important;
        }

        button[data-baseweb="tab"]:hover {
            background: rgba(255,105,180,0.12) !important;
            color: var(--bp-text) !important;
            border: 1px solid rgba(255,105,180,0.24) !important;
        }

        button[aria-selected="true"] {
            background: linear-gradient(180deg, rgba(255,105,180,0.16), rgba(255,105,180,0.10)) !important;
            color: #FF6FB5 !important;
            border: 1px solid rgba(255,105,180,0.36) !important;
            box-shadow: 0 10px 20px rgba(255,105,180,0.10) !important;
        }

        button[data-baseweb="tab"]::after {
            display: none !important;
        }

        /* ===== Real tab panel ===== */
        div[data-testid="stTabs"] > div:nth-of-type(2) {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        div[data-testid="stTabs"] div[role="tabpanel"] {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 22px !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.22) !important;
            padding: 1.2rem !important;
            margin: 0 !important;
        }

        div[data-testid="stTabs"] div[role="tabpanel"] > div {
            padding-top: 0 !important;
        }

        div[data-testid="stTabs"] div[role="tabpanel"]::before {
            content: none !important;
            display: none !important;
        }

        /* ===== Text input wrappers ===== */
        div[data-baseweb="input"] > div {
            background: var(--bp-input-bg) !important;
            border: 1px solid rgba(255,105,180,0.25) !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 12px rgba(255,105,180,0.08) !important;
            transition: all 0.2s ease !important;
        }

        div[data-baseweb="input"] > div:focus-within {
            border: 1px solid rgba(255,105,180,0.55) !important;
            box-shadow: 0 0 0 3px rgba(255,105,180,0.12) !important;
        }

        /* ===== Select wrappers ===== */
        div[data-baseweb="select"] > div {
            background: var(--bp-surface-2) !important;
            border: 1px solid rgba(255,105,180,0.25) !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 12px rgba(255,105,180,0.08) !important;
            transition: all 0.2s ease !important;
        }

        div[data-baseweb="select"] > div:focus-within {
            border: 1px solid rgba(255,105,180,0.55) !important;
            box-shadow: 0 0 0 3px rgba(255,105,180,0.12) !important;
        }

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

        /* ===== Text inputs ===== */
        .stTextInput input,
        .stTextInput input[type="text"],
        .stTextInput input[type="password"],
        div[data-baseweb="base-input"] input,
        div[data-baseweb="input"] input {
            background: transparent !important;
            color: var(--bp-input-text) !important;
            -webkit-text-fill-color: var(--bp-input-text) !important;
            caret-color: var(--bp-input-text) !important;
            opacity: 1 !important;
            text-shadow: none !important;
        }

        /* placeholder */
        .stTextInput input::placeholder,
        div[data-baseweb="input"] input::placeholder {
            color: var(--bp-input-placeholder) !important;
            -webkit-text-fill-color: var(--bp-input-placeholder) !important;
            opacity: 1 !important;
        }

        /* ===== Hover ===== */
        div[data-baseweb="select"] > div:hover {
            border: 1px solid rgba(255,105,180,0.40) !important;
        }

        /* ===== Dropdown portal / opened menu ===== */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] > div {
            background: transparent !important;
        }

        /* ===== Dropdown menu (theme-aware) ===== */
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

        /* ===== FIX DROPDOWN TEXT COLOR ===== */
        ul[role="listbox"] li,
        ul[role="listbox"] li *,
        div[role="option"],
        div[role="option"] * {
            color: #FFFFFF !important;
            opacity: 1 !important;
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

        /* ===== Dataframe ===== */
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 16px !important;
            overflow: hidden !important;
        }

        /* ===== Danger Zone (Adaptive: Light + Dark) ===== */
        .danger-zone {
            background: linear-gradient(
                135deg,
                rgba(255, 77, 109, 0.12),
                rgba(255, 0, 60, 0.08)
            );
            border: 1.5px solid rgba(255, 77, 109, 0.45);
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 20px;
            box-shadow: 0 6px 20px rgba(255, 0, 60, 0.15);
        }

        /* Title */
        .danger-zone h3 {
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 10px;
            
            /* adaptive color */
            color: var(--bp-pink-2);
        }

        /* Text */
        .danger-zone p {
            font-size: 15px;
            margin: 4px 0;

            /* adaptive readable text */
            color: var(--bp-text);
        }

        /* make icons pop slightly */
        .danger-zone span {
            filter: saturate(1.2);
        }

        /* ===== Alerts ===== */
        div[data-testid="stAlert"] {
            border-radius: 14px !important;
        }

        /* ===== Responsive ===== */
        @media (max-width: 900px) {
            div[data-baseweb="tab-list"] {
                grid-template-columns: 1fr 1fr !important;
            }
        }

        @media (max-width: 640px) {
            div[data-baseweb="tab-list"] {
                grid-template-columns: 1fr !important;
            }
        }

        /* selection highlight */
        div[data-baseweb="input"] input::selection,
        div[data-baseweb="select"] input::selection {
            background: rgba(255,255,255,0.18) !important;
            color: #ffffff !important;
        }

        div[data-baseweb="input"] input::-moz-selection,
        div[data-baseweb="select"] input::-moz-selection {
            background: rgba(255,255,255,0.18) !important;
            color: #ffffff !important;
        }

        /* kill weird focus artifacts on searchable select */
        div[data-baseweb="select"] input:focus,
        div[data-baseweb="select"] input:focus-visible,
        div[data-baseweb="input"] input:focus,
        div[data-baseweb="input"] input:focus-visible {
            outline: none !important;
            box-shadow: none !important;
        }

        div[data-baseweb="select"] input {
            border: none !important;
        }

        div[data-baseweb="select"] div[role="combobox"] {
            box-shadow: none !important;
        }

        /* ===== DISABLE TYPING IN ALL DROPDOWNS ===== */
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

        </style>
        """,
        unsafe_allow_html=True,
    )

    render_pink_header(
        "Admin • User Management",
        "Create accounts, reset passwords, manage roles, and remove users."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total users", total_users)
    c2.metric("Admins", total_admins)
    c3.metric("Managers", total_managers)
    c4.metric("Staff", total_staff)

    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Users",
        "Create User",
        "Security",
        "Delete User"
    ])

    with tab1:
        st.subheader("Current users")
        st.markdown(
            '<div class="admin-section-note">View all registered accounts and update role permissions when needed.</div>',
            unsafe_allow_html=True
        )

        st.dataframe(show, use_container_width=True, hide_index=True)

        st.write("")
        st.subheader("Change role")

        if users:
            col1, col2 = st.columns(2)
            target2 = col1.selectbox("User", users, key="role_user_pick")
            options = ["staff", "manager", "admin"]

            new_role2 = col2.selectbox(
                "New role",
                options,
                index=None,
                placeholder="Select new role", 
                key="new_role_pick"
            )

            if st.button("Update role", use_container_width=True):
                if new_role2 is None:
                    st.error("Please select a role.")
                else:
                    ok, msg = update_role(target2, new_role2)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        else:
            st.info("No users found.")

    with tab2:
        st.subheader("Create a new user")
        st.markdown(
            '<div class="admin-section-note">Add a new account and assign the correct permission level from the start.</div>',
            unsafe_allow_html=True
        )

        with st.form("admin_create_user", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            new_u = col1.text_input("Username")
            new_role = col2.selectbox(
                "Role",
                ["staff", "manager", "admin"],
                index=None,
                placeholder="Select a role"
            )
            new_pw = st.text_input("Temporary password", type="password")

            create_btn = st.form_submit_button("Create user", use_container_width=True)

        if create_btn:
            username = new_u.strip().lower()

            if not username:
                st.error("Username cannot be empty.")
            elif " " in username:
                st.error("Username cannot contain spaces.")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_role is None:
                st.error("Please select a role.")
            else:
                ok, msg = create_user(username, new_pw, new_role)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    with tab3:
        st.subheader("Reset password")
        st.markdown(
            '<div class="admin-section-note">Update a user password securely when credentials need to be reset.</div>',
            unsafe_allow_html=True
        )

        if users:
            target = st.selectbox(
                "",
                users,
                index=None,
                placeholder="Select a user",
                key="reset_user_pick"
            )

            with st.form("admin_reset_pw", clear_on_submit=True):
                pw1 = st.text_input("New password", type="password")
                reset_btn = st.form_submit_button("Update password", use_container_width=True)

            if reset_btn:
                if target is None:
                    st.error("Please select a user.")
                elif len(pw1) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = update_password(target, pw1)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        else:
            st.info("No users found.")

    with tab4:
        st.subheader("Delete user")
        st.markdown("""
        <div class="danger-zone">
            <h3>🚨 Danger Zone 🚨</h3>
            <p>⚠️ Deleting a user is permanent and cannot be undone.</p>
            <p>⚠️ The admin account cannot be deleted.</p>
        </div>
        """, unsafe_allow_html=True
        )

        if users:
            target3 = st.selectbox(
                "",
                users,
                index=None,
                placeholder="Select a user to delete",
                key="delete_user_pick"
            )
            confirm_delete = st.checkbox("I understand this action cannot be undone")

            if st.button("Delete user", type="primary", disabled=not confirm_delete, use_container_width=True):
                if target3 is None:
                    st.error("Please select a user.")
                else:
                    ok, msg = delete_user(target3)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            st.info("No users found.")
