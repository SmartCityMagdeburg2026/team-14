import json
import os
import streamlit as st
import streamlit.components.v1 as components
import folium
from folium.plugins import MarkerCluster, HeatMap
import plotly.graph_objects as go
import pandas as pd

from utils.live_api   import (fetch_weather, fetch_elbe_level,
                               load_mvb_stops, fetch_departures,
                               fetch_service_disruptions)
from utils.overpass   import fetch_parking, fetch_charging, fetch_transit_stops, fetch_restaurants
from utils.ui_helpers import section_header, live_card
from utils.i18n import t
from utils.constants  import PLOTLY_TEMPLATE

NAV_ORANGE = "#D4481C"
NAV_AMBER  = "#E8650B"

# ── Page header ───────────────────────────────────────────────────────────────
st.title(t("navi.title"))
st.markdown(
    f"<p style='font-size:0.97rem;color:#64748b;max-width:680px;margin:-6px 0 20px 0;'>"
    f"{t('navi.subtitle')}"
    f"</p>",
    unsafe_allow_html=True,
)

# ── Live data ─────────────────────────────────────────────────────────────────
weather  = fetch_weather()
elbe     = fetch_elbe_level()

temp     = weather.get("temperature")   if weather else None
wind_spd = weather.get("wind_speed")    if weather else None
cond     = weather.get("condition", "") if weather else ""
precip   = weather.get("precipitation") if weather else None
elbe_val = elbe.get("value")            if elbe    else None

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: TRAFFIC ALERTS
# ─────────────────────────────────────────────────────────────────────────────
alerts = []

if temp is not None and temp < 0:
    alerts.append((t("navi.alert.blackice.title"),
                   t("navi.alert.blackice.msg", temp=temp), "warning"))
elif temp is not None and temp < 3 and precip is not None and precip > 0:
    alerts.append((t("navi.alert.slippery.title"),
                   t("navi.alert.slippery.msg", temp=temp), "warning"))

if cond and "fog" in cond.lower():
    alerts.append((t("navi.alert.fog.title"), t("navi.alert.fog.msg"), "warning"))

if wind_spd is not None and wind_spd > 60:
    alerts.append((t("navi.alert.wind.title"),
                   t("navi.alert.wind.msg", wind=wind_spd), "warning"))

if elbe_val is not None and elbe_val > 400:
    alerts.append((t("navi.alert.elbe.title"),
                   t("navi.alert.elbe.msg", elbe=elbe_val), "error"))

if cond and any(k in cond.lower() for k in ["rain", "hail", "sleet"]):
    alerts.append((t("navi.alert.rain.title"), t("navi.alert.rain.msg"), "info"))

for d in fetch_service_disruptions():
    affects_str = f" ({t('navi.affects')}: {d['affects']})" if d["affects"] else ""
    alerts.append((f"🚌 {d['head']}", f"{d['text']}{affects_str}", "warning"))

if alerts:
    for label, msg, kind in alerts:
        if kind == "error":
            st.error(f"**{label}** — {msg}")
        elif kind == "warning":
            st.warning(f"**{label}** — {msg}")
        else:
            st.info(f"**{label}** — {msg}")
else:
    st.success(t("navi.alert.clear"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: FETCH MAP DATA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("navi.sec.map"), color=NAV_ORANGE), unsafe_allow_html=True)
st.caption(t("navi.map.cap") + " " + t("navi.map.layer_hint"))

with st.spinner(t("navi.spinner.map")):
    parking_pts     = fetch_parking()
    charging_pts    = fetch_charging()
    transit_pts     = fetch_transit_stops()
    restaurant_pts  = fetch_restaurants()

# Load accident GeoJSON
accident_pts = []
_acc_path = os.path.join(os.path.dirname(__file__), "..", "data", "Unfaelle", "Magdeburg_Unfallatlas.geojson")
try:
    with open(os.path.normpath(_acc_path), encoding="utf-8") as f:
        _acc_geojson = json.load(f)
    for feat in _acc_geojson.get("features", []):
        props = feat.get("properties", {})
        lat = props.get("lat") or props.get("LAT") or props.get("YLAT")
        lon = props.get("lon") or props.get("LON") or props.get("XLON")
        if lat and lon:
            try:
                accident_pts.append({
                    "lat": float(lat), "lon": float(lon),
                    "year": int(props.get("UJAHR", 0)),
                    "category": int(props.get("UKATEGORIE", 0)),
                    "rad": int(props.get("IstRad", 0)),
                    "pkw": int(props.get("IstPKW", 0)),
                    "fuss": int(props.get("IstFuss", 0)),
                    "krad": int(props.get("IstKrad", 0)),
                })
            except (TypeError, ValueError):
                pass
except Exception:
    pass

# Load district boundaries
_stadtteile_path = os.path.join(os.path.dirname(__file__), "..", "data", "Stadtteile", "Stadtteile.geojson")
stadtteile_geojson = None
try:
    with open(os.path.normpath(_stadtteile_path), encoding="utf-8") as f:
        stadtteile_geojson = json.load(f)
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# BUILD FOLIUM MAP
# ─────────────────────────────────────────────────────────────────────────────
m = folium.Map(location=[52.131, 11.640], zoom_start=12, tiles="CartoDB positron")

# Layer 1: District boundaries
if stadtteile_geojson:
    fg_districts = folium.FeatureGroup(name=t("navi.layer.districts"), show=True)
    folium.GeoJson(
        stadtteile_geojson,
        style_function=lambda f: {
            "fillColor": "transparent",
            "color": "#007A6E",
            "weight": 1.5,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=[f"{t('common.district')}:" ]),
    ).add_to(fg_districts)
    fg_districts.add_to(m)

# Layer 2: Transit stops
fg_transit = folium.FeatureGroup(name=t("navi.layer.transit"), show=False)
transit_cluster = MarkerCluster(
    options={"maxClusterRadius": 40, "disableClusteringAtZoom": 15}
)
for s in transit_pts:
    color = "#009E3D" if s["type"] == "bus" else "#0057A8"
    icon_char = "🚌" if s["type"] == "bus" else "🚃"
    ref_str = f" ({s['ref']})" if s.get("ref") else ""
    folium.CircleMarker(
        location=[s["lat"], s["lon"]],
        radius=5,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(
            f"<b>{icon_char} {s['name']}{ref_str}</b><br>{t('navi.popup.type')}: {s['type'].title()} {t('common.stop')}",
            max_width=200,
        ),
        tooltip=s["name"],
    ).add_to(transit_cluster)
transit_cluster.add_to(fg_transit)
fg_transit.add_to(m)

# Layer 3: Parking
fg_parking = folium.FeatureGroup(name=t("navi.layer.parking"), show=False)
parking_cluster = MarkerCluster(
    options={"maxClusterRadius": 50, "disableClusteringAtZoom": 15}
)
for p in parking_pts:
    cap_str = f"<br>{t('navi.popup.capacity')}: {p['capacity']}" if p.get("capacity") else ""
    typ_str = f"<br>{t('navi.popup.type')}: {p['type'].replace('_',' ').title()}" if p.get("type") else ""
    folium.CircleMarker(
        location=[p["lat"], p["lon"]],
        radius=6,
        color="#1565C0",
        fill=True,
        fill_color="#1565C0",
        fill_opacity=0.7,
        popup=folium.Popup(
            f"<b>🅿️ {p['name']}</b>{cap_str}{typ_str}",
            max_width=220,
        ),
        tooltip=f"🅿️ {p['name']}",
    ).add_to(parking_cluster)
parking_cluster.add_to(fg_parking)
fg_parking.add_to(m)

# Layer 4: EV Charging
fg_charging = folium.FeatureGroup(name=t("navi.layer.charging"), show=False)
for c in charging_pts:
    op_str  = f"<br>{t('navi.popup.operator')}: {c['operator']}" if c.get("operator") else ""
    soc_str = f"<br>{t('navi.popup.sockets')}: {c['sockets']}"   if c.get("sockets")  else ""
    fee_str = f"<br>{t('navi.popup.fee')}: {c['fee']}"            if c.get("fee")      else ""
    folium.Marker(
        location=[c["lat"], c["lon"]],
        popup=folium.Popup(
            f"<b>⚡ {c['name']}</b>{op_str}{soc_str}{fee_str}",
            max_width=220,
        ),
        tooltip=f"⚡ {c['name']}",
        icon=folium.DivIcon(
            html=(
                '<div style="background:#F59E0B;border:2px solid #92400E;'
                'border-radius:50%;width:22px;height:22px;display:flex;'
                'align-items:center;justify-content:center;'
                'font-size:13px;font-weight:900;color:#fff;">⚡</div>'
            ),
            icon_size=(22, 22),
            icon_anchor=(11, 11),
        ),
    ).add_to(fg_charging)
fg_charging.add_to(m)

# Layer 5: Restaurants & Cafés
fg_food = folium.FeatureGroup(name=t("navi.layer.food"), show=False)
food_cluster = MarkerCluster(options={"maxClusterRadius": 45, "disableClusteringAtZoom": 15})
for r in restaurant_pts:
    cuisine_str = f"<br>{t('navi.popup.cuisine')}: {r['cuisine']}" if r.get("cuisine") else ""
    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=5,
        color="#E65100",
        fill=True,
        fill_color="#E65100",
        fill_opacity=0.8,
        popup=folium.Popup(
            f"<b>🍽️ {r['name'] or 'Restaurant'}</b>{cuisine_str}",
            max_width=200,
        ),
        tooltip=r["name"] or r.get("amenity", "restaurant").title(),
    ).add_to(food_cluster)
food_cluster.add_to(fg_food)
fg_food.add_to(m)

# Layer 6: Accident hotspots (clustered red markers)
if accident_pts:
    fg_accidents = folium.FeatureGroup(name=t("navi.layer.accidents"), show=False)
    acc_cluster = MarkerCluster(
        options={"maxClusterRadius": 35, "disableClusteringAtZoom": 15}
    )
    cat_label = {1: t("navi.acc.fatal"), 2: t("navi.acc.serious"), 3: t("navi.acc.minor")}
    for a in accident_pts:
        cat = cat_label.get(a["category"], t("navi.acc.generic"))
        involved = []
        if a["rad"]:  involved.append(t("navi.vehicle.cyclist"))
        if a["pkw"]:  involved.append(t("navi.vehicle.car"))
        if a["fuss"]: involved.append(t("navi.vehicle.pedestrian"))
        if a["krad"]: involved.append(t("navi.vehicle.motorcycle"))
        inv_str = ", ".join(involved) if involved else t("navi.vehicle.vehicle")
        folium.CircleMarker(
            location=[a["lat"], a["lon"]],
            radius=4,
            color="#C0392B",
            fill=True,
            fill_color="#C0392B",
            fill_opacity=0.75,
            popup=folium.Popup(
                f"<b>🚨 {cat}</b><br>{t('navi.popup.year')}: {a['year']}<br>{t('navi.popup.involved')}: {inv_str}",
                max_width=200,
            ),
            tooltip=f"{t('navi.acc.generic')} {a['year']} — {cat}",
        ).add_to(acc_cluster)
    acc_cluster.add_to(fg_accidents)
    fg_accidents.add_to(m)

    # Layer 6: Accident heatmap
    fg_heatmap = folium.FeatureGroup(name=t("navi.layer.heatmap"), show=False)
    heat_data = [[a["lat"], a["lon"]] for a in accident_pts]
    HeatMap(
        heat_data,
        min_opacity=0.3,
        radius=14,
        blur=10,
        gradient={"0.4": "#ffd700", "0.65": "#ff8c00", "1": "#c0392b"},
    ).add_to(fg_heatmap)
    fg_heatmap.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

components.html(m._repr_html_(), height=560, scrolling=False)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: STATS STRIP
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("navi.sec.infra"), color=NAV_ORANGE), unsafe_allow_html=True)

stat_cols = st.columns(4)

with stat_cols[0]:
    st.markdown(live_card(
        "🅿️", t("navi.card.parking"),
        str(len(parking_pts)) if parking_pts else "—",
        t("navi.card.parking.sub"),
        status_color="#1565C0",
    ), unsafe_allow_html=True)

with stat_cols[1]:
    st.markdown(live_card(
        "⚡", t("navi.card.charging"),
        str(len(charging_pts)) if charging_pts else "—",
        t("navi.card.charging.sub"),
        status_color="#F59E0B",
    ), unsafe_allow_html=True)

with stat_cols[2]:
    bus_count  = sum(1 for s in transit_pts if s["type"] == "bus")
    tram_count = sum(1 for s in transit_pts if s["type"] == "tram")
    st.markdown(live_card(
        "🚌", t("navi.card.transit"),
        str(len(transit_pts)) if transit_pts else "—",
        t("navi.card.transit.sub", bus=bus_count, tram=tram_count),
        status_color="#009E3D",
    ), unsafe_allow_html=True)

with stat_cols[3]:
    if accident_pts:
        max_year = max(a["year"] for a in accident_pts)
        yr_count = sum(1 for a in accident_pts if a["year"] == max_year)
        st.markdown(live_card(
            "🚨", t("navi.card.accidents"),
            f"{yr_count:,}".replace(",", "."),
            t("navi.card.accidents.sub", year=max_year),
            status_color="#C0392B",
        ), unsafe_allow_html=True)
    else:
        st.markdown(live_card(
            "🚨", t("navi.card.accidents"), "—",
            t("navi.card.accidents.none"),
            status_color="#C0392B",
        ), unsafe_allow_html=True)

st.caption(t("navi.source.infra"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: LIVE DEPARTURES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("navi.sec.depart"), color=NAV_ORANGE), unsafe_allow_html=True)

mvb_stops = load_mvb_stops()
if mvb_stops:
    sel_col, hint_col = st.columns([4, 1])
    with sel_col:
        sel_idx = st.selectbox(
            t("common.stop"),
            options=range(len(mvb_stops)),
            format_func=lambda i: mvb_stops[i]["name"],
            index=None,
            placeholder=t("common.choose_stop"),
            label_visibility="collapsed",
        )
    with hint_col:
        st.caption(t("navi.depart.update"))

    if sel_idx is not None:
        selected_stop = mvb_stops[sel_idx]
        with st.spinner(t("navi.depart.spinner", stop=selected_stop["name"])):
            deps = fetch_departures(selected_stop["ext_id"])

        if deps:
            rows_html = ""
            for d in deps:
                delay_min = d["delay_min"]
                cancelled = d["cancelled"]
                if cancelled:
                    row_bg    = "background:#FFF1F2;"
                    name_sty  = "text-decoration:line-through;color:#999;"
                    delay_html = f'<span style="color:#C0392B;font-weight:700;">{t("navi.depart.cancelled")}</span>'
                else:
                    row_bg   = ""
                    name_sty = ""
                    if delay_min is None or delay_min <= 0:
                        delay_html = f'<span style="color:#2E7D32;font-weight:700;">{t("navi.depart.ontime")}</span>'
                    elif delay_min <= 5:
                        delay_html = f'<span style="color:#E8650B;font-weight:700;">+{delay_min} min</span>'
                    else:
                        delay_html = f'<span style="color:#C0392B;font-weight:700;">+{delay_min} min</span>'

                rt_cell  = d["rt_time"] if d["rt_time"] and d["rt_time"] != d["time"] else "—"
                plat_cell = d["platform"] if d["platform"] else "—"
                rows_html += f"""
<tr style="{row_bg}border-bottom:1px solid #f1f5f9;">
  <td style="padding:8px 12px;font-weight:700;color:{NAV_ORANGE};white-space:nowrap;{name_sty}">{d['line']}</td>
  <td style="padding:8px 12px;color:#374151;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{d['direction']}</td>
  <td style="padding:8px 12px;font-family:monospace;color:#374151;">{d['time']}</td>
  <td style="padding:8px 12px;font-family:monospace;color:#374151;">{rt_cell}</td>
  <td style="padding:8px 12px;">{delay_html}</td>
  <td style="padding:8px 12px;color:#94a3b8;text-align:center;">{plat_cell}</td>
</tr>"""

            st.markdown(f"""
<div style="background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-bottom:8px;">
  <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
    <thead>
      <tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
        <th style="padding:10px 12px;text-align:left;font-size:0.68rem;text-transform:uppercase;
                   letter-spacing:0.1em;color:#64748b;font-weight:800;">{t("navi.depart.line")}</th>
        <th style="padding:10px 12px;text-align:left;font-size:0.68rem;text-transform:uppercase;
                   letter-spacing:0.1em;color:#64748b;font-weight:800;">{t("navi.depart.direction")}</th>
        <th style="padding:10px 12px;text-align:left;font-size:0.68rem;text-transform:uppercase;
                   letter-spacing:0.1em;color:#64748b;font-weight:800;">{t("navi.depart.scheduled")}</th>
        <th style="padding:10px 12px;text-align:left;font-size:0.68rem;text-transform:uppercase;
                   letter-spacing:0.1em;color:#64748b;font-weight:800;">{t("navi.depart.realtime")}</th>
        <th style="padding:10px 12px;text-align:left;font-size:0.68rem;text-transform:uppercase;
                   letter-spacing:0.1em;color:#64748b;font-weight:800;">{t("navi.depart.delay")}</th>
        <th style="padding:10px 12px;text-align:center;font-size:0.68rem;text-transform:uppercase;
                   letter-spacing:0.1em;color:#64748b;font-weight:800;">{t("navi.depart.track")}</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)
            st.caption(
                t("navi.depart.caption", stop=selected_stop["name"])
            )
        else:
            st.info(t("navi.depart.none"))
    else:
        st.markdown(
            '<div style="color:#94a3b8;font-size:0.88rem;padding:12px 0;">'
            f'{t("navi.depart.prompt")}</div>',
            unsafe_allow_html=True,
        )
else:
    st.info(t("navi.depart.stops_none"))
