import json
import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import folium
import branca.colormap as cm

from utils.data_loader import load_kiss, load_mietspiegel
from utils.constants import MONTHS_DE, MD_TEAL, MD_ORANGE, MD_BLUE, MD_RED, PLOTLY_TEMPLATE
from utils.ui_helpers import hero_stat, section_header, insight_box, live_card
from utils.i18n import t

POP_BLUE   = "#1565C0"
POP_CORAL  = "#E8650B"
POP_GREEN  = "#2E7D32"

# ── Page header ───────────────────────────────────────────────────────────────
st.title(t("pop.title"))
st.markdown(
    f"<p style='font-size:0.97rem;color:#64748b;max-width:680px;margin:-6px 0 20px 0;'>"
    f"{t('pop.subtitle')}"
    f"</p>",
    unsafe_allow_html=True,
)
st.caption(t("pop.source.header"))

# ── Load core datasets ────────────────────────────────────────────────────────
df_pop_raw = load_kiss("bevoelkerung/bevoelkerungsbestand-monatlich.json")
df_pop_raw = df_pop_raw.sort_values("Jahr")

# ── Hero KPI ──────────────────────────────────────────────────────────────────
try:
    _cy  = int(df_pop_raw["Jahr"].max())
    _py  = _cy - 1
    _cp  = int(df_pop_raw[df_pop_raw["Jahr"] == _cy]["var5"].mean())
    _pp  = int(df_pop_raw[df_pop_raw["Jahr"] == _py]["var5"].mean())
    _d   = _cp - _pp
    st.markdown(hero_stat(
        "👥",
        f"{_cp:,}".replace(",", "."),
        t("pop.hero.desc", year=_cy),
        f"{'+' if _d>=0 else ''}{_d:,} {t('pop.vs_year', year=_py)}".replace(",", "."),
        delta_positive=_d >= 0,
        color=POP_BLUE,
    ), unsafe_allow_html=True)
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: POPULATION SNAPSHOT METRICS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("pop.sec.glance"), color=POP_BLUE), unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)

# Total population
with m1:
    try:
        cy = int(df_pop_raw["Jahr"].max())
        pop_val = int(df_pop_raw[df_pop_raw["Jahr"] == cy]["var5"].mean())
        st.markdown(live_card("👥", t("pop.total"),
            f"{pop_val:,}".replace(",", "."), t("pop.primary", year=cy),
            status_color=POP_BLUE), unsafe_allow_html=True)
    except Exception:
        st.markdown(live_card("👥", t("pop.total"), "—", t("common.data_unavailable"),
            status_color=POP_BLUE), unsafe_allow_html=True)

# YoY change
with m2:
    try:
        cy_p = int(df_pop_raw[df_pop_raw["Jahr"] == cy]["var5"].mean())
        py_p = int(df_pop_raw[df_pop_raw["Jahr"] == cy - 1]["var5"].mean())
        delta = cy_p - py_p
        d_color = POP_GREEN if delta >= 0 else MD_RED
        st.markdown(live_card("📈", t("pop.yoy"),
            f"{'+' if delta >= 0 else ''}{delta:,}".replace(",", "."),
            t("pop.vs_year", year=cy - 1), status_color=d_color), unsafe_allow_html=True)
    except Exception:
        st.markdown(live_card("📈", t("pop.yoy"), "—", t("common.data_unavailable"),
            status_color=POP_GREEN), unsafe_allow_html=True)

# Average age
with m3:
    try:
        df_age = load_kiss("bevoelkerung/altersdurchschnitt.json")
        age_col = next((c for c in df_age.columns if "alter" in c.lower() and c != "Jahr"), None)
        if age_col:
            df_age[age_col] = pd.to_numeric(df_age[age_col], errors="coerce")
            latest_age = float(df_age[df_age[age_col].notna()].sort_values("Jahr")[age_col].iloc[-1])
            latest_age_yr = int(df_age[df_age[age_col].notna()].sort_values("Jahr")["Jahr"].iloc[-1])
            st.markdown(live_card("👴", t("pop.avg_age"),
                f"{latest_age:.1f} {t('pop.years')}", t("pop.city_avg", year=latest_age_yr),
                status_color=POP_BLUE), unsafe_allow_html=True)
        else:
            raise ValueError("no age column")
    except Exception:
        st.markdown(live_card("👴", t("pop.avg_age"), "—", t("common.data_unavailable"),
            status_color=POP_BLUE), unsafe_allow_html=True)

# Foreign residents %
with m4:
    try:
        cy_f = float(df_pop_raw[df_pop_raw["Jahr"] == cy]["var8"].mean())
        cy_t = float(df_pop_raw[df_pop_raw["Jahr"] == cy]["var5"].mean())
        foreign_pct = cy_f / cy_t * 100 if cy_t else 0
        st.markdown(live_card("🌍", t("pop.foreign"),
            f"{foreign_pct:.1f}%", t("pop.people", people=f"{int(cy_f):,}".replace(",", "."), year=cy),
            status_color=MD_ORANGE), unsafe_allow_html=True)
    except Exception:
        st.markdown(live_card("🌍", t("pop.foreign"), "—", t("common.data_unavailable"),
            status_color=MD_ORANGE), unsafe_allow_html=True)

# Net migration balance
with m5:
    try:
        df_mig = load_kiss("bevoelkerung/wanderungsbewegungen-nach-geschlecht.json")
        # Columns are unlabeled: var2=arrivals, var5=departures, var8=balance
        # Detect by checking which col first becomes negative (balance) vs. always positive (flows)
        saldo_col = next((c for c in df_mig.columns
                          if c not in ("Jahr",) and
                             pd.to_numeric(df_mig[c], errors="coerce").min() < 0), None)
        if not saldo_col and "var8" in df_mig.columns:
            saldo_col = "var8"
        if saldo_col:
            df_mig[saldo_col] = pd.to_numeric(df_mig[saldo_col], errors="coerce")
            latest_m = df_mig[df_mig[saldo_col].notna()].sort_values("Jahr")
            mig_val  = int(latest_m[saldo_col].iloc[-1])
            mig_yr   = int(latest_m["Jahr"].iloc[-1])
            m_color  = POP_GREEN if mig_val >= 0 else MD_RED
            st.markdown(live_card("➡️", t("pop.net_migration"),
                f"{'+' if mig_val >= 0 else ''}{mig_val:,}".replace(",", "."),
                t("pop.arrivals_minus", year=mig_yr),
                status_color=m_color), unsafe_allow_html=True)
        else:
            raise ValueError("no migration column")
    except Exception:
        st.markdown(live_card("➡️", t("pop.net_migration"), "—", t("common.data_unavailable"),
            status_color=POP_GREEN), unsafe_allow_html=True)

st.caption(t("pop.source.kiss"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: POPULATION TREND
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("pop.sec.trend"), color=POP_BLUE), unsafe_allow_html=True)

try:
    df_pop = df_pop_raw.copy()
    df_pop["_month_num"] = df_pop["Monat"].map(MONTHS_DE).fillna(1)
    df_pop["date"] = pd.to_datetime(
        df_pop["Jahr"].astype(str) + "-" + df_pop["_month_num"].astype(int).astype(str) + "-01"
    )
    df_pop = df_pop.sort_values("date")
    df_pop["Gesamt"]    = pd.to_numeric(df_pop["var5"], errors="coerce")
    df_pop["Ausländer"] = pd.to_numeric(df_pop["var8"], errors="coerce").fillna(0)
    df_pop["Deutsche"]  = df_pop["Gesamt"] - df_pop["Ausländer"]

    pop_yr_range = st.slider(
        t("common.year_range"), int(df_pop["Jahr"].min()), int(df_pop["Jahr"].max()),
        value=(2000, int(df_pop["Jahr"].max())), key="pop_years",
    )
    mask    = (df_pop["Jahr"] >= pop_yr_range[0]) & (df_pop["Jahr"] <= pop_yr_range[1])
    df_plot = df_pop[mask]
    show_breakdown = st.checkbox(t("pop.breakdown"), value=True, key="pop_breakdown")

    fig_pop = go.Figure()
    if show_breakdown:
        fig_pop.add_trace(go.Scatter(
            x=df_plot["date"], y=df_plot["Deutsche"],
            mode="lines", name=t("pop.trace.german"),
            stackgroup="one", line=dict(color=POP_BLUE),
            hovertemplate=f"%{{x|%b %Y}}: %{{y:,.0f}}<extra>{t('pop.trace.german')}</extra>",
        ))
        fig_pop.add_trace(go.Scatter(
            x=df_plot["date"], y=df_plot["Ausländer"],
            mode="lines", name=t("pop.trace.foreign"),
            stackgroup="one", line=dict(color=MD_ORANGE),
            hovertemplate=f"%{{x|%b %Y}}: %{{y:,.0f}}<extra>{t('pop.trace.foreign')}</extra>",
        ))
    else:
        fig_pop.add_trace(go.Scatter(
            x=df_plot["date"], y=df_plot["Gesamt"],
            mode="lines", name=t("pop.trace.total"),
            line=dict(color=POP_BLUE, width=2),
            hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra></extra>",
        ))
    fig_pop.update_layout(
        template=PLOTLY_TEMPLATE,
        yaxis_title=t("pop.axis.residents"),
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=60, r=20, t=30, b=60),
        yaxis=dict(tickformat=",d"),
    )
    st.plotly_chart(fig_pop, use_container_width=True)
    st.markdown(insight_box(
        t("pop.insight.trend")
    ), unsafe_allow_html=True)
    st.caption(t("pop.cap.primary"))
except Exception as e:
    st.warning(t("pop.warn.trend", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: BIRTHS, DEATHS & MIGRATION
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("pop.sec.natural"), color=POP_BLUE), unsafe_allow_html=True)

nat_col, mig_col = st.columns(2)

with nat_col:
    st.caption(t("pop.cap.births"))
    try:
        df_vit = load_kiss("bevoelkerung/geburten-sterbefaelle-und-eheschliessungen-monatlich.json")
        birth_col = next((c for c in df_vit.columns if "geborene" in c.lower() or "geburt" in c.lower()), None)
        death_col = next((c for c in df_vit.columns if "sterbef" in c.lower() or "gestor" in c.lower()), None)
        if birth_col and death_col:
            df_vit[birth_col] = pd.to_numeric(df_vit[birth_col], errors="coerce")
            df_vit[death_col] = pd.to_numeric(df_vit[death_col], errors="coerce")
            df_nat = df_vit.groupby("Jahr").agg(
                Births=(birth_col, "sum"), Deaths=(death_col, "sum")
            ).reset_index().sort_values("Jahr")
            df_nat = df_nat[(df_nat["Births"] > 0) | (df_nat["Deaths"] > 0)]

            fig_nat = go.Figure()
            fig_nat.add_trace(go.Scatter(
                x=df_nat["Jahr"], y=df_nat["Births"],
                mode="lines+markers", name=t("pop.births"),
                line=dict(color=POP_GREEN, width=2),
                hovertemplate=f"%{{x}}: %{{y:,}} {t('pop.births').lower()}<extra></extra>",
            ))
            fig_nat.add_trace(go.Scatter(
                x=df_nat["Jahr"], y=df_nat["Deaths"],
                mode="lines+markers", name=t("pop.deaths"),
                line=dict(color=MD_RED, width=2),
                hovertemplate=f"%{{x}}: %{{y:,}} {t('pop.deaths').lower()}<extra></extra>",
            ))
            # Shaded area between lines
            fig_nat.add_trace(go.Scatter(
                x=pd.concat([df_nat["Jahr"], df_nat["Jahr"][::-1]]),
                y=pd.concat([df_nat["Births"], df_nat["Deaths"][::-1]]),
                fill="toself",
                fillcolor="rgba(46,125,50,0.12)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))
            fig_nat.update_layout(
                template=PLOTLY_TEMPLATE,
                yaxis_title=t("common.people_year"),
                yaxis=dict(tickformat=",d"),
                legend=dict(orientation="h", y=-0.2),
                margin=dict(l=50, r=10, t=20, b=60),
                height=300,
            )
            st.plotly_chart(fig_nat, use_container_width=True)
        else:
            st.info(t("pop.info.birth_cols"))
    except Exception as e:
        st.info(t("pop.info.natural", error=e))

with mig_col:
    st.caption(t("pop.cap.migration"))
    try:
        df_mig2 = load_kiss("bevoelkerung/wanderungsbewegungen-nach-geschlecht.json")
        # var2=arrivals, var5=departures, var8=balance (columns unlabeled in source)
        zu_col  = "var2" if "var2" in df_mig2.columns else next(
                      (c for c in df_mig2.columns if "zuzug" in c.lower()), None)
        weg_col = "var5" if "var5" in df_mig2.columns else next(
                      (c for c in df_mig2.columns if "wegzug" in c.lower()), None)
        if zu_col and weg_col:
            df_mig2[zu_col]  = pd.to_numeric(df_mig2[zu_col],  errors="coerce")
            df_mig2[weg_col] = pd.to_numeric(df_mig2[weg_col], errors="coerce")
            df_mig2["saldo"] = df_mig2[zu_col] - df_mig2[weg_col]
            df_migsum = df_mig2.groupby("Jahr").agg(
                Arrivals=(zu_col, "sum"),
                Departures=(weg_col, "sum"),
                Balance=("saldo", "sum"),
            ).reset_index().sort_values("Jahr")
            df_migsum = df_migsum[df_migsum["Arrivals"] > 0]

            fig_mig = go.Figure()
            fig_mig.add_trace(go.Bar(
                x=df_migsum["Jahr"], y=df_migsum["Arrivals"],
                name=t("pop.arrivals"), marker_color=POP_BLUE, opacity=0.7,
                hovertemplate=f"%{{x}}: %{{y:,}} {t('pop.arrivals').lower()}<extra></extra>",
            ))
            fig_mig.add_trace(go.Bar(
                x=df_migsum["Jahr"], y=-df_migsum["Departures"],
                name=t("pop.departures"), marker_color=MD_RED, opacity=0.7,
                hovertemplate=f"%{{x}}: %{{customdata:,}} {t('pop.departures').lower()}<extra></extra>",
                customdata=df_migsum["Departures"],
            ))
            fig_mig.add_trace(go.Scatter(
                x=df_migsum["Jahr"], y=df_migsum["Balance"],
                mode="lines+markers", name=t("pop.balance"),
                line=dict(color="black", width=1.5, dash="dot"),
                yaxis="y2",
                hovertemplate=f"%{{x}}: %{{y:,}} {t('pop.balance').lower()}<extra></extra>",
            ))
            fig_mig.update_layout(
                template=PLOTLY_TEMPLATE,
                barmode="relative",
                yaxis=dict(title=t("common.people_year"), tickformat=",d"),
                yaxis2=dict(title=t("pop.balance"), overlaying="y", side="right", tickformat=",d"),
                legend=dict(orientation="h", y=-0.2),
                margin=dict(l=50, r=60, t=20, b=60),
                height=300,
            )
            st.plotly_chart(fig_mig, use_container_width=True)
        else:
            st.info(t("pop.info.migration_cols"))
    except Exception as e:
        st.info(t("pop.info.migration", error=e))

st.caption(t("pop.source.vital"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: RENTAL PRICE MAP
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("pop.sec.rent"), color=POP_BLUE), unsafe_allow_html=True)
st.caption(t("pop.cap.rent_map"))

try:
    map_ctrl_l, map_ctrl_r = st.columns([1, 2])

    with map_ctrl_l:
        map_view = st.radio(t("pop.view_by"), [t("pop.apartment_size"), t("pop.building_age")],
                            horizontal=True, key="rent_map_view")

    if map_view == t("pop.apartment_size"):
        df_miet = load_mietspiegel("wohnflaeche")
        class_col = "wohnflaechenklasse"
        classes   = sorted(df_miet[class_col].unique())
        with map_ctrl_r:
            mr_a, mr_b = st.columns(2)
            with mr_a:
                sel_map_year  = st.selectbox(t("common.year"), sorted(df_miet["year"].unique())[::-1], key="map_year_sz")
            with mr_b:
                sel_map_class = st.selectbox(t("pop.apartment_size"), classes, index=1, key="map_class_sz")
    else:
        df_miet = load_mietspiegel("baualter")
        class_col = "baualtersklasse"
        classes   = sorted(df_miet[class_col].unique())
        with map_ctrl_r:
            mr_a2, mr_b2 = st.columns(2)
            with mr_a2:
                sel_map_year  = st.selectbox(t("common.year"), sorted(df_miet["year"].unique())[::-1], key="map_year_ba")
            with mr_b2:
                sel_map_class = st.selectbox(t("pop.building_age"), classes, index=1, key="map_class_ba")

    df_filt = df_miet[(df_miet["year"] == sel_map_year) & (df_miet[class_col] == sel_map_class)]
    rent_by_district = df_filt.groupby("stadtteil")["nettokaltmiete_pro_qm"].mean().reset_index()
    rent_by_district.columns = ["name", "rent"]
    rent_dict = {k.lower().strip(): v for k, v in zip(rent_by_district["name"], rent_by_district["rent"])}

    # Load district boundaries
    _st_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "Stadtteile", "Stadtteile.geojson")
    )
    with open(_st_path, encoding="utf-8") as f:
        stadtteile_geo = json.load(f)

    # Add rent value to each feature
    for feat in stadtteile_geo["features"]:
        feat_name = feat["properties"].get("name", "")
        r_val = rent_dict.get(feat_name.lower().strip())
        feat["properties"]["rent"] = round(r_val, 2) if r_val is not None else None

    rent_vals = [feat["properties"]["rent"] for feat in stadtteile_geo["features"]
                 if feat["properties"]["rent"] is not None]

    m_rent = folium.Map(location=[52.131, 11.640], zoom_start=11, tiles="CartoDB positron")

    if rent_vals:
        vmin, vmax = min(rent_vals), max(rent_vals)
        colormap = cm.LinearColormap(
            colors=["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
            vmin=vmin, vmax=vmax,
            caption=t("pop.rent"),
        )

        def style_fn(feature):
            rv = feature["properties"].get("rent")
            if rv is not None:
                return {"fillColor": colormap(rv), "color": "#fff", "weight": 1.5,
                        "fillOpacity": 0.78}
            return {"fillColor": "#d0d0d0", "color": "#ccc", "weight": 1, "fillOpacity": 0.3}

        folium.GeoJson(
            stadtteile_geo,
            style_function=style_fn,
            tooltip=folium.GeoJsonTooltip(
                fields=["name", "rent"],
                aliases=[t("common.district"), t("pop.rent")],
                localize=True,
            ),
        ).add_to(m_rent)
        colormap.add_to(m_rent)
    else:
        # Fallback: outline only
        folium.GeoJson(stadtteile_geo,
                       style_function=lambda f: {"color": "#007A6E", "weight": 1.5,
                                                 "fillOpacity": 0.05}
                       ).add_to(m_rent)

    components.html(m_rent._repr_html_(), height=460, scrolling=False)

    # District ranking bar below map
    if not rent_by_district.empty:
        rbd_sorted = rent_by_district.sort_values("rent", ascending=True)
        bar_colors = ["#ffffb2" if v < 6 else "#fd8d3c" if v < 8 else "#bd0026"
                      for v in rbd_sorted["rent"]]
        fig_rank = go.Figure(go.Bar(
            y=rbd_sorted["name"], x=rbd_sorted["rent"],
            orientation="h",
            marker_color=bar_colors,
            text=rbd_sorted["rent"].map(lambda v: f"€{v:.2f}"),
            textposition="outside",
            hovertemplate="%{y}: €%{x:.2f}/m²<extra></extra>",
        ))
        fig_rank.update_layout(
            template=PLOTLY_TEMPLATE,
            xaxis_title=t("pop.axis.net_rent"),
            yaxis_title="",
            height=max(360, len(rbd_sorted) * 20),
            margin=dict(l=160, r=80, t=20, b=40),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    st.caption(t("pop.source.rent_map"))

except Exception as e:
    st.warning(t("pop.warn.rent_map", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: RENT TRENDS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("pop.sec.renttren"), color=POP_BLUE), unsafe_allow_html=True)

try:
    df_rent = load_mietspiegel("wohnflaeche")
    years_r       = sorted(df_rent["year"].unique())
    area_classes  = sorted(df_rent["wohnflaechenklasse"].unique())

    ctrl_l, ctrl_r = st.columns(2)
    with ctrl_l:
        sel_year_r = st.selectbox(t("pop.rent_year_bar"), years_r[::-1], key="rent_year")
    with ctrl_r:
        sel_area_r = st.selectbox(t("pop.apartment_size"), area_classes, index=1, key="rent_area")

    df_r = df_rent[(df_rent["year"] == sel_year_r) & (df_rent["wohnflaechenklasse"] == sel_area_r)]
    df_r = df_r.sort_values("nettokaltmiete_pro_qm", ascending=True)

    bar_col_fn = lambda v: MD_TEAL if v < 6 else MD_ORANGE if v < 8 else MD_RED
    fig_rbar = go.Figure(go.Bar(
        y=df_r["stadtteil"], x=df_r["nettokaltmiete_pro_qm"],
        orientation="h",
        marker_color=[bar_col_fn(v) for v in df_r["nettokaltmiete_pro_qm"]],
        text=df_r["nettokaltmiete_pro_qm"].map(lambda v: f"€{v:.2f}"),
        textposition="outside",
        hovertemplate="%{y}: €%{x:.2f}/m²<extra></extra>",
    ))
    city_mean_r = float(df_r["nettokaltmiete_pro_qm"].mean())
    fig_rbar.add_vline(x=city_mean_r, line_dash="dash", line_color="#374151",
                       annotation_text=f"{t('common.city_avg')}: €{city_mean_r:.2f}",
                       annotation_position="top right")
    fig_rbar.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="€/m²",
        height=max(380, len(df_r) * 22),
        margin=dict(l=160, r=80, t=30, b=40),
    )
    st.plotly_chart(fig_rbar, use_container_width=True)

    # Trend for selected district + city avg
    st.caption(t("pop.cap.rent_trend"))
    districts_r   = sorted(df_rent["stadtteil"].unique())
    sel_district_r = st.selectbox(t("common.district"), districts_r, key="rent_district")
    df_trend = df_rent[(df_rent["stadtteil"] == sel_district_r) &
                       (df_rent["wohnflaechenklasse"] == sel_area_r)]
    df_city_trend = df_rent[df_rent["wohnflaechenklasse"] == sel_area_r].groupby("year")[
                        "nettokaltmiete_pro_qm"].mean().reset_index()

    if not df_trend.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_trend["year"], y=df_trend["nettokaltmiete_pro_qm"],
            mode="lines+markers", name=sel_district_r,
            line=dict(color=POP_BLUE, width=2),
            hovertemplate="%{x}: €%{y:.2f}/m²<extra></extra>",
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_city_trend["year"], y=df_city_trend["nettokaltmiete_pro_qm"],
            mode="lines", name=t("common.city_avg"),
            line=dict(color="#94a3b8", width=1.5, dash="dot"),
            hovertemplate="%{x}: €%{y:.2f}/m² city avg<extra></extra>",
        ))
        fig_trend.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis_title="€/m²",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=50, r=20, t=20, b=60),
            height=280,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # Rent by building age
    st.caption(t("pop.cap.rent_age"))
    df_age_rent = load_mietspiegel("baualter")
    df_age_city = df_age_rent.groupby(["year", "baualtersklasse"])[
                      "nettokaltmiete_pro_qm"].mean().reset_index()
    age_classes = sorted(df_age_city["baualtersklasse"].unique())
    age_colors  = [POP_BLUE, MD_TEAL, POP_GREEN, MD_ORANGE, MD_RED]

    fig_age = go.Figure()
    for i, cls in enumerate(age_classes):
        sub = df_age_city[df_age_city["baualtersklasse"] == cls]
        fig_age.add_trace(go.Scatter(
            x=sub["year"], y=sub["nettokaltmiete_pro_qm"],
            mode="lines+markers", name=cls,
            line=dict(color=age_colors[i % len(age_colors)], width=2),
            hovertemplate=f"{cls} %{{x}}: €%{{y:.2f}}/m²<extra></extra>",
        ))
    fig_age.update_layout(
        template=PLOTLY_TEMPLATE,
        yaxis_title=f"€/m² ({t('common.city_avg').lower()})",
        xaxis_title=t("common.year"),
        legend=dict(orientation="h", y=-0.25, font=dict(size=11)),
        margin=dict(l=50, r=20, t=20, b=80),
        height=320,
    )
    st.plotly_chart(fig_age, use_container_width=True)
    st.markdown(insight_box(
        t("pop.insight.rent")
    ), unsafe_allow_html=True)
    st.caption(t("pop.source.rent"))

except Exception as e:
    st.warning(t("pop.warn.rent", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: HOUSING VACANCY
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("pop.sec.vacancy"), color=POP_BLUE), unsafe_allow_html=True)
st.caption(t("pop.cap.vacancy"))

try:
    df_leer = load_kiss("bautaetigkeit-und-wohnen/leerstand-im-geschosswohnungsbau.json")
    gesamt_col = next((c for c in df_leer.columns if "gesamt" in c.lower()), None)
    leer_col   = next((c for c in df_leer.columns if "leersteh" in c.lower()), None)
    quote_col  = "Leerstandsquote" if "Leerstandsquote" in df_leer.columns else next(
                     (c for c in df_leer.columns if "quote" in c.lower()), None)

    if gesamt_col and leer_col:
        df_leer[gesamt_col] = pd.to_numeric(df_leer[gesamt_col], errors="coerce")
        df_leer[leer_col]   = pd.to_numeric(df_leer[leer_col],   errors="coerce")
        df_city_v = df_leer.groupby("Jahr").apply(
            lambda g: g[leer_col].sum() / g[gesamt_col].sum() * 100
                      if g[gesamt_col].sum() > 0 else None
        ).reset_index(name="Vacancy_%")
        df_city_v = df_city_v[df_city_v["Vacancy_%"].notna()]
    elif quote_col:
        df_leer[quote_col] = pd.to_numeric(df_leer[quote_col], errors="coerce")
        df_city_v = df_leer.groupby("Jahr")[quote_col].mean().reset_index()
        df_city_v.columns = ["Jahr", "Vacancy_%"]
    else:
        raise ValueError(t("pop.err.vacancy_cols"))

    vac_l, vac_r = st.columns([2, 1])

    with vac_l:
        fig_vac = go.Figure()
        fig_vac.add_trace(go.Scatter(
            x=df_city_v["Jahr"], y=df_city_v["Vacancy_%"],
            mode="lines+markers", fill="tozeroy",
            line=dict(color=MD_ORANGE), fillcolor="rgba(232,119,34,0.15)",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
            name=t("pop.vacancy_rate"),
        ))
        peak_row = df_city_v.loc[df_city_v["Vacancy_%"].idxmax()]
        fig_vac.add_annotation(
            x=peak_row["Jahr"], y=peak_row["Vacancy_%"],
            text=f"{t('pop.peak')}: {peak_row['Vacancy_%']:.1f}% ({int(peak_row['Jahr'])})",
            showarrow=True, arrowhead=2, ax=40, ay=-30,
        )
        fig_vac.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis_title=t("pop.axis.vacancy"),
            xaxis_title=t("common.year"),
            margin=dict(l=50, r=20, t=30, b=40),
            height=300,
        )
        st.plotly_chart(fig_vac, use_container_width=True)

    with vac_r:
        # Top districts by latest vacancy
        if quote_col:
            df_leer_latest = df_leer[df_leer["Jahr"] == df_leer["Jahr"].max()].copy()
            df_leer_latest[quote_col] = pd.to_numeric(df_leer_latest[quote_col], errors="coerce")
            df_top = (df_leer_latest[df_leer_latest[quote_col].notna()]
                      .sort_values(quote_col, ascending=False)
                      .head(10))
            if not df_top.empty:
                stadtteil_col = next((c for c in df_top.columns
                                      if "stadtteil" in c.lower() and "nr" not in c.lower()), None)
                id_col = "Stadtteil-Nr." if "Stadtteil-Nr." in df_top.columns else df_top.columns[1]
                fig_top_v = go.Figure(go.Bar(
                    y=df_top[stadtteil_col if stadtteil_col else id_col].astype(str),
                    x=df_top[quote_col],
                    orientation="h",
                    marker_color=MD_ORANGE,
                    hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
                ))
                fig_top_v.update_layout(
                    template=PLOTLY_TEMPLATE,
                    title=t("pop.vacancy.top", year=int(df_leer["Jahr"].max())),
                    xaxis_title="%",
                    height=300,
                    margin=dict(l=80, r=20, t=40, b=40),
                )
                st.plotly_chart(fig_top_v, use_container_width=True)

    latest_vac = float(df_city_v["Vacancy_%"].iloc[-1])
    peak_vac   = float(peak_row["Vacancy_%"])
    st.markdown(insight_box(
        t("pop.insight.vacancy", peak=peak_vac, year=int(peak_row["Jahr"]), latest=latest_vac)
    ), unsafe_allow_html=True)
    st.caption(t("pop.source.vacancy"))

except Exception as e:
    st.warning(t("pop.warn.vacancy", error=e))
