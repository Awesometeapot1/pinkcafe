import streamlit as st

# ----------------------------
# Theme registry (EDIT THIS to add themes)
# ----------------------------
THEMES = {
    # Your current look, but parameterised
    "blackpink_pro": {
        "label": "BLACKPINK ",
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
            # gradient accent strength
            "--bp-accent-a": "rgba(255,105,180,0.10)",
            "--bp-accent-b": "rgba(255,45,149,0.08)",
            "--bp-grad-bottom": "#000000",
            # button text (important for contrast)
            "--bp-button-text": "#0A0A0F",
            "--bp-input-bg": "rgba(10,10,15,0.72)",
        },
    },

    # Higher accessibility contrast, still dark + pink accents (improved)
"high_contrast": {
    "label": "High Contrast Dark (BP Pro)",
    "mode": "dark",
    "vars": {
        # Backgrounds: avoid pure black to reduce eye strain
        "--bp-bg": "#0B0B10",
        "--bp-bg-2": "#11111A",
        "--bp-grad-bottom": "#07070B",

        # Surfaces: slightly lighter than bg so cards separate clearly
        "--bp-surface": "rgba(255,255,255,0.06)",
        "--bp-surface-2": "rgba(255,255,255,0.09)",

        # Borders: mostly neutral, pink used as accent
        "--bp-border": "rgba(255,255,255,0.14)",
        "--bp-border-strong": "rgba(255,45,149,0.55)",

        # Text: crisp white + sensible hierarchy
        "--bp-text": "#F6F7FB",
        "--bp-text-dim": "rgba(246,247,251,0.86)",
        "--bp-text-mute": "rgba(246,247,251,0.68)",

        # Accents: slightly less neon, more “premium”
        "--bp-pink": "#FF2D95",
        "--bp-pink-2": "#FF6BBE",

        # Shadows: cleaner, less muddy
        "--bp-shadow": "0 14px 40px rgba(0,0,0,0.65)",

        # Radii
        "--bp-radius": "18px",
        "--bp-radius-sm": "12px",

        # Accent fills for subtle highlights / chips
        "--bp-accent-a": "rgba(255,45,149,0.16)",
        "--bp-accent-b": "rgba(255,107,190,0.12)",

        # Inputs: darker than surface so they look “editable”
        "--bp-input-bg": "rgba(12,12,18,0.90)",

        # Button text: on pink buttons use near-black for contrast
        "--bp-button-text": "#0B0B10",
    },
},

# Light theme for report-style viewing (improved)
"light_clean": {
    "label": "Light (Clean BP)",
    "mode": "light",
    "vars": {
        # Backgrounds: slightly tinted so it doesn't feel sterile
        "--bp-bg": "#FFFFFF",
        "--bp-bg-2": "#F7F7FB",
        "--bp-grad-bottom": "#FFFFFF",

        # Surfaces: soft elevation
        "--bp-surface": "rgba(11,11,16,0.04)",
        "--bp-surface-2": "rgba(11,11,16,0.06)",

        # Borders: neutral base, pink accent
        "--bp-border": "rgba(11,11,16,0.12)",
        "--bp-border-strong": "rgba(255,45,149,0.40)",

        # Text: deep neutral (not pure black)
        "--bp-text": "#0B0B10",
        "--bp-text-dim": "rgba(11,11,16,0.82)",
        "--bp-text-mute": "rgba(11,11,16,0.62)",

        # Accents: consistent with dark theme
        "--bp-pink": "#FF2D95",
        "--bp-pink-2": "#FF6BBE",

        # Shadows: subtle but present
        "--bp-shadow": "0 12px 30px rgba(11,11,16,0.10)",

        # Radii
        "--bp-radius": "18px",
        "--bp-radius-sm": "12px",

        # Accent fills (very light)
        "--bp-accent-a": "rgba(255,45,149,0.10)",
        "--bp-accent-b": "rgba(255,107,190,0.08)",

        # Inputs: white but slightly separated
        "--bp-input-bg": "rgba(255,255,255,0.96)",

        # Button text: on pink buttons, white reads cleanest in light theme
        "--bp-button-text": "#FFFFFF",
    },
}
}

# ----------------------------
# Helpers
# ----------------------------
def theme_options():
    """Returns list of (key, label) in a stable order."""
    keys = list(THEMES.keys())
    return [(k, THEMES[k]["label"]) for k in keys]


def _vars_to_css(vars_dict: dict) -> str:
    # Convert {"--x":"y"} into CSS lines
    return "\n".join([f"  {k}: {v};" for k, v in vars_dict.items()])


def inject_header_gap_fix() -> None:
    """
    Removes Streamlit's header gap/white bar and forces background to the top.
    Keep this separate from themes (it is structural).
    """
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
    """Hides Streamlit's auto page dropdown/list."""
    st.markdown(
        """
        <style>
          [data-testid="stSidebarNav"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(theme_key: str) -> None:
    """
    Applies a theme from THEMES by injecting variable-driven CSS.
    Add new themes by adding an entry in THEMES only.
    """
    theme = THEMES.get(theme_key) or THEMES["blackpink_pro"]
    css_vars = _vars_to_css(theme["vars"])

    # Pick sensible background gradients per mode
    is_light = theme.get("mode") == "light"
    app_bg = "var(--bp-bg)" if is_light else "var(--bp-bg)"

    st.markdown(
        f"""
        <style>
        :root {{
{css_vars}
        }}

        /* App background */
        [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
            background: {app_bg} !important;
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
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
        }}

        .block-container {{ padding-top: 1.1rem; padding-bottom: 2.6rem; }}

        h1, h2, h3, h4 {{
            color: var(--bp-pink) !important;
            letter-spacing: 0.2px;
        }}
        p, li, label, .stMarkdown, .stCaption {{
            color: var(--bp-text-dim) !important;
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

        /* Card components */
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
            font-size: 11px;
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
            color: var(--bp-text) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: var(--bp-radius-sm) !important;
        }}

        div[role="radiogroup"] label, .stCheckbox label {{
            color: var(--bp-text-dim) !important;
        }}

        /* Alerts */
        div[data-testid="stAlert"] {{
            border-radius: var(--bp-radius) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            background: rgba(10,10,15,0.65) !important;
            color: var(--bp-text) !important;
        }}

        /* Dataframes */
        .stDataFrame, div[data-testid="stDataFrame"] {{
            border-radius: var(--bp-radius) !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            overflow: hidden;
        }}
        div[data-testid="stDataFrame"] * {{
            color: var(--bp-text) !important;
        }}
        div[data-testid="stDataFrame"] thead tr th {{
            background: rgba(255,105,180,0.10) !important;
            border-bottom: 1px solid var(--bp-border) !important;
        }}
        div[data-testid="stDataFrame"] tbody tr:hover td {{
            background: rgba(255,105,180,0.06) !important;
        }}

        a, a:visited {{ color: rgba(255,182,217,0.95) !important; }}
        a:hover {{ color: var(--bp-pink) !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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