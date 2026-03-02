# auth.py
from __future__ import annotations

import hashlib
import pandas as pd
import streamlit as st

from constants import USERS_FILE
from theme import theme_options  # [(key,label), ...]


def _pw_hash(password: str, salt: str) -> str:
    password_b = (password or "").encode("utf-8")
    salt_b = (salt or "").encode("utf-8")
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password_b, salt_b, iterations)
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def _pw_verify(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, hx = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters)
        test = hashlib.pbkdf2_hmac(
            "sha256",
            (password or "").encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return test == hx
    except Exception:
        return False


def ensure_users_file() -> None:
    if USERS_FILE.exists():
        return
    default = pd.DataFrame(
        [
            {"username": "admin", "role": "admin", "pw_hash": _pw_hash("admin123", "salt_admin")},
            {"username": "manager", "role": "manager", "pw_hash": _pw_hash("manager123", "salt_manager")},
            {"username": "staff", "role": "staff", "pw_hash": _pw_hash("staff123", "salt_staff")},
        ]
    )
    default.to_csv(USERS_FILE, index=False)


@st.cache_data
def load_users() -> pd.DataFrame:
    ensure_users_file()
    dfu = pd.read_csv(USERS_FILE)

    for c in ["username", "role", "pw_hash"]:
        if c not in dfu.columns:
            dfu[c] = ""

    dfu["username"] = dfu["username"].astype(str).str.strip().str.lower()
    dfu["role"] = dfu["role"].astype(str).str.strip().str.lower()
    dfu["pw_hash"] = dfu["pw_hash"].astype(str).str.strip()

    dfu = dfu[dfu["username"] != ""].drop_duplicates(subset=["username"], keep="last")
    return dfu.reset_index(drop=True)


def save_users(dfu: pd.DataFrame) -> None:
    out = dfu.copy()
    out["username"] = out["username"].astype(str).str.strip().str.lower()
    out["role"] = out["role"].astype(str).str.strip().str.lower()
    out["pw_hash"] = out["pw_hash"].astype(str).str.strip()
    out = out[out["username"] != ""].drop_duplicates(subset=["username"], keep="last")
    out.to_csv(USERS_FILE, index=False)
    st.cache_data.clear()


def get_user_record(username: str) -> dict | None:
    dfu = load_users()
    u = (username or "").strip().lower()
    hit = dfu[dfu["username"] == u]
    if hit.empty:
        return None
    r = hit.iloc[0].to_dict()
    return {"username": r["username"], "role": r["role"], "pw_hash": r["pw_hash"]}


def create_user(username: str, password: str, role: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    role = (role or "").strip().lower()

    if not u:
        return False, "Username is required."
    if role not in {"admin", "manager", "staff"}:
        return False, "Role must be admin, manager, or staff."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."

    dfu = load_users()
    if (dfu["username"] == u).any():
        return False, "That username already exists."

    salt = f"salt_{u}"
    pw_hash = _pw_hash(password, salt)
    dfu = pd.concat([dfu, pd.DataFrame([{"username": u, "role": role, "pw_hash": pw_hash}])], ignore_index=True)
    save_users(dfu)
    return True, "User created."


def update_password(username: str, new_password: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    if len(new_password or "") < 6:
        return False, "Password must be at least 6 characters."

    dfu = load_users()
    m = dfu["username"] == u
    if not m.any():
        return False, "User not found."

    salt = f"salt_{u}"
    dfu.loc[m, "pw_hash"] = _pw_hash(new_password, salt)
    save_users(dfu)
    return True, "Password updated."


def update_role(username: str, new_role: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    new_role = (new_role or "").strip().lower()
    if new_role not in {"admin", "manager", "staff"}:
        return False, "Role must be admin, manager, or staff."

    dfu = load_users()
    m = dfu["username"] == u
    if not m.any():
        return False, "User not found."

    dfu.loc[m, "role"] = new_role
    save_users(dfu)
    return True, "Role updated."


def delete_user(username: str) -> tuple[bool, str]:
    u = (username or "").strip().lower()
    if u == "admin":
        return False, "You can't delete the default admin account."

    dfu = load_users()
    before = len(dfu)
    dfu = dfu[dfu["username"] != u].copy()
    if len(dfu) == before:
        return False, "User not found."

    save_users(dfu)
    return True, "User deleted."


def login_gate() -> bool:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

    # Ensure theme exists even before login
    if "theme_key" not in st.session_state:
        st.session_state.theme_key = "blackpink_pro"

    if st.session_state.logged_in:
        return True

    left, mid, right = st.columns([1.2, 1, 1.2])
    with mid:
        st.markdown('<div class="bp-card">', unsafe_allow_html=True)
        st.markdown('<div class="bp-badge">BLACKPINK • Café Portal</div>', unsafe_allow_html=True)

        # ✅ Theme toggle (pill-style)
        opts = theme_options()  # [(key,label), ...]
        keys = [k for k, _ in opts]
        labels = [lbl for _, lbl in opts]

        current_key = st.session_state.theme_key if st.session_state.theme_key in keys else keys[0]
        current_label = labels[keys.index(current_key)]

        chosen_label = st.radio(
            "Theme",
            labels,
            horizontal=True,
            index=labels.index(current_label),
            key="login_theme_toggle",
        )

        chosen_key = keys[labels.index(chosen_label)]
        if chosen_key != st.session_state.theme_key:
            st.session_state.theme_key = chosen_key
            st.rerun()

        st.markdown("## Login")

        with st.form("bp_login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="admin, manager or staff")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Log in")

        if submit:
            u = (username or "").strip().lower()
            user = get_user_record(u)

            if user and _pw_verify(password, user["pw_hash"]):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                st.success(f"Welcome, {st.session_state.role.title()}.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown('<div class="bp-divider"></div>', unsafe_allow_html=True)
        st.caption("Default accounts (change immediately): admin/admin123, manager/manager123, staff/staff123")
        st.markdown("</div>", unsafe_allow_html=True)

    return False


def logout_button() -> None:
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()