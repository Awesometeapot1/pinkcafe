# auth.py
from __future__ import annotations

import hashlib
import pandas as pd
import streamlit as st

from constants import USERS_FILE
from theme import theme_options, apply_theme  

# Password hashing / verification
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

# User storage
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

# UI styling
def _inject_login_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stHeader"] {
            display: none !important;
        }

        #MainMenu,
        footer {
            visibility: hidden !important;
        }

        /* Background covers full viewport always */
        [data-testid="stAppViewContainer"] {
            min-height: 100vh !important;
            background:
                radial-gradient(circle at 50% 0%, rgba(255, 90, 170, 0.18), transparent 26%),
                radial-gradient(circle at 20% 18%, rgba(255, 255, 255, 0.035), transparent 18%),
                radial-gradient(circle at 80% 20%, rgba(255, 90, 170, 0.06), transparent 18%),
                linear-gradient(180deg, #05050a 0%, #0a0a12 100%);
            background-attachment: fixed !important;
        }

        [data-testid="stMain"] {
            min-height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: flex-start !important;
            overflow-y: auto !important;
        }

        .block-container {
            width: 100% !important;
            max-width: 460px !important;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        @media (max-width: 500px) {
            .block-container {
                padding-left: 0.85rem !important;
                padding-right: 0.85rem !important;
            }
        }

        /* Login card */
        .bp-login-glow {
            position: relative;
            border-radius: 28px;
            padding: 1.75rem 1.75rem 1.4rem 1.75rem;
            margin-top: -1rem !important;
            margin-bottom: 1.1rem !important;
            background: linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.02));
            border: 1px solid rgba(255, 105, 180, 0.16);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow:
                0 18px 50px rgba(0, 0, 0, 0.42),
                0 0 80px rgba(255, 80, 170, 0.14),
                inset 0 1px 0 rgba(255,255,255,0.04);
            overflow: hidden;
        }

        .bp-login-glow::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 28px;
            padding: 1px;
            background: linear-gradient(
                120deg,
                rgba(255,255,255,0.04),
                rgba(255,105,180,0.45),
                rgba(255,255,255,0.03)
            );
            -webkit-mask:
                linear-gradient(#000 0 0) content-box,
                linear-gradient(#000 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }

        .bp-login-glow::after {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            right: -90px;
            top: -110px;
            background: radial-gradient(circle, rgba(255, 90, 170, 0.20), transparent 70%);
            pointer-events: none;
            filter: blur(8px);
        }

        /* Typography */
        .bp-brand {
            text-align: center;
            margin-bottom: 1rem;
        }

        .bp-wordmark {
            font-family: var(--bp-font-display, "Inter", sans-serif);
            font-size: 2.1rem;
            font-weight: 500;
            line-height: 1;
            letter-spacing: -0.04em;
            color: var(--bp-text, #f7f7fb);
            margin-bottom: 0.3rem;
        }

        .bp-wordmark .pink {
            color: var(--bp-pink, #ff63b8);
            text-shadow: 0 0 16px rgba(255, 99, 184, 0.30);
        }

        .bp-tagline {
            font-family: var(--bp-font-body, "Inter", sans-serif);
            font-size: 0.72rem;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: var(--bp-text-mute, #acacba);
        }

        .bp-section-title {
            font-family: var(--bp-font-display, "Inter", sans-serif);
            font-size: 1.35rem;
            line-height: 1.15;
            color: var(--bp-text, #f7f7fb);
            margin: 0.2rem 0 0.1rem 0;
        }

        .bp-section-subtitle {
            color: var(--bp-text-mute, #acacba);
            font-size: 0.86rem;
            margin-bottom: 0.6rem;
        }

        .bp-footer {
            text-align: center;
            margin-top: 0.65rem;
            font-size: 0.68rem;
            line-height: 1.6;
            color: var(--bp-text-mute, #acacba);
        }

        /* Tighten Streamlit's default widget spacing  */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            gap: 0 !important;
        }

        .stTextInput        { margin-bottom: 0.35rem !important; }
        .stRadio            { margin-bottom: 0.35rem !important; }
        .stCheckbox         { margin-bottom: 0.2rem  !important; }

        /* Input fields  */
        div[data-baseweb="input"] > div {
            border-radius: 14px !important;
            background: rgba(255,255,255,0.025) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            box-shadow: none !important;
            overflow: visible !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }

        /* Input text — inherit theme color instead of forcing white */
        div[data-baseweb="input"] input,
        div[data-testid="stForm"] input {
            color: inherit !important;
            caret-color: #ff63b8 !important;
            -webkit-text-fill-color: inherit !important;
        }

        /* Placeholder text */
        div[data-baseweb="input"] input::placeholder {
            color: rgba(172, 172, 186, 0.6) !important;
            -webkit-text-fill-color: rgba(172, 172, 186, 0.6) !important;
        }

        /* Hide "Press Enter to submit form" */
        [data-testid="InputInstructions"],
        div[class*="InputInstructions"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Pink border for the Sign in form box */
        div[data-testid="stForm"] {
            border: 1px solid rgba(255, 105, 180, 0.26) !important;
            border-radius: 20px !important;
            box-shadow:
                0 0 0 1px rgba(255, 105, 180, 0.06),
                0 0 24px rgba(255, 80, 170, 0.06) !important;
            background: transparent !important;
            padding: 1.15rem 1.15rem 1rem 1.15rem !important;
        }

        
        div[data-baseweb="input"] > div:focus-within {
            border-color: rgba(255, 99, 184, 0.26) !important;
            box-shadow: 0 0 0 1px rgba(255, 99, 184, 0.18),
                        0 0 18px rgba(255, 99, 184, 0.10) !important;
        }

        div[data-baseweb="input"] input {
            border-radius: 0 !important;
            background: transparent !important;
        }

        div[data-testid="stForm"] input,
        div[data-testid="stForm"] button,
        div[data-testid="stForm"] label {
            font-size: revert !important;
        }

        /* Eye Icon */
        div[data-testid="InputRightElement"] {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding-right: 0.7rem !important;
            padding-left: 0.25rem !important;
            margin: 0 !important;
        }

        /* reset EVERY wrapper inside the right element */
        div[data-testid="InputRightElement"] > *,
        div[data-testid="InputRightElement"] button,
        div[data-testid="InputRightElement"] [data-baseweb="button"],
        div[data-testid="InputRightElement"] div,
        div[data-testid="InputRightElement"] span {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            margin: 0 !important;
        }

        /* kill pill sizing */
        div[data-testid="InputRightElement"] button,
        div[data-testid="InputRightElement"] [data-baseweb="button"] {
            padding: 0 !important;
            min-width: 0 !important;
            width: auto !important;
            height: auto !important;
            border-radius: 0 !important;
        }

        /* icon only */
        div[data-testid="InputRightElement"] svg {
            width: 1.05rem !important;
            height: 1.05rem !important;
            display: block !important;
            color: rgba(255, 99, 184, 0.82) !important;
            fill: rgba(255, 99, 184, 0.82) !important;
        }

        /* Misc */
        div[role="radiogroup"] {
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 14px !important;
            min-height: 2.6rem !important;
            font-weight: 600 !important;
            border: 1px solid rgba(255, 99, 184, 0.30) !important;
            box-shadow: 0 0 24px rgba(255, 99, 184, 0.10) !important;
        }

        /* Accessibility Expander */
        [data-testid="stExpander"] {
            border: 1px solid rgba(255, 105, 180, 0.26) !important;
            border-radius: 16px !important;
            background: rgba(255, 255, 255, 0.03) !important;
        }

        [data-testid="stExpander"] summary {
            padding: 0.8rem 1rem !important;
            color: var(--bp-text, #f7f7fb) !important;
        }

        [data-testid="stExpanderDetails"] {
            padding: 0.6rem 1rem 1rem 1rem !important;
        }

        /* Slider */
        [data-testid="stSlider"] div[data-baseweb="slider"] {
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
        }

        [data-testid="stSlider"] div[data-baseweb="slider"] + div,
        [data-testid="stSlider"] [data-testid="stTickBar"],
        [data-testid="stSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-testid="stTickBarMax"] {
            display: none !important;
        }

        [data-testid="stSlider"] div[data-baseweb="slider"] > div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child {
            height: 4px !important;
            border-radius: 999px !important;
            background: rgba(255,255,255,0.14) !important;
            overflow: visible !important;
        }

        [data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child > div:first-child {
            height: 4px !important;
            border-radius: 999px !important;
            background: #ff63b8 !important;
        }

        [data-testid="stSlider"] [role="slider"] {
            width: 20px !important;
            height: 20px !important;
            border-radius: 50% !important;
            background: #ff63b8 !important;
            border: 3px solid rgba(255, 192, 223, 0.95) !important;
            box-shadow:
                0 0 0 5px rgba(255,99,184,0.18),
                0 0 18px rgba(255,99,184,0.42) !important;
            top: -2px !important;
        }

        [data-testid="stSlider"] [role="slider"]:focus {
            outline: none !important;
            box-shadow:
                0 0 0 6px rgba(255,99,184,0.22),
                0 0 20px rgba(255,99,184,0.48) !important;
        }

        [data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
            color: #ffffff !important;
            font-size: 0.74rem !important;
            font-weight: 700 !important;
            background: transparent !important;
        }

        [data-testid="stSlider"] label p {
            font-size: 0.80rem !important;
            color: var(--bp-text, #f7f7fb) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Auth views
def login_gate() -> bool:
    # Session init
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None

    # Theme defaults (pre-login safe)
    if "theme_key" not in st.session_state:
        st.session_state.theme_key = "blackpink_pro"

    # Accessibility defaults (pre-login safe)
    if "a11y_text_scale" not in st.session_state:
        st.session_state.a11y_text_scale = 1.0
        
    if "a11y_reduced_motion" not in st.session_state:
        st.session_state.a11y_reduced_motion = False

    apply_theme(
        st.session_state.theme_key,
        text_scale=st.session_state.a11y_text_scale,
        reduced_motion=st.session_state.a11y_reduced_motion,
    )

    if st.session_state.logged_in:
        return True

    st.markdown(
        """
        <div class="bp-login-glow">
            <div class="bp-brand">
                <div class="bp-wordmark">Bristol <span class="pink">Pink Café</span></div>
                <div class="bp-tagline">Management Portal</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    #Theme toggle
    opts = theme_options()      # [(key,label), ...]
    keys = [k for k, _ in opts]
    labels = [label for _, label in opts]

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
        apply_theme(
            st.session_state.theme_key,
            text_scale=st.session_state.a11y_text_scale,
            reduced_motion=st.session_state.a11y_reduced_motion,
        )
        st.rerun()

    st.divider()

    st.markdown(
        """
        <div class="bp-section-title">Sign in</div>
        <div class="bp-section-subtitle">Enter your credentials to continue</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("bp_login_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            placeholder="admin, manager or staff",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
        )

        submit = st.form_submit_button("Sign in", use_container_width=True)

    if submit:
        u = (username or "").strip().lower()
        user = get_user_record(u)

        if user and _pw_verify(password, user["pw_hash"]):
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Invalid username or password.")

    # Accessibility controls on login screen
    with st.expander("Accessibility settings", expanded=False):
        st.caption("These settings apply immediately.")

        new_scale = st.slider(
            "Text size",
            min_value=0.90,
            max_value=1.50,
            value=float(st.session_state.a11y_text_scale),
            step=0.05,
            format="%.2f",
        )

        new_motion = st.checkbox(
            "Reduce motion",
            value=bool(st.session_state.a11y_reduced_motion),
        )

        if (
            new_scale != st.session_state.a11y_text_scale
            or new_motion != st.session_state.a11y_reduced_motion
        ):
            st.session_state.a11y_text_scale = float(new_scale)
            st.session_state.a11y_reduced_motion = bool(new_motion)
            apply_theme(
                st.session_state.theme_key,
                text_scale=st.session_state.a11y_text_scale,
                reduced_motion=st.session_state.a11y_reduced_motion,
            )
            st.rerun()

    st.markdown(
        """
        <div class="bp-footer">
            Default accounts for first login only:<br>
            admin / admin123 &nbsp;•&nbsp;
            manager / manager123 &nbsp;•&nbsp;
            staff / staff123
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return False


def logout_button() -> None:
    if st.button("Sign out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()
