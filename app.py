import base64
import os
import streamlit as st
from utils.ui_helpers import GLOBAL_CSS
from utils.i18n import t

st.set_page_config(
    page_title="Smart City Magdeburg",
    page_icon="utils/Wappen_Magdeburg.svg.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state["lang"] = "de"
if "_lang_radio" in st.session_state:
    st.session_state["lang"] = st.session_state["_lang_radio"].lower()

pages = {
    "Dashboard": [
        st.Page("pages/1_Home.py",
                title=t("nav.home"),             icon="🏠"),
        st.Page("pages/CityNav.py",
                title=t("navi.title"),           icon="🗺️",  url_path="navigation"),
        st.Page("pages/2_Climate.py",
                title=t("cli.title"),            icon="🌡️",  url_path="climate"),
        st.Page("pages/3_Population_Housing.py",
                title=t("pop.title"),            icon="🏘️",  url_path="population"),
        st.Page("pages/CityInfo.py",
                title=t("cit.title"),            icon="🏛️",  url_path="city"),
    ]
}

pg = st.navigation(pages, position="hidden")

# ── Load GIF icons as base64 data URIs ────────────────────────────────────────
def _nav_src(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "utils", "icons", filename)
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:image/gif;base64,{b64}"
    except Exception:
        return ""

_GIFS = [
    _nav_src("home.gif"),
    _nav_src("navigation.gif"),
    _nav_src("climate.gif"),
    _nav_src("population.gif"),
    _nav_src("city.gif"),
]

_NAV = [
    ("pages/1_Home.py",                t("nav.home"),       "",           "#007A6E"),
    ("pages/CityNav.py",               t("nav.navigation"), "navigation", "#00897B"),
    ("pages/2_Climate.py",             t("nav.climate"),    "climate",    "#1565C0"),
    ("pages/3_Population_Housing.py",  t("nav.population"), "population", "#6A1B9A"),
    ("pages/CityInfo.py",              t("nav.city"),       "city",       "#6D28D9"),
]

current = getattr(pg, "url_path", None) or ""

# ── Nav bar ───────────────────────────────────────────────────────────────────
brand_col, c1, c2, c3, c4, c5, lang_col = st.columns([2, 1, 1, 1, 1, 1, 0.8])
nav_cols = [c1, c2, c3, c4, c5]

with brand_col:
    st.markdown(
        '<div style="padding:8px 4px 4px;">'
        '<div style="font-size:1.05rem;font-weight:900;color:#007A6E;letter-spacing:-0.03em;line-height:1.1;">Magdeburg</div>'
        f'<div style="font-size:0.6rem;color:#aaa;text-transform:uppercase;letter-spacing:0.13em;font-weight:600;">{t("nav.brand_sub")}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

with lang_col:
    _chosen = st.radio(
        "",
        ["DE", "EN"],
        index=0 if st.session_state["lang"] == "de" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="_lang_radio",
    )
    st.session_state["lang"] = _chosen.lower()

for col, (page_file, label, url_path, color), gif_src in zip(nav_cols, _NAV, _GIFS):
    active = (current == url_path)
    with col:
        if gif_src:
            st.markdown(
                f'<div style="display:flex;justify-content:center;padding-top:8px;pointer-events:none;">'
                f'<img src="{gif_src}" style="width:1.4rem;height:1.4rem;object-fit:contain;"></div>',
                unsafe_allow_html=True,
            )
        st.page_link(page_file, label=label, use_container_width=True)
        bar_color = color if active else "transparent"
        st.markdown(
            f'<div style="height:3px;background:{bar_color};border-radius:1px;margin-top:-6px;"></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<hr style="margin:0 0 10px 0;border-top:2px solid #eef0f2;border-bottom:0;border-left:0;border-right:0;">',
    unsafe_allow_html=True,
)

pg.run()
