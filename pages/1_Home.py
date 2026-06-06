import base64
import os
import streamlit as st
import streamlit.components.v1 as components
import folium
import pandas as pd
from datetime import date, timedelta

from utils.live_api import (
    fetch_weather, fetch_air_quality,
    fetch_weather_forecast, fetch_city_news,
    fetch_elbe_level, fetch_uv_index,
)
from utils.data_loader import load_kiss
from utils.ui_helpers import section_header, topic_card
from utils.i18n import t

# ── Icon assets ───────────────────────────────────────────────────────────────
def _b64_img(rel_path: str, size: str = "2rem") -> str:
    _p = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", rel_path))
    try:
        with open(_p, "rb") as _f:
            _b = base64.b64encode(_f.read()).decode()
        ext = os.path.splitext(_p)[1].lstrip(".")
        mime = "image/gif" if ext == "gif" else f"image/{ext}"
        return f"<img src='data:{mime};base64,{_b}' style='width:{size};height:{size};object-fit:contain;'>"
    except Exception:
        return "🌡️"

TEMP_ICON   = _b64_img("utils/icons/temperature.gif",    "3rem")
WIND_ICON   = _b64_img("utils/icons/wind.gif",         "3rem")
AIR_ICON    = _b64_img("utils/icons/airquality.gif",   "3rem")
ALERT_ICON  = _b64_img("utils/icons/alert.gif",        "2.2rem")
_FIRE_ICON  = _b64_img("utils/icons/fire-brigade.png", "1.5rem")
_POLICE_ICON= _b64_img("utils/icons/policeman.png",    "1.5rem")
_BUS_ICON   = _b64_img("utils/icons/bus.png",          "1.5rem")
_BLDG_ICON  = _b64_img("utils/icons/historic-building.png", "1.5rem")

# ── Helpers ───────────────────────────────────────────────────────────────────

COND_ICON = {
    "dry": "☀️", "rain": "🌧️", "snow": "❄️", "sleet": "🌨️",
    "hail": "⛈️", "thunderstorm": "⛈️", "fog": "🌫️",
    "wind": "💨", "cloudy": "⛅", "partly-cloudy": "🌤️",
}

def cond_icon(cond: str) -> str:
    cond = (cond or "dry").lower()
    for key in COND_ICON:
        if key in cond:
            return COND_ICON[key]
    return "🌤️"

def day_label(date_str: str) -> str:
    try:
        d = date.fromisoformat(date_str[:10])
        if d == date.today():
            return t("day.today")
        if d == date.today() + timedelta(days=1):
            return t("day.tomorrow")
        return d.strftime("%A")
    except Exception:
        return date_str[:10]

# ── Fetch live data (cached) ──────────────────────────────────────────────────
weather    = fetch_weather()
pm25       = fetch_air_quality()
forecast   = fetch_weather_forecast()
news_items = fetch_city_news()
elbe       = fetch_elbe_level()
uv_index   = fetch_uv_index()

temp      = weather.get("temperature")       if weather else None
wind_spd  = weather.get("wind_speed")        if weather else None
cond      = weather.get("condition")         if weather else None
humidity  = weather.get("relative_humidity") if weather else None
elbe_val  = elbe.get("value")               if elbe    else None

# ── Page header with fading background ───────────────────────────────────────
_img_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "utils", "mag.jpeg")
)
try:
    with open(_img_path, "rb") as _f:
        _img_b64 = base64.b64encode(_f.read()).decode()
    _img_css = f"url('data:image/jpeg;base64,{_img_b64}')"
except Exception:
    _img_css = "none"

st.markdown(f"""
<div style="
  position:relative;
  border-radius:16px;
  overflow:hidden;
  margin-bottom:24px;
  min-height:160px;
  background-image:
    linear-gradient(to right, #ffffff 38%, rgba(255,255,255,0.55) 68%, rgba(255,255,255,0) 100%),
    {_img_css};
  background-size: cover;
  background-position: center right;
  background-repeat: no-repeat;
">
  <div style="position:relative;padding:38px 40px 32px 36px;max-width:560px;">
    <div style="font-size:2rem;font-weight:900;color:#1A1A1A;line-height:1.15;">
      {t("home.title")}
    </div>
    <div style="font-size:1rem;color:#475569;margin-top:8px;line-height:1.55;">
      {t("home.subtitle")}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: ACTIVE ALERTS
# ─────────────────────────────────────────────────────────────────────────────
alerts = []

if pm25 is not None and pm25 > 35:
    alerts.append((f"😷 {t('home.alert.air.title')}",
                   t("home.alert.air.msg", pm25=pm25), "warning"))

if wind_spd is not None and wind_spd > 60:
    alerts.append((f"💨 {t('home.alert.wind.title')}",
                   t("home.alert.wind.msg", wind=wind_spd), "warning"))

if alerts:
    for level_label, msg, alert_type in alerts:
        bg    = "#FFF1F2" if alert_type == "error" else "#FFFBEB"
        border = "#EF4444" if alert_type == "error" else "#F59E0B"
        st.markdown(f"""
<div style="background:{bg};border-left:4px solid {border};border-radius:0 12px 12px 0;
            padding:14px 18px;margin-bottom:10px;
            display:flex;align-items:center;gap:14px;">
  <div style="flex-shrink:0;">{ALERT_ICON}</div>
  <div>
    <div style="font-size:0.82rem;font-weight:800;color:#1A1A1A;margin-bottom:3px;">{level_label}</div>
    <div style="font-size:0.8rem;color:#374151;line-height:1.5;">{msg}</div>
  </div>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown(f"""
<div style="background:#F0FDF4;border-left:4px solid #22C55E;border-radius:0 12px 12px 0;
            padding:14px 18px;margin-bottom:10px;
            display:flex;align-items:center;gap:14px;">
  <div style="flex-shrink:0;">{ALERT_ICON}</div>
  <div style="font-size:0.82rem;font-weight:800;color:#15803D;">
    {t("home.alert.clear")}
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 + 3: WEATHER + LIVE PULSE (side by side)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("home.sec.weather")), unsafe_allow_html=True)

weather_col, pulse_col = st.columns([3, 2], gap="large")

with weather_col:
    temp_str  = f"{temp:.0f}°C"         if temp      is not None else "—"
    wind_str  = f"{wind_spd:.0f} km/h"  if wind_spd  is not None else "—"
    hum_str   = f"{humidity:.0f}%"       if humidity  is not None else "—"
    icon_main = cond_icon(cond)
    cond_str  = (cond or "").replace("-", " ").title() if cond else "—"

    st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f4c75 0%,#1b6ca8 60%,#1e8bc3 100%);
            border-radius:20px;padding:28px 32px;color:#fff;">
  <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
              letter-spacing:0.14em;opacity:0.7;margin-bottom:6px;">{t("home.weather.today")}</div>
  <div style="display:flex;align-items:center;gap:16px;">
    <div style="font-size:4rem;line-height:1;">{icon_main}</div>
    <div>
      <div style="font-size:3.2rem;font-weight:900;line-height:1;">{temp_str}</div>
      <div style="font-size:1rem;opacity:0.85;margin-top:4px;">{cond_str}</div>
    </div>
  </div>
  <div style="display:flex;gap:28px;margin-top:20px;font-size:0.88rem;opacity:0.85;">
    <span>💨 {t("home.weather.wind")} &nbsp;<strong>{wind_str}</strong></span>
    <span>💧 {t("home.weather.humidity")} &nbsp;<strong>{hum_str}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

    if forecast:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        fc_cols = st.columns(min(len(forecast), 4))
        for i, fc in enumerate(forecast[:4]):
            with fc_cols[i]:
                hi  = f"{fc['temp_max']:.0f}°" if fc.get("temp_max") is not None else "—"
                lo  = f"{fc['temp_min']:.0f}°" if fc.get("temp_min") is not None else "—"
                ico = cond_icon(fc.get("condition"))
                lbl = day_label(fc["date"])
                st.markdown(f"""
<div style="background:#f8fafc;border-radius:12px;padding:12px 8px;text-align:center;">
  <div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;
              letter-spacing:0.08em;">{lbl}</div>
  <div style="font-size:1.6rem;margin:6px 0;">{ico}</div>
  <div style="font-size:0.9rem;font-weight:800;color:#1A1A1A;">{hi}</div>
  <div style="font-size:0.78rem;color:#94a3b8;">{lo}</div>
</div>
""", unsafe_allow_html=True)

    st.caption(t("home.weather.source"))

with pulse_col:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    uv_color = ("#007A6E" if uv_index is None or uv_index <= 2
                else "#F59E0B" if uv_index <= 5
                else "#E65100" if uv_index <= 7
                else "#C0392B")
    uv_risk  = (t("risk.low") if uv_index is None or uv_index <= 2
                else t("risk.moderate") if uv_index <= 5
                else t("risk.high") if uv_index <= 7
                else t("risk.very_high"))
    _uv_val  = f"{uv_index:.1f}" if uv_index is not None else "—"
    st.markdown(f"""
<div style="background:#fff;border-radius:12px;padding:18px 16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.06);
            border-left:4px solid {uv_color};margin-bottom:4px;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="flex-shrink:0;font-size:2.6rem;line-height:1;">☀️</div>
    <div>
      <div style="font-size:0.68rem;font-weight:800;color:#999;text-transform:uppercase;
                  letter-spacing:0.1em;margin-bottom:4px;">{t("pulse.uv")}</div>
      <div style="font-size:1.8rem;font-weight:800;color:#1A1A1A;line-height:1.1;">{_uv_val}</div>
      <div style="font-size:0.78rem;color:#999;margin-top:4px;">{t("pulse.uv.sub", risk=uv_risk)}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    elbe_color = ("#007A6E" if elbe_val is None or elbe_val < 200
                  else "#F59E0B" if elbe_val < 400
                  else "#C0392B")
    _elbe_val = f"{elbe_val:.0f} cm" if elbe_val is not None else "—"
    st.markdown(f"""
<div style="background:#fff;border-radius:12px;padding:18px 16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.06);
            border-left:4px solid {elbe_color};margin-bottom:4px;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="flex-shrink:0;font-size:2.6rem;line-height:1;">🌊</div>
    <div>
      <div style="font-size:0.68rem;font-weight:800;color:#999;text-transform:uppercase;
                  letter-spacing:0.1em;margin-bottom:4px;">{t("pulse.elbe")}</div>
      <div style="font-size:1.8rem;font-weight:800;color:#1A1A1A;line-height:1.1;">{_elbe_val}</div>
      <div style="font-size:0.78rem;color:#999;margin-top:4px;">{t("pulse.elbe.sub")}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    pm_color = ("#C0392B" if pm25 is not None and pm25 > 35
                else "#F59E0B" if pm25 is not None and pm25 > 25
                else "#007A6E")
    _pm_val = f"{pm25:.1f} µg/m³" if pm25 is not None else "—"
    st.markdown(f"""
<div style="background:#fff;border-radius:12px;padding:18px 16px;
            box-shadow:0 2px 12px rgba(0,0,0,0.06);
            border-left:4px solid {pm_color};margin-bottom:4px;">
  <div style="display:flex;align-items:center;gap:14px;">
    <div style="flex-shrink:0;">{AIR_ICON}</div>
    <div>
      <div style="font-size:0.68rem;font-weight:800;color:#999;text-transform:uppercase;
                  letter-spacing:0.1em;margin-bottom:4px;">{t("pulse.pm25")}</div>
      <div style="font-size:1.8rem;font-weight:800;color:#1A1A1A;line-height:1.1;">{_pm_val}</div>
      <div style="font-size:0.78rem;color:#999;margin-top:4px;">{t("pulse.pm25.sub")}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.caption(t("home.source.pulse"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: TODAY'S TIPS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("home.sec.reco")), unsafe_allow_html=True)

tips = []
if cond and any(k in cond.lower() for k in ["rain", "sleet", "hail"]):
    tips.append(t("home.tip.rain"))
elif cond and "snow" in cond.lower():
    tips.append(t("home.tip.snow"))
elif cond and "fog" in cond.lower():
    tips.append(t("home.tip.fog"))
elif temp is not None and temp > 25:
    tips.append(t("home.tip.warm"))
elif temp is not None and temp < 0:
    tips.append(t("home.tip.freeze"))
else:
    tips.append(t("home.tip.good"))

if pm25 is not None and pm25 > 25:
    tips.append(t("home.tip.air.moderate"))
else:
    tips.append(t("home.tip.air.good"))

tips.append(t("home.tip.events"))

tips_html = "".join(f'<li style="margin-bottom:8px;">{t}</li>' for t in tips)
st.markdown(f"""
<div style="background:#fffbeb;border-left:4px solid #F59E0B;border-radius:0 14px 14px 0;
            padding:18px 24px;margin-bottom:8px;">
  <div style="font-size:0.72rem;font-weight:800;color:#92400E;text-transform:uppercase;
              letter-spacing:0.12em;margin-bottom:10px;">{t("home.tip.header")}</div>
  <ul style="margin:0;padding-left:18px;font-size:0.9rem;color:#374151;line-height:1.6;">
    {tips_html}
  </ul>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: CITY NEWS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("home.sec.news")), unsafe_allow_html=True)

if news_items:
    news_cols = st.columns(2)
    for i, item in enumerate(news_items[:4]):
        with news_cols[i % 2]:
            link_html = (
                f'<a href="{item["link"]}" target="_blank" rel="noopener" '
                f'style="color:#1565C0;text-decoration:none;font-weight:700;'
                f'font-size:0.88rem;">{item["title"]}</a>'
            ) if item.get("link") else (
                f'<span style="font-weight:700;font-size:0.88rem;color:#1A1A1A;">{item["title"]}</span>'
            )
            summary_html = (
                f'<div style="font-size:0.78rem;color:#64748b;margin-top:4px;">{item["summary"]}</div>'
            ) if item.get("summary") else ""
            date_html = (
                f'<div style="font-size:0.68rem;color:#94a3b8;margin-top:6px;">{item["date"]}</div>'
            ) if item.get("date") else ""
            st.markdown(f"""
<div style="background:#fff;border-radius:12px;padding:16px 18px;
            box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:10px;
            border-left:3px solid #1565C0;">
  {link_html}
  {summary_html}
  {date_html}
</div>
""", unsafe_allow_html=True)
    st.caption(t("home.news.source"))

else:
    st.info(t("home.news.offline"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: CITY AT A GLANCE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("home.sec.glance")), unsafe_allow_html=True)
st.caption(t("home.glance.cap"))

TOPIC_COLORS = {
    "population": "#1565C0",
    "navigation": "#D4481C",
    "city":       "#6D28D9",
}

glance_cols = st.columns(3)

# Tile 1: Population — registered residents (city total)
with glance_cols[0]:
    try:
        df_p = load_kiss("bevoelkerung/entwicklung-der-hauptwohnsitzbevoelkerung.json")
        df_city = df_p[df_p["Stadtteil-Nr."] == 15003].sort_values("Jahr")
        ly = int(df_city["Jahr"].max()); py = ly - 1
        p_ly = int(df_city[df_city["Jahr"] == ly]["Hauptwohnsitzbevölkerung"].iloc[-1])
        p_py = int(df_city[df_city["Jahr"] == py]["Hauptwohnsitzbevölkerung"].iloc[-1])
        diff = p_ly - p_py
        card_html = topic_card("🏘️", t("tile.population"), f"{p_ly/1000:.0f}k", t("tile.pop.unit"),
                               f"{abs(diff):,} vs {py}".replace(",", "."), diff >= 0,
                               str(ly), color=TOPIC_COLORS["population"], href="/population")
    except Exception:
        card_html = topic_card("🏘️", t("tile.population"), "—", t("tile.pop.unit"), "—", True,
                               "—", color=TOPIC_COLORS["population"], href="/population")
    st.markdown(card_html, unsafe_allow_html=True)

# Tile 2: Navigation — MVB annual ridership
with glance_cols[1]:
    try:
        df_m = load_kiss("verkehr/befoerderte-personen-der-magdeburger-verkehrsbetriebe-gmbh-und-co-kg.json")
        df_m["_v"] = pd.to_numeric(df_m["var2"], errors="coerce")
        df_m = df_m[df_m["_v"].notna()].sort_values("Jahr")
        ly = int(df_m["Jahr"].max()); py = ly - 1
        v_ly = float(df_m[df_m["Jahr"] == ly]["_v"].iloc[-1])
        v_py = float(df_m[df_m["Jahr"] == py]["_v"].iloc[-1]) if py in df_m["Jahr"].values else v_ly
        diff_pct = (v_ly - v_py) / v_py * 100 if v_py else 0
        card_html = topic_card("🚌", t("tile.navigation"), f"{v_ly/1e6:.0f}M", t("tile.nav.unit"),
                               f"{abs(diff_pct):.1f}% vs {py}", diff_pct >= 0,
                               str(ly), color=TOPIC_COLORS["navigation"], href="/navigation")
    except Exception:
        card_html = topic_card("🚌", t("tile.navigation"), "—", t("tile.nav.unit"), "—", True,
                               "—", color=TOPIC_COLORS["navigation"], href="/navigation")
    st.markdown(card_html, unsafe_allow_html=True)

# Tile 3: City & Culture — cultural events
with glance_cols[2]:
    try:
        df_t = load_kiss("erholung-sport-und-fremdenverkehr/ankuenfte-der-gaeste-in-magdeburg.json")
        df_t["_a"] = pd.to_numeric(df_t["Ankünfte gesamt"], errors="coerce")
        yr_totals = df_t[df_t["_a"].notna()].groupby("Jahr")["_a"].sum()
        yr_totals = yr_totals[yr_totals > 100_000]
        ly = int(yr_totals.index.max()); py = ly - 1
        a_ly = int(yr_totals[ly])
        a_py = int(yr_totals[py]) if py in yr_totals.index else a_ly
        diff_pct = (a_ly - a_py) / a_py * 100 if a_py else 0
        card_html = topic_card("🏛️", t("tile.city"), f"{a_ly/1000:.0f}k", t("tile.city.unit"),
                               f"{abs(diff_pct):.1f}% vs {py}", diff_pct >= 0,
                               str(ly), color=TOPIC_COLORS["city"], href="/city")
    except Exception:
        card_html = topic_card("🏛️", t("tile.city"), "—", t("tile.city.unit"), "—", True,
                               "—", color=TOPIC_COLORS["city"], href="/city")
    st.markdown(card_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: CITY SERVICES & CONTACTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("home.sec.services")), unsafe_allow_html=True)

_CONTACTS = [
    {"icon": _FIRE_ICON,   "name": t("svc.emergency"),  "number": "112",
     "detail": t("svc.emergency.detail"),  "color": "#C0392B"},
    {"icon": _POLICE_ICON, "name": t("svc.police"),     "number": "110",
     "detail": t("svc.police.detail"),     "color": "#1565C0"},
    {"icon": "🏥",         "name": t("svc.medical"),    "number": "116 117",
     "detail": t("svc.medical.detail"),    "color": "#DC2626"},
    {"icon": _BLDG_ICON,   "name": t("svc.cityhall"),   "number": "+49 391 540-0",
     "detail": t("svc.cityhall.detail"),   "color": "#007A6E"},
    {"icon": _BUS_ICON,    "name": t("svc.mvb"),        "number": "+49 391 886-0",
     "detail": t("svc.mvb.detail"),        "color": "#6A1B9A"},
    {"icon": "💡",         "name": t("svc.stadtwerke"), "number": "+49 391 587-0",
     "detail": t("svc.stadtwerke.detail"), "color": "#F59E0B"},
    {"icon": "🔧",         "name": t("svc.maintenance"),"number": "+49 391 540-2233",
     "detail": t("svc.maintenance.detail"),"color": "#78716C"},
    {"icon": "📚",         "name": t("svc.library"),    "number": "+49 391 540-4506",
     "detail": t("svc.library.detail"),    "color": "#0891B2"},
    {"icon": "ℹ️",        "name": t("svc.tourist"),    "number": "+49 391 8380-430",
     "detail": t("svc.tourist.detail"),    "color": "#2E7D32"},
]

_cc = st.columns(3)
for i, c in enumerate(_CONTACTS):
    with _cc[i % 3]:
        st.markdown(
            f'<div style="background:#fff;border-radius:12px;padding:16px 18px;'
            f'box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:12px;'
            f'border-left:4px solid {c["color"]};">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<span style="display:inline-flex;align-items:center;font-size:1.4rem;line-height:1;">{c["icon"]}</span>'
            f'<span style="font-size:0.78rem;font-weight:700;color:#374151;">{c["name"]}</span>'
            f'</div>'
            f'<div style="font-size:1.15rem;font-weight:900;color:{c["color"]};margin-bottom:4px;">{c["number"]}</div>'
            f'<div style="font-size:0.74rem;color:#94a3b8;">{c["detail"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: CITY MAP
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("home.sec.explore")), unsafe_allow_html=True)

landmarks = [
    (52.1316, 11.6397, "Dom", t("home.landmark.dom")),
    (52.1275, 11.6361, "Rathaus", t("home.landmark.rathaus")),
    (52.1229, 11.6457, "Hundertwasserhaus", t("home.landmark.hundert")),
    (52.1361, 11.6272, "Elbauenpark", t("home.landmark.elbauen")),
    (52.1302, 11.6267, "Magdeburg Hbf", t("home.landmark.hbf")),
    (52.1393, 11.6470, "OVGU Campus", t("home.landmark.ovgu")),
    (52.1219, 11.6306, "Elbe Promenade", t("home.landmark.elbe")),
]

m = folium.Map(location=[52.131, 11.640], zoom_start=13, tiles="CartoDB positron")
for lat, lon, name, tooltip in landmarks:
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(f"<b>{name}</b><br><small>{tooltip}</small>", max_width=240),
        tooltip=tooltip,
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

map_html = m._repr_html_()
components.html(map_html, height=440, scrolling=False)
st.caption(t("home.map.source"))


st.markdown(
    "<div style='height:20px'></div>"
    "<div style='font-size:0.72rem;color:#94a3b8;text-align:center;padding-bottom:16px;'>"
    f"{t('home.footer')}"
    "</div>",
    unsafe_allow_html=True,
)
