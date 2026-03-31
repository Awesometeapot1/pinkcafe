import streamlit as st

# ----------------------------
# Theme registry
# ----------------------------
THEMES = {
    "blackpink_pro": {
        "label": "BLACKPINK",
        "mode": "dark",
        "vars": {
            "--bp-bg": "#06060A",
            "--bp-bg-2": "#0A0A10",
            "--bp-surface": "rgba(255,255,255,0.06)",
            "--bp-surface-2": "rgba(255,255,255,0.09)",
            "--bp-border": "rgba(255,105,180,0.22)",
            "--bp-border-strong": "rgba(255,105,180,0.40)",
            "--bp-text": "#F6F1F7",
            "--bp-text-dim": "rgba(246,241,247,0.78)",
            "--bp-text-mute": "rgba(246,241,247,0.62)",
            "--bp-pink": "#ff69b4",
            "--bp-pink-2": "#ff2d95",
            "--bp-shadow": "0 14px 44px rgba(0,0,0,0.62)",
            "--bp-radius": "18px",
            "--bp-radius-sm": "12px",
            "--bp-accent-a": "rgba(255,105,180,0.10)",
            "--bp-accent-b": "rgba(255,45,149,0.08)",
            "--bp-grad-bottom": "#000000",
            "--bp-button-text": "#0A0A0F",
            "--bp-input-bg": "rgba(10,10,15,0.72)",
            "--bp-input-text": "#F6F1F7",
            "--bp-input-placeholder": "rgba(246,241,247,0.50)",
        },
    },
    "high_contrast": {
        "label": "High Contrast Dark",
        "mode": "dark",
        "vars": {
            "--bp-bg": "#0B0B10",
            "--bp-bg-2": "#11111A",
            "--bp-grad-bottom": "#07070B",
            "--bp-surface": "rgba(255,255,255,0.06)",
            "--bp-surface-2": "rgba(255,255,255,0.09)",
            "--bp-border": "rgba(255,255,255,0.14)",
            "--bp-border-strong": "rgba(255,45,149,0.55)",
            "--bp-text": "#F6F7FB",
            "--bp-text-dim": "rgba(246,247,251,0.86)",
            "--bp-text-mute": "rgba(246,247,251,0.68)",
            "--bp-pink": "#FF2D95",
            "--bp-pink-2": "#FF6BBE",
            "--bp-shadow": "0 14px 40px rgba(0,0,0,0.65)",
            "--bp-radius": "18px",
            "--bp-radius-sm": "12px",
            "--bp-accent-a": "rgba(255,45,149,0.16)",
            "--bp-accent-b": "rgba(255,107,190,0.12)",
            "--bp-input-bg": "rgba(12,12,18,0.90)",
            "--bp-input-text": "#F6F7FB",
            "--bp-input-placeholder": "rgba(246,247,251,0.55)",
            "--bp-button-text": "#0B0B10",
        },
    },
    "light_clean": {
        "label": "Light",
        "mode": "light",
        "vars": {
            "--bp-bg": "#FFFFFF",
            "--bp-bg-2": "#F7F7FB",
            "--bp-grad-bottom": "#FFFFFF",
            "--bp-surface": "rgba(11,11,16,0.04)",
            "--bp-surface-2": "rgba(11,11,16,0.06)",
            "--bp-border": "rgba(11,11,16,0.12)",
            "--bp-border-strong": "rgba(255,45,149,0.40)",
            "--bp-text": "#0B0B10",
            "--bp-text-dim": "rgba(11,11,16,0.82)",
            "--bp-text-mute": "rgba(11,11,16,0.62)",
            "--bp-pink": "#FF2D95",
            "--bp-pink-2": "#FF6BBE",
            "--bp-shadow": "0 12px 30px rgba(11,11,16,0.10)",
            "--bp-radius": "18px",
            "--bp-radius-sm": "12px",
            "--bp-accent-a": "rgba(255,45,149,0.10)",
            "--bp-accent-b": "rgba(255,107,190,0.08)",
            "--bp-input-bg": "rgba(255,255,255,0.96)",
            "--bp-input-text": "#0B0B10",
            "--bp-input-placeholder": "rgba(11,11,16,0.42)",
            "--bp-button-text": "#FFFFFF",
        },
    },
}


# ----------------------------
# Helpers
# ----------------------------
def theme_options():
    keys = list(THEMES.keys())
    return [(k, THEMES[k]["label"]) for k in keys]


def _vars_to_css(vars_dict: dict) -> str:
    return "\n".join([f"  {k}: {v};" for k, v in vars_dict.items()])


def inject_header_gap_fix() -> None:
    st.markdown(
        """
        <style>
          [data-testid="stHeader"] {
            background: rgba(0,0,0,0) !important;
            height: 0px !important;
          }
          .block-container {
            padding-top: 0rem !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hide_native_multipage_nav() -> None:
    st.markdown(
        """
        <style>
          [data-testid="stSidebarNav"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(
    theme_key: str,
    text_scale: float = 1.0,
    reduced_motion: bool = False,
) -> None:
    theme = THEMES.get(theme_key) or THEMES["blackpink_pro"]
    css_vars = _vars_to_css(theme["vars"])

    try:
        text_scale = float(text_scale)
    except Exception:
        text_scale = 1.0
    text_scale = max(0.85, min(1.60, text_scale))

    motion_css = ""
    if reduced_motion:
        motion_css = """
    * {
        transition: none !important;
        animation: none !important;
        scroll-behavior: auto !important;
    }

    .stButton > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover,
    div[data-testid="stForm"] button:hover {
        transform: none !important;
        filter: none !important;
    }
    """

    st.markdown(
        f"""
        <style>
        :root {{
{css_vars}
          --bp-text-scale: {text_scale};
        }}

        /* App background */
        [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
            background: var(--bp-bg) !important;
        }}

        .stApp {{
            background:
                radial-gradient(1000px 700px at 20% 0%, var(--bp-accent-a) 0%, rgba(0,0,0,0) 62%),
                radial-gradient(1000px 700px at 80% 0%, var(--bp-accent-b) 0%, rgba(0,0,0,0) 62%),
                linear-gradient(180deg, var(--bp-bg) 0%, var(--bp-grad-bottom) 72%, var(--bp-grad-bottom) 100%) !important;
            color: var(--bp-text) !important;
        }}

        html, body, [class*="css"] {{
            color: var(--bp-text) !important;
            font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial,
                         "Apple Color Emoji","Segoe UI Emoji" !important;
            font-size: calc(16px * var(--bp-text-scale)) !important;
            line-height: 1.45 !important;
        }}

        h1 {{ font-size: calc(2.00rem * var(--bp-text-scale)) !important; }}
        h2 {{ font-size: calc(1.50rem * var(--bp-text-scale)) !important; }}
        h3 {{ font-size: calc(1.20rem * var(--bp-text-scale)) !important; }}

        .block-container {{
            padding-top: 1.1rem;
            padding-bottom: 2.6rem;
        }}

        h1, h2, h3, h4 {{
            color: var(--bp-pink) !important;
            letter-spacing: 0.2px;
        }}

        p, li, label, .stMarkdown, .stCaption {{
            color: var(--bp-text-dim) !important;
        }}

        /* Strong keyboard focus */
        :focus {{ outline: none; }}
        :focus-visible {{
            outline: 3px solid var(--bp-pink-2) !important;
            outline-offset: 2px !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--bp-bg-2) 0%, var(--bp-bg) 100%) !important;
            border-right: 1px solid var(--bp-border) !important;
        }}

        section[data-testid="stSidebar"] * {{
            color: var(--bp-text) !important;
        }}

        section[data-testid="stSidebar"] .stRadio label {{
            color: var(--bp-text-dim) !important;
        }}

        /* Cards */
        .bp-card {{
            background: linear-gradient(180deg, var(--bp-surface-2) 0%, var(--bp-surface) 100%) !important;
            border: 1px solid var(--bp-border) !important;
            border-radius: var(--bp-radius) !important;
            padding: 22px !important;
            box-shadow: var(--bp-shadow) !important;
            backdrop-filter: blur(10px);
        }}

        .bp-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid var(--bp-border-strong);
            background: linear-gradient(180deg, rgba(255,105,180,0.14) 0%, rgba(0,0,0,0.10) 100%);
            color: var(--bp-text);
            font-size: calc(11px * var(--bp-text-scale));
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}

        .bp-divider {{
            height: 1px;
            background: rgba(255,105,180,0.18);
            margin: 14px 0;
        }}

        /* Buttons */
        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        div[data-testid="stForm"] button {{
            background: linear-gradient(90deg, var(--bp-pink) 0%, var(--bp-pink-2) 100%) !important;
            color: var(--bp-button-text) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 14px !important;
            padding: 0.62rem 1.05rem !important;
            font-weight: 900 !important;
            letter-spacing: 0.2px !important;
            box-shadow: 0 10px 26px rgba(255,45,149,0.14) !important;
            transition: transform 120ms ease, filter 120ms ease !important;
        }}

        .stButton > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        div[data-testid="stForm"] button:hover {{
            filter: brightness(1.05) !important;
            transform: translateY(-1px) !important;
        }}

        /* Inputs */
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {{
            background: var(--bp-input-bg) !important;
            color: var(--bp-input-text) !important;
            -webkit-text-fill-color: var(--bp-input-text) !important;
            caret-color: var(--bp-input-text) !important;
            border: 1px solid var(--bp-border) !important;
            border-radius: var(--bp-radius-sm) !important;
            font-size: calc(1rem * var(--bp-text-scale)) !important;
        }}

        /* placeholder */
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        .stDateInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: var(--bp-input-placeholder) !important;
            -webkit-text-fill-color: var(--bp-input-placeholder) !important;
        }}

        /* labels */
        div[role="radiogroup"] label,
        .stCheckbox label {{
            color: var(--bp-text-dim) !important;
            font-size: calc(1rem * var(--bp-text-scale)) !important;
        }}

        /* Alerts */
        div[data-testid="stAlert"] {{
            border-radius: var(--bp-radius) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            background: rgba(10,10,15,0.65) !important;
            color: var(--bp-text) !important;
        }}

        /* Expanders */
        div[data-testid="stExpander"] {{
            background: transparent !important;
            border: none !important;
        }}

        div[data-testid="stExpander"] .streamlit-expanderHeader,
        div[data-testid="stExpander"] button[kind="header"] {{
            background: var(--bp-surface) !important;
            border: 1px solid var(--bp-border-strong) !important;
            border-radius: var(--bp-radius-sm) !important;
            color: var(--bp-text) !important;
        }}

        div[data-testid="stExpander"] .streamlit-expanderHeader:hover,
        div[data-testid="stExpander"] button[kind="header"]:hover {{
            background: var(--bp-surface-2) !important;
            border-color: var(--bp-pink) !important;
        }}

        div[data-testid="stExpander"] .streamlit-expanderContent,
        div[data-testid="stExpander"] details > div:not(summary),
        div[data-testid="stExpander"] details[open] > div {{
            background: var(--bp-surface) !important;
            border: 1px solid var(--bp-border) !important;
            border-top: none !important;
            border-radius: 0 0 var(--bp-radius-sm) var(--bp-radius-sm) !important;
            padding: 16px !important;
        }}

        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] li,
        div[data-testid="stExpander"] span,
        div[data-testid="stExpander"] div,
        div[data-testid="stExpander"] label,
        div[data-testid="stExpander"] .stMarkdown {{
            color: var(--bp-text-dim) !important;
            background: transparent !important;
        }}

        div[data-testid="stExpander"] details {{
            background: transparent !important;
        }}

        div[data-testid="stExpander"] summary {{
            background: var(--bp-surface) !important;
        }}

        /* Dataframes */
        .stDataFrame,
        div[data-testid="stDataFrame"] {{
            border-radius: var(--bp-radius) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            overflow: hidden;
        }}

        div[data-testid="stDataFrame"] * {{
            color: var(--bp-text) !important;
            font-size: calc(0.95rem * var(--bp-text-scale)) !important;
        }}

        div[data-testid="stDataFrame"] thead tr th {{
            background: rgba(255,105,180,0.10) !important;
            border-bottom: 1px solid var(--bp-border) !important;
        }}

        div[data-testid="stDataFrame"] tbody tr:hover td {{
            background: rgba(255,105,180,0.06) !important;
        }}

        /* Links */
        a, a:visited {{
            color: rgba(255,182,217,0.95) !important;
        }}

        a:hover {{
            color: var(--bp-pink) !important;
        }}

        /* Slider */
        [data-testid="stSlider"] div[data-baseweb="slider"] {{
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
        }}

        [data-testid="stSlider"] div[data-baseweb="slider"] + div,
        [data-testid="stSlider"] [data-testid="stTickBar"],
        [data-testid="stSlider"] [data-testid="stTickBarMin"],
        [data-testid="stSlider"] [data-testid="stTickBarMax"] {{
            display: none !important;
        }}

        [data-testid="stSlider"] div[data-baseweb="slider"] > div {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        [data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child {{
            height: 4px !important;
            border-radius: 999px !important;
            background: rgba(255,255,255,0.14) !important;
            overflow: visible !important;
        }}

        [data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child > div:first-child {{
            height: 4px !important;
            border-radius: 999px !important;
            background: #ff63b8 !important;
        }}

        [data-testid="stSlider"] [role="slider"] {{
            width: 20px !important;
            height: 20px !important;
            border-radius: 50% !important;
            background: #ff63b8 !important;
            border: 3px solid rgba(255, 192, 223, 0.95) !important;
            box-shadow:
                0 0 0 5px rgba(255,99,184,0.18),
                0 0 18px rgba(255,99,184,0.42) !important;
            top: -2px !important;
        }}

        [data-testid="stSlider"] [role="slider"]:focus {{
            outline: none !important;
            box-shadow:
                0 0 0 6px rgba(255,99,184,0.22),
                0 0 20px rgba(255,99,184,0.48) !important;
        }}

        [data-testid="stSlider"] [data-testid="stSliderThumbValue"] {{
            color: #ffffff !important;
            font-size: 0.74rem !important;
            font-weight: 700 !important;
            background: transparent !important;
        }}

        [data-testid="stSlider"] label p {{
            font-size: 0.80rem !important;
            color: var(--bp-text) !important;
        }}

        /* Respect reduced motion preference + toggle */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                transition: none !important;
                animation: none !important;
                scroll-behavior: auto !important;
            }}
        }}

        /* Hide "Press Enter to submit form" GLOBALLY */
        [data-testid="InputInstructions"],
        div[class*="InputInstructions"],
        form [data-testid="InputInstructions"] {{
            display: none !important;
            visibility: hidden !important;
        }}

        {motion_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_accessibility_controls(prefix: str = "a11y") -> None:
    with st.expander("Accessibility settings", expanded=False):
        st.caption("These settings apply immediately.")

        new_scale = st.slider(
            "Text size",
            min_value=0.90,
            max_value=1.50,
            value=float(st.session_state.get("a11y_text_scale", 1.0)),
            step=0.05,
            format="%.2f",
            key=f"{prefix}_text_scale",
        )

        new_motion = st.checkbox(
            "Reduce motion",
            value=bool(st.session_state.get("a11y_reduced_motion", False)),
            key=f"{prefix}_reduce_motion",
        )

        if (
            new_scale != st.session_state.a11y_text_scale
            or new_motion != st.session_state.a11y_reduced_motion
        ):
            st.session_state.a11y_text_scale = float(new_scale)
            st.session_state.a11y_reduced_motion = bool(new_motion)
            st.rerun()


def render_pink_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="bp-card">
            <div class="bp-badge">Bristol Pink Café</div>
            <h1 style="margin:0; line-height:1.1;">{title}</h1>
            <p style="margin:8px 0 0 0; color: var(--bp-text-mute);">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
