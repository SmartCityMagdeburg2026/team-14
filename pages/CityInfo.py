import base64
import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from utils.data_loader import load_kiss
from utils.constants import MD_TEAL, MD_ORANGE, PLOTLY_TEMPLATE
from utils.ui_helpers import section_header, insight_box, live_card
from utils.i18n import t

CITY_PURPLE = "#6D28D9"

# ── Icon helpers ──────────────────────────────────────────────────────────────
def _b64_img(rel_path: str, size: str = "1.6rem") -> str:
    _p = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", rel_path))
    try:
        with open(_p, "rb") as _f:
            _b = base64.b64encode(_f.read()).decode()
        ext  = os.path.splitext(_p)[1].lstrip(".")
        mime = "image/gif" if ext == "gif" else f"image/{ext}"
        return f"<img src='data:{mime};base64,{_b}' style='width:{size};height:{size};object-fit:contain;vertical-align:middle;'>"
    except Exception:
        return ""

_FIRE    = _b64_img("utils/icons/fire-brigade.png")
_POLICE  = _b64_img("utils/icons/policeman.png")
_BUS     = _b64_img("utils/icons/bus.png")
_BLDG    = _b64_img("utils/icons/historic-building.png")
_FACTORY = _b64_img("utils/icons/factory.gif", "2.2rem")

# ── Event helpers (moved from 1_Home.py) ─────────────────────────────────────
_today = date.today()

def next_occurrence(month: int, day: int) -> date:
    try:
        candidate = date(_today.year, month, day)
    except ValueError:
        candidate = date(_today.year, month, 28)
    if candidate < _today:
        try:
            candidate = date(_today.year + 1, month, day)
        except ValueError:
            candidate = date(_today.year + 1, month, 28)
    return candidate

def next_first_monday() -> date:
    d = _today.replace(day=1)
    while True:
        first_monday = d + timedelta(days=(7 - d.weekday()) % 7)
        if first_monday >= _today:
            return first_monday
        d = (d + timedelta(days=32)).replace(day=1)

# ── Page header ───────────────────────────────────────────────────────────────
st.title(t("cit.title"))
st.markdown(
    f"<p style='font-size:0.97rem;color:#64748b;max-width:700px;margin:-6px 0 20px 0;'>"
    f"{t('cit.subtitle')}"
    f"</p>",
    unsafe_allow_html=True,
)
st.caption(t("cit.source.header"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: EVENTS CALENDAR
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cit.sec.events"), color=CITY_PURPLE), unsafe_allow_html=True)

EVENTS = [
    {"name": "Stadtfest Magdeburg",      "icon": "🎉", "month": 6,    "day": 14,
     "desc": t("cit.event.stadtfest.desc")},
    {"name": "Magdeburg Marathon",        "icon": "🏃", "month": 4,    "day": 20,
     "desc": t("cit.event.marathon.desc")},
    {"name": "Kulturnacht",               "icon": "🎭", "month": 10,   "day": 12,
     "desc": t("cit.event.kulturnacht.desc")},
    {"name": "Altstadtfest",             "icon": "🏰", "month": 8,    "day": 23,
     "desc": t("cit.event.altstadt.desc")},
    {"name": "Weihnachtsmarkt",           "icon": "🎄", "month": 11,   "day": 24,
     "desc": t("cit.event.weihnacht.desc")},
    {"name": t("cit.event.council"), "icon": "🏛️", "month": None, "day": None,
     "desc": t("cit.event.council.desc")},
]

upcoming = []
for ev in EVENTS:
    ev_date = next_first_monday() if ev["month"] is None else next_occurrence(ev["month"], ev["day"])
    upcoming.append({**ev, "date": ev_date})
upcoming.sort(key=lambda x: x["date"])

ev_cols = st.columns(min(len(upcoming), 4))
for i, ev in enumerate(upcoming[:4]):
    with ev_cols[i]:
        days_away = (ev["date"] - _today).days
        if days_away == 0:
            badge, badge_color = t("day.today_badge"), "#C0392B"
        elif days_away <= 7:
            badge, badge_color = t("day.in_days", days=days_away), "#E65100"
        elif days_away <= 30:
            badge, badge_color = t("day.in_days", days=days_away), "#F59E0B"
        else:
            badge, badge_color = ev["date"].strftime("%d %b %Y"), "#64748b"

        st.markdown(f"""
<div style="background:#fff;border-radius:14px;padding:18px 16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.07);">
  <div style="font-size:1.8rem;margin-bottom:8px;">{ev["icon"]}</div>
  <div style="font-size:0.82rem;font-weight:800;color:#1A1A1A;margin-bottom:6px;
              line-height:1.3;">{ev["name"]}</div>
  <div style="display:inline-block;background:{badge_color}18;color:{badge_color};
              border-radius:8px;padding:2px 10px;font-size:0.72rem;
              font-weight:700;margin-bottom:8px;">{badge}</div>
  <div style="font-size:0.76rem;color:#64748b;line-height:1.5;">{ev["desc"]}</div>
</div>
""", unsafe_allow_html=True)

st.caption(t("cit.events.source"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: KEY ATTRACTIONS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cit.sec.attract"), color=CITY_PURPLE), unsafe_allow_html=True)

ATTRACTIONS = [
    {
        "icon": "🕌",
        "name": "Magdeburger Dom",
        "desc": t("cit.attr.dom.desc"),
        "badge": t("cit.badge.history"),
        "badge_color": "#7C3AED",
    },
    {
        "icon": "🟢",
        "name": "Grüne Zitadelle",
        "desc": t("cit.attr.zitadelle.desc"),
        "badge": t("cit.badge.arch"),
        "badge_color": "#059669",
    },
    {
        "icon": "🏛️",
        "name": "Kunstmuseum Kloster Unser Lieben Frauen",
        "desc": t("cit.attr.kunst.desc"),
        "badge": t("cit.badge.art"),
        "badge_color": "#D97706",
    },
    {
        "icon": _FACTORY,
        "name": "Technikmuseum Magdeburg",
        "desc": t("cit.attr.tech.desc"),
        "badge": t("cit.badge.museum"),
        "badge_color": "#64748b",
    },
    {
        "icon": "🌿",
        "name": "Gruson-Gewächshäuser",
        "desc": t("cit.attr.gruson.desc"),
        "badge": t("cit.badge.nature"),
        "badge_color": "#16A34A",
    },
    {
        "icon": "🌊",
        "name": "Elbe Promenade & Hubbrücke",
        "desc": t("cit.attr.elbe.desc"),
        "badge": t("cit.badge.outdoors"),
        "badge_color": "#0891B2",
    },
]

attr_row1 = st.columns(3)
attr_row2 = st.columns(3)
rows = [attr_row1, attr_row2]

for idx, attr in enumerate(ATTRACTIONS):
    row_i   = idx // 3
    col_i   = idx % 3
    with rows[row_i][col_i]:
        st.markdown(f"""
<div style="background:#fff;border-radius:14px;padding:20px 18px;
            box-shadow:0 2px 14px rgba(0,0,0,0.07);margin-bottom:16px;
            border-top:4px solid {attr['badge_color']};">
  <div style="font-size:2rem;margin-bottom:10px;">{attr["icon"]}</div>
  <div style="display:inline-block;background:{attr['badge_color']}18;color:{attr['badge_color']};
              border-radius:8px;padding:2px 10px;font-size:0.68rem;
              font-weight:700;margin-bottom:8px;">{attr["badge"]}</div>
  <div style="font-size:0.88rem;font-weight:800;color:#1A1A1A;margin-bottom:6px;
              line-height:1.3;">{attr["name"]}</div>
  <div style="font-size:0.78rem;color:#64748b;line-height:1.55;">{attr["desc"]}</div>
</div>
""", unsafe_allow_html=True)

st.caption(t("cit.visitor_tips"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: CULTURAL VENUES — VISITOR TRENDS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cit.sec.venues"), color=CITY_PURPLE), unsafe_allow_html=True)

cult_l, cult_r = st.columns(2)

with cult_l:
    st.caption(t("cit.cap.library"))
    try:
        df_lib = load_kiss("bildung-und-kultur/monatliche-besuchszahlen-bestaende-und-entleihungen.json")
        lib_col = next((c for c in df_lib.columns if "besucher" in c.lower()), None)
        if lib_col:
            df_lib[lib_col] = pd.to_numeric(df_lib[lib_col], errors="coerce")
            lib_annual = df_lib.groupby("Jahr")[lib_col].sum().reset_index()
            lib_annual = lib_annual[lib_annual[lib_col] > 0]

            fig_lib = go.Figure(go.Bar(
                x=lib_annual["Jahr"], y=lib_annual[lib_col],
                marker_color=CITY_PURPLE, opacity=0.8,
                hovertemplate=f"%{{x}}: %{{y:,}} {t('cit.hover.visitors')}<extra></extra>",
            ))
            peak_lib = lib_annual.loc[lib_annual[lib_col].idxmax()]
            fig_lib.add_annotation(
                x=peak_lib["Jahr"], y=peak_lib[lib_col],
                text=f"{t('cit.peak')}: {int(peak_lib[lib_col]):,}".replace(",", "."),
                showarrow=True, arrowhead=2, ax=30, ay=-30,
            )
            fig_lib.update_layout(
                template=PLOTLY_TEMPLATE,
                yaxis_title=t("cit.axis.visitors"), yaxis=dict(tickformat=",d"),
                margin=dict(l=50, r=10, t=20, b=40), height=280,
            )
            st.plotly_chart(fig_lib, use_container_width=True)
        else:
            st.info(t("cit.info.library_col"))
    except Exception as e:
        st.info(t("cit.info.library", error=e))

with cult_r:
    st.caption(t("cit.cap.gruson"))
    try:
        df_gr = load_kiss("bildung-und-kultur/besuche-gruson-gewaechshaeuser.json")
        gr_col = next((c for c in df_gr.columns if "besucher" in c.lower()), None)
        if gr_col:
            df_gr[gr_col] = pd.to_numeric(df_gr[gr_col], errors="coerce")
            gr_annual = df_gr.groupby("Jahr")[gr_col].sum().reset_index()
            gr_annual = gr_annual[gr_annual[gr_col] > 0]

            fig_gr = go.Figure(go.Bar(
                x=gr_annual["Jahr"], y=gr_annual[gr_col],
                marker_color="#16A34A", opacity=0.8,
                hovertemplate=f"%{{x}}: %{{y:,}} {t('cit.hover.visitors')}<extra></extra>",
            ))
            fig_gr.update_layout(
                template=PLOTLY_TEMPLATE,
                yaxis_title=t("cit.axis.visitors"), yaxis=dict(tickformat=",d"),
                margin=dict(l=50, r=10, t=20, b=40), height=280,
            )
            st.plotly_chart(fig_gr, use_container_width=True)
        else:
            st.info(t("cit.info.green_col"))
    except Exception as e:
        st.info(t("cit.info.green", error=e))

st.markdown(insight_box(
    t("cit.insight.venues")
), unsafe_allow_html=True)
st.caption(t("cit.source.venues"))

