import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta

from utils.data_loader import load_klima_monat, load_klima_tag, load_kiss
from utils.chart_helpers import heatmap
from utils.live_api import (fetch_weather, fetch_air_quality, fetch_weather_forecast,
                             fetch_recent_daily_weather, fetch_co2_trend)
from utils.constants import (
    MONTHS_DE, MONTHS_DE_ORDER, MD_TEAL, MD_BLUE, MD_RED, MD_ORANGE, PLOTLY_TEMPLATE
)
from utils.ui_helpers import hero_stat, section_header, insight_box, live_card
from utils.i18n import t

# ── Weather condition icon helper ─────────────────────────────────────────────
_COND_ICON = {
    "dry": "☀️", "rain": "🌧️", "snow": "❄️", "sleet": "🌨️",
    "hail": "⛈️", "thunderstorm": "⛈️", "fog": "🌫️",
    "wind": "💨", "cloudy": "⛅", "partly-cloudy": "🌤️",
}
def _cond_icon(cond: str) -> str:
    c = (cond or "dry").lower()
    for key, ico in _COND_ICON.items():
        if key in c:
            return ico
    return "🌤️"

def _day_label(date_str: str) -> str:
    try:
        d = date.fromisoformat(date_str[:10])
        if d == date.today():                     return t("day.today")
        if d == date.today() + timedelta(days=1): return t("day.tomorrow")
        return d.strftime("%A")
    except Exception:
        return date_str[:10]

# ── Page header ───────────────────────────────────────────────────────────────
st.title(t("cli.title"))
st.markdown(
    f"<p style='font-size:0.97rem;color:#64748b;max-width:680px;margin:-6px 0 20px 0;'>"
    f"{t('cli.subtitle')}"
    f"</p>",
    unsafe_allow_html=True,
)
st.caption(t("cli.source.header"))

# ── Load static data ──────────────────────────────────────────────────────────
df_monthly = load_klima_monat()
df_daily   = load_klima_tag()

# ── Live API data ─────────────────────────────────────────────────────────────
weather  = fetch_weather()
pm25     = fetch_air_quality()
forecast = fetch_weather_forecast()

temp     = weather.get("temperature")        if weather else None
humidity = weather.get("relative_humidity")  if weather else None
wind_spd = weather.get("wind_speed")         if weather else None
cond     = weather.get("condition")          if weather else None

# ── Hero KPI ──────────────────────────────────────────────────────────────────
try:
    df_ann = load_kiss("wetter/witterung-in-magdeburg.json")
    # find the anomaly column (may include units)
    anom_col = next((c for c in df_ann.columns if "abweichung" in c.lower()), None)
    yr_col   = "Jahr"
    if anom_col and yr_col in df_ann.columns:
        df_ann_clean = df_ann[[yr_col, anom_col]].dropna()
        df_ann_clean = df_ann_clean.sort_values(yr_col)
        _la  = float(df_ann_clean[anom_col].iloc[-1])
        _pya = float(df_ann_clean[anom_col].iloc[-2])
        _yr  = int(df_ann_clean[yr_col].iloc[-1])
        _diff = _la - _pya
        st.markdown(hero_stat(
            "🌡️",
            f"{'+' if _la>=0 else ''}{_la:.1f} °C",
            t("cli.hero.desc", year=_yr),
            t("cli.hero.delta", delta=_diff, year=_yr-1),
            delta_positive=False,
            color="#00897B",
        ), unsafe_allow_html=True)
    else:
        raise ValueError("anomaly column not found")
except Exception:
    # Fallback to DWD monthly calculation
    try:
        _baseline = df_monthly[(df_monthly["year"] >= 1961) & (df_monthly["year"] <= 1990)]["MO_TT"].mean()
        _yearly   = df_monthly[df_monthly["MO_TT"].notna()].groupby("year")["MO_TT"].mean()
        _comp     = _yearly[_yearly.index < datetime.now().year]
        _la  = float(_comp.iloc[-1]) - _baseline
        _pya = float(_comp.iloc[-2]) - _baseline
        _yr  = int(_comp.index[-1])
        _diff = _la - _pya
        st.markdown(hero_stat(
            "🌡️",
            f"{'+' if _la>=0 else ''}{_la:.1f} °C",
            t("cli.hero.desc.base", baseline=_baseline, year=_yr),
            t("cli.hero.delta", delta=_diff, year=_yr-1),
            delta_positive=False,
            color="#00897B",
        ), unsafe_allow_html=True)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: LIVE CONDITIONS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.live"), color=MD_TEAL), unsafe_allow_html=True)

live_cols = st.columns(4)

with live_cols[0]:
    temp_color = ("#C0392B" if temp is not None and temp < 0
                  else "#E65100" if temp is not None and temp < 5
                  else "#007A6E")
    st.markdown(live_card(
        "🌡️", t("cli.live.temp"),
        f"{temp:.1f} °C" if temp is not None else "—",
        f"{_cond_icon(cond)} {(cond or '').replace('-',' ').title()}" if cond else t("pulse.temp.sub"),
        status_color=temp_color,
    ), unsafe_allow_html=True)

with live_cols[1]:
    hum_color = "#007A6E" if humidity is not None and humidity < 80 else "#F59E0B"
    st.markdown(live_card(
        "💧", t("cli.live.hum"),
        f"{humidity:.0f}%" if humidity is not None else "—",
        t("pulse.humidity.sub"),
        status_color=hum_color,
    ), unsafe_allow_html=True)

with live_cols[2]:
    wind_color = ("#C0392B" if wind_spd is not None and wind_spd > 60
                  else "#F59E0B" if wind_spd is not None and wind_spd > 40
                  else "#007A6E")
    st.markdown(live_card(
        "💨", t("cli.live.wind"),
        f"{wind_spd:.0f} km/h" if wind_spd is not None else "—",
        t("pulse.wind.sub"),
        status_color=wind_color,
    ), unsafe_allow_html=True)

with live_cols[3]:
    pm_color = ("#C0392B" if pm25 is not None and pm25 > 35
                else "#F59E0B" if pm25 is not None and pm25 > 25
                else "#007A6E")
    st.markdown(live_card(
        "🫁", t("cli.live.pm25"),
        f"{pm25:.1f} µg/m³" if pm25 is not None else "—",
        t("pulse.pm25.sub"),
        status_color=pm_color,
    ), unsafe_allow_html=True)

st.caption(t("cli.live.source"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: WEATHER FORECAST
# ─────────────────────────────────────────────────────────────────────────────
if forecast:
    st.markdown(section_header(t("cli.sec.forecast"), color=MD_TEAL), unsafe_allow_html=True)
    fc_cols = st.columns(min(len(forecast), 4))
    for i, fc in enumerate(forecast[:4]):
        with fc_cols[i]:
            hi  = f"{fc['temp_max']:.0f}°C" if fc.get("temp_max") is not None else "—"
            lo  = f"{fc['temp_min']:.0f}°C" if fc.get("temp_min") is not None else "—"
            ico = _cond_icon(fc.get("condition"))
            lbl = _day_label(fc["date"])
            cond_label = (fc.get("condition") or "").replace("-", " ").title()
            st.markdown(f"""
<div style="background:#fff;border-radius:14px;padding:16px 12px;text-align:center;
            box-shadow:0 2px 12px rgba(0,0,0,0.07);border-top:3px solid {MD_TEAL};">
  <div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;
              letter-spacing:0.08em;">{lbl}</div>
  <div style="font-size:2rem;margin:8px 0;">{ico}</div>
  <div style="font-size:0.7rem;color:#64748b;margin-bottom:8px;">{cond_label}</div>
  <div style="font-size:1rem;font-weight:800;color:#1A1A1A;">{hi}</div>
  <div style="font-size:0.82rem;color:#94a3b8;">{lo}</div>
</div>
""", unsafe_allow_html=True)
    st.caption(t("cli.forecast.source"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: RECENT 14-DAY WEATHER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.14day"), color=MD_TEAL), unsafe_allow_html=True)

try:
    # Try live BrightSky data first; fall back to static DWD file
    df_d = fetch_recent_daily_weather(14)
    if df_d.empty:
        df_d = df_daily.copy()
        if "date" in df_d.columns:
            df_d["date"] = pd.to_datetime(df_d["date"], errors="coerce")
        elif "MESS_DATUM" in df_d.columns:
            df_d["date"] = pd.to_datetime(df_d["MESS_DATUM"].astype(str), format="%Y%m%d", errors="coerce")
        df_d = df_d[df_d["TMK"].notna()].sort_values("date").tail(14)

    week_l, week_r = st.columns(2)

    with week_l:
        st.caption(t("cli.cap.recent.temp"))
        fig_temp = go.Figure()
        # Filled band: min to max
        fig_temp.add_trace(go.Scatter(
            x=pd.concat([df_d["date"], df_d["date"][::-1]]),
            y=pd.concat([df_d["TXK"], df_d["TNK"][::-1]]),
            fill="toself",
            fillcolor=MD_TEAL + "30",
            line=dict(color="rgba(0,0,0,0)"),
            name=t("cli.live.temp"),
            showlegend=True,
            hoverinfo="skip",
        ))
        # Mean temperature line
        fig_temp.add_trace(go.Scatter(
            x=df_d["date"], y=df_d["TMK"],
            mode="lines+markers",
            name=t("common.long_mean"),
            line=dict(color=MD_TEAL, width=2),
            marker=dict(size=5),
            hovertemplate="%{x|%d %b}: %{y:.1f} °C<extra>Mean</extra>",
        ))
        fig_temp.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis_title=t("cli.live.temp") + " (°C)",
            xaxis_tickformat="%d %b",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=50, r=10, t=20, b=60),
            height=280,
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with week_r:
        st.caption(t("cli.cap.recent.prec"))
        df_d_prec = df_d[df_d["RSK"].notna()]
        fig_prec = go.Figure(go.Bar(
            x=df_d_prec["date"], y=df_d_prec["RSK"],
            marker_color=MD_BLUE,
            hovertemplate="%{x|%d %b}: %{y:.1f} mm<extra></extra>",
            name=t("cli.sec.prec"),
        ))
        fig_prec.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis_title=t("cli.sec.prec").replace(" (Heatmap)", "") + " (mm)",
            xaxis_tickformat="%d %b",
            margin=dict(l=50, r=10, t=20, b=60),
            height=280,
        )
        st.plotly_chart(fig_prec, use_container_width=True)

    st.caption(t("cli.source.dwd"))
except Exception as e:
    st.info(t("cli.err.recent", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: MONTHLY CLIMATE PROFILE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.monthly"), color=MD_TEAL), unsafe_allow_html=True)

try:
    df_kiss_m = load_kiss("wetter/witterungsverhaeltnisse-monatlich.json")
    # Identify temperature and precipitation columns
    temp_col  = next((c for c in df_kiss_m.columns if "monatsmittel" in c.lower() and "luft" in c.lower()), None)
    prec_col  = next((c for c in df_kiss_m.columns if "niederschlag" in c.lower() and "summe" in c.lower()), None)
    hum_col   = next((c for c in df_kiss_m.columns if "feuchtigkeit" in c.lower() or "luftfeuchtigkeit" in c.lower()), None)

    if temp_col and "Jahr" in df_kiss_m.columns and "Monat" in df_kiss_m.columns:
        df_kiss_m["Jahr"]  = pd.to_numeric(df_kiss_m["Jahr"],  errors="coerce")
        df_kiss_m["Monat"] = pd.to_numeric(df_kiss_m["Monat"], errors="coerce")
        df_kiss_m = df_kiss_m.dropna(subset=["Jahr", "Monat"])
        df_kiss_m[temp_col] = pd.to_numeric(df_kiss_m[temp_col], errors="coerce")

        latest_yr = int(df_kiss_m["Jahr"].max())
        df_this   = df_kiss_m[df_kiss_m["Jahr"] == latest_yr].sort_values("Monat")
        # Long-term monthly mean (1990–)
        df_lt = (
            df_kiss_m[df_kiss_m["Jahr"] >= 1990]
            .groupby("Monat")[temp_col]
            .mean()
            .reset_index()
            .rename(columns={temp_col: "LT_mean"})
        )

        month_nums = list(range(1, 13))
        month_abbr = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

        prof_l, prof_r = st.columns(2)

        with prof_l:
            st.caption(t("cli.cap.month.temp", year=latest_yr))
            fig_mptemp = go.Figure()
            fig_mptemp.add_trace(go.Bar(
                x=[month_abbr[int(r["Monat"])-1] for _, r in df_this.iterrows()],
                y=df_this[temp_col].tolist(),
                name=str(latest_yr),
                marker_color=MD_RED,
                opacity=0.8,
                hovertemplate="%{x}: %{y:.1f} °C<extra></extra>",
            ))
            fig_mptemp.add_trace(go.Scatter(
                x=[month_abbr[int(r["Monat"])-1] for _, r in df_lt.iterrows()],
                y=df_lt["LT_mean"].tolist(),
                mode="lines+markers",
                name=t("common.long_mean"),
                line=dict(color="#64748b", width=2, dash="dot"),
                hovertemplate="%{x}: %{y:.1f} °C long-term<extra></extra>",
            ))
            fig_mptemp.update_layout(
                template=PLOTLY_TEMPLATE,
                yaxis_title="°C",
                legend=dict(orientation="h", y=-0.25),
                margin=dict(l=40, r=10, t=20, b=60),
                height=300,
            )
            st.plotly_chart(fig_mptemp, use_container_width=True)

        with prof_r:
            if prec_col:
                df_kiss_m[prec_col] = pd.to_numeric(df_kiss_m[prec_col], errors="coerce")
                df_this_p = df_kiss_m[df_kiss_m["Jahr"] == latest_yr].sort_values("Monat")
                df_lt_p   = (
                    df_kiss_m[df_kiss_m["Jahr"] >= 1990]
                    .groupby("Monat")[prec_col]
                    .mean()
                    .reset_index()
                    .rename(columns={prec_col: "LT_prec"})
                )
                st.caption(t("cli.cap.month.prec", year=latest_yr))
                fig_mpprec = go.Figure()
                fig_mpprec.add_trace(go.Bar(
                    x=[month_abbr[int(r["Monat"])-1] for _, r in df_this_p.iterrows()],
                    y=df_this_p[prec_col].tolist(),
                    name=str(latest_yr),
                    marker_color=MD_BLUE,
                    opacity=0.8,
                    hovertemplate="%{x}: %{y:.0f} mm<extra></extra>",
                ))
                fig_mpprec.add_trace(go.Scatter(
                    x=[month_abbr[int(r["Monat"])-1] for _, r in df_lt_p.iterrows()],
                    y=df_lt_p["LT_prec"].tolist(),
                    mode="lines+markers",
                    name=t("common.long_mean"),
                    line=dict(color="#64748b", width=2, dash="dot"),
                    hovertemplate="%{x}: %{y:.0f} mm long-term<extra></extra>",
                ))
                fig_mpprec.update_layout(
                    template=PLOTLY_TEMPLATE,
                    yaxis_title=t("cli.sec.prec").replace(" (Heatmap)", "") + " (mm)",
                    legend=dict(orientation="h", y=-0.25),
                    margin=dict(l=40, r=10, t=20, b=60),
                    height=300,
                )
                st.plotly_chart(fig_mpprec, use_container_width=True)
            else:
                st.info(t("cli.month.info.no_prec"))

        st.markdown(insight_box(
            t("cli.insight.monthly", year=latest_yr)
        ), unsafe_allow_html=True)
        st.caption(t("cli.source.monthly"))
    else:
        st.info(t("cli.month.info.none"))
except Exception as e:
    st.info(t("cli.month.info.error", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: LONG-TERM TEMPERATURE ANOMALY (existing)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.anomaly"), color=MD_TEAL), unsafe_allow_html=True)
st.caption(t("cli.cap.anomaly"))

year_min, year_max = st.slider(
    t("common.year_range"), int(df_monthly["year"].min()), int(df_monthly["year"].max()),
    value=(1950, int(df_monthly["year"].max())), key="temp_years",
)

df_temp = df_monthly[df_monthly["MO_TT"].notna()].copy()
baseline = df_temp[(df_temp["year"] >= 1961) & (df_temp["year"] <= 1990)]["MO_TT"].mean()
df_temp["anomaly"] = df_temp["MO_TT"] - baseline

df_annual = (
    df_temp.groupby("year")["MO_TT"].mean().reset_index()
    .rename(columns={"MO_TT": "annual_mean"})
)
df_annual["anomaly"]   = df_annual["annual_mean"] - baseline
df_annual["rolling10"] = df_annual["anomaly"].rolling(10, center=True).mean()
df_plot = df_annual[(df_annual["year"] >= year_min) & (df_annual["year"] <= year_max)]

fig_anom = go.Figure()
colours = [MD_RED if v >= 0 else MD_BLUE for v in df_plot["anomaly"]]
fig_anom.add_trace(go.Bar(
    x=df_plot["year"], y=df_plot["anomaly"],
    marker_color=colours, name=t("cli.trace.anomaly"),
    hovertemplate="%{x}: %{y:+.2f} °C<extra></extra>",
))
fig_anom.add_trace(go.Scatter(
    x=df_plot["year"], y=df_plot["rolling10"],
    mode="lines", name=t("cli.trace.rolling"),
    line=dict(color="black", width=2, dash="dot"),
))
fig_anom.add_hline(y=0, line_color="grey", line_width=1)
fig_anom.update_layout(
    template=PLOTLY_TEMPLATE,
    yaxis_title=t("cli.axis.temp_anomaly"),
    xaxis_title=t("common.year"),
    legend=dict(orientation="h", y=-0.15),
    margin=dict(l=40, r=20, t=30, b=60),
)
st.plotly_chart(fig_anom, use_container_width=True)
st.markdown(insight_box(
    t("cli.insight.anomaly", baseline=baseline)
), unsafe_allow_html=True)
st.caption(t("cli.cap.baseline", baseline=baseline))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5b: HISTORICAL ANNUAL MEANS — TEMPERATURE & PRESSURE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.histmean"), color=MD_TEAL), unsafe_allow_html=True)

hist_l, hist_r = st.columns(2)

with hist_l:
    try:
        df_ann_temp = (
            df_monthly[df_monthly["MO_TT"].notna()]
            .groupby("year")["MO_TT"].mean()
            .reset_index()
            .rename(columns={"MO_TT": "ann_temp"})
            .sort_values("year")
        )
        st.caption(t("cli.cap.annual_temp"))
        fig_ann_t = go.Figure(go.Scatter(
            x=df_ann_temp["year"], y=df_ann_temp["ann_temp"],
            mode="lines+markers",
            line=dict(color=MD_RED, width=2),
            marker=dict(size=4),
            hovertemplate="%{x}: %{y:.1f} °C<extra></extra>",
        ))
        fig_ann_t.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis_title="°C",
            margin=dict(l=50, r=10, t=20, b=40),
            height=280,
        )
        st.plotly_chart(fig_ann_t, use_container_width=True)
    except Exception:
        st.info(t("cli.info.annual_temp"))

with hist_r:
    try:
        _pp_col = next((c for c in df_monthly.columns if "PP" in c.upper() or "druck" in c.lower()), None)
        if _pp_col:
            df_ann_p = (
                df_monthly[df_monthly[_pp_col].notna()]
                .groupby("year")[_pp_col].mean()
                .reset_index()
                .rename(columns={_pp_col: "ann_pressure"})
                .sort_values("year")
            )
            st.caption(t("cli.cap.annual_pressure"))
            fig_ann_p = go.Figure(go.Scatter(
                x=df_ann_p["year"], y=df_ann_p["ann_pressure"],
                mode="lines+markers",
                line=dict(color=MD_BLUE, width=2),
                marker=dict(size=4),
                hovertemplate="%{x}: %{y:.1f} hPa<extra></extra>",
            ))
            fig_ann_p.update_layout(
                template=PLOTLY_TEMPLATE,
                yaxis_title="hPa",
                margin=dict(l=50, r=10, t=20, b=40),
                height=280,
            )
            st.plotly_chart(fig_ann_p, use_container_width=True)
        else:
            st.info(t("cli.info.pressure_col"))
    except Exception:
        st.info(t("cli.info.pressure"))

st.caption(t("cli.source.annual"))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: PRECIPITATION HEATMAP (existing)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.prec"), color=MD_TEAL), unsafe_allow_html=True)
st.caption(t("cli.cap.prec"))

n_years = st.selectbox(t("common.show_last_n"), [20, 30, 50, t("common.all")], index=0, key="prec_nyears")
df_prec = df_monthly[df_monthly["MO_RR"].notna()].copy()
if n_years != t("common.all"):
    max_year = int(df_prec["year"].max())
    df_prec  = df_prec[df_prec["year"] >= max_year - int(n_years) + 1]

df_prec["month_name"] = df_prec["month"].map({v: k for k, v in MONTHS_DE.items()})
pivot = df_prec.pivot_table(index="year", columns="month_name", values="MO_RR", aggfunc="mean")
pivot = pivot.reindex(columns=[m for m in MONTHS_DE_ORDER if m in pivot.columns])

fig_heat = heatmap(pivot, title=t("cli.chart.prec_title"), colorscale="Blues", zmin=0,
                   x_label=t("cli.axis.month"), y_label=t("common.year"))
fig_heat.update_layout(margin=dict(l=50, r=20, t=50, b=40))
st.plotly_chart(fig_heat, use_container_width=True)
st.markdown(insight_box(
    t("cli.insight.prec")
), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: SUNSHINE & WIND ANNUAL TRENDS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.sun"), color=MD_TEAL), unsafe_allow_html=True)

try:
    df_ann2 = load_kiss("wetter/witterung-in-magdeburg.json")
    sun_col  = next((c for c in df_ann2.columns if "sonnenschein" in c.lower()), None)
    wind_col = next((c for c in df_ann2.columns if "windgeschwindigkeit" in c.lower()), None)

    if sun_col or wind_col:
        sun_l, sun_r = st.columns(2)

        if sun_col and "Jahr" in df_ann2.columns:
            df_ann2[sun_col]  = pd.to_numeric(df_ann2[sun_col],  errors="coerce")
            df_sun = df_ann2[["Jahr", sun_col]].dropna().sort_values("Jahr")
            with sun_l:
                st.caption(t("cli.cap.sun"))
                fig_sun = go.Figure(go.Bar(
                    x=df_sun["Jahr"], y=df_sun[sun_col],
                    marker_color=MD_ORANGE, opacity=0.85,
                    hovertemplate="%{x}: %{y:.0f} h<extra></extra>",
                ))
                fig_sun.update_layout(
                    template=PLOTLY_TEMPLATE,
                    yaxis_title=t("cli.axis.sun"),
                    margin=dict(l=50, r=10, t=20, b=40),
                    height=280,
                )
                st.plotly_chart(fig_sun, use_container_width=True)

        if wind_col and "Jahr" in df_ann2.columns:
            df_ann2[wind_col] = pd.to_numeric(df_ann2[wind_col], errors="coerce")
            df_wind = df_ann2[["Jahr", wind_col]].dropna().sort_values("Jahr")
            with sun_r:
                st.caption(t("cli.cap.wind"))
                fig_wind = go.Figure(go.Scatter(
                    x=df_wind["Jahr"], y=df_wind[wind_col],
                    mode="lines+markers",
                    line=dict(color=MD_TEAL, width=2),
                    marker=dict(size=6),
                    hovertemplate="%{x}: %{y:.1f} m/s<extra></extra>",
                ))
                fig_wind.update_layout(
                    template=PLOTLY_TEMPLATE,
                    yaxis_title=t("cli.axis.wind"),
                    margin=dict(l=50, r=10, t=20, b=40),
                    height=280,
                )
                st.plotly_chart(fig_wind, use_container_width=True)

        st.caption(t("cli.source.sun"))
    else:
        st.info(t("cli.info.sun_cols"))
except Exception as e:
    st.info(t("cli.info.sun_error", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: AIR POLLUTANTS (existing + live context)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.poll"), color=MD_TEAL), unsafe_allow_html=True)
st.caption(t("cli.cap.poll"))

try:
    df_air = load_kiss("energie-und-umwelt/schadstoffkonzentration-in-der-luft.json")
    rename_map = {}
    for c in df_air.columns:
        cl = c.lower()
        if "stickstoffdioxid" in cl or "no" in cl and "₂" in c:
            rename_map[c] = "NO₂ (µg/m³)"
        elif "ozon" in cl:
            rename_map[c] = "O₃ (µg/m³)"
        elif "schwefeldioxid" in cl:
            rename_map[c] = "SO₂ (µg/m³)"
        elif "feinstaub" in cl or "pm" in cl:
            rename_map[c] = "PM₁₀ (µg/m³)"
    df_air = df_air.rename(columns=rename_map)

    poll_options = [c for c in ["NO₂ (µg/m³)", "O₃ (µg/m³)", "SO₂ (µg/m³)", "PM₁₀ (µg/m³)"]
                    if c in df_air.columns]
    selected = st.multiselect(t("cli.poll.select"), poll_options,
                              default=["NO₂ (µg/m³)", "PM₁₀ (µg/m³)"], key="pollutants")

    if selected:
        df_air_ann = df_air.groupby("Jahr")[selected].mean().reset_index()

        fig_poll = go.Figure()
        colours3 = px.colors.qualitative.Set1
        for i, col in enumerate(selected):
            sub = df_air_ann[df_air_ann[col].notna()]
            fig_poll.add_trace(go.Scatter(
                x=sub["Jahr"], y=sub[col], mode="lines+markers",
                name=col, line=dict(color=colours3[i % len(colours3)]),
                hovertemplate=f"{col}: %{{y:.1f}} µg/m³<extra></extra>",
            ))

        eu_limits = {"NO₂ (µg/m³)": 40, "PM₁₀ (µg/m³)": 40}
        for col, limit in eu_limits.items():
            if col in selected:
                fig_poll.add_hline(y=limit, line_dash="dash", line_color="grey",
                                   annotation_text=t("cli.poll.limit", pollutant=col, limit=limit),
                                   annotation_position="bottom right")

        fig_poll.update_layout(
            template=PLOTLY_TEMPLATE,
            yaxis_title=t("cli.axis.concentration"),
            xaxis_title=t("common.year"),
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=40, r=20, t=30, b=70),
        )
        st.plotly_chart(fig_poll, use_container_width=True)

        st.markdown(insight_box(
            t("cli.insight.poll")
        ), unsafe_allow_html=True)
    else:
        st.info(t("cli.poll.none"))

    # Live PM2.5 context callout
    if pm25 is not None and "PM₁₀ (µg/m³)" in df_air.columns:
        try:
            df_pm_recent = df_air[df_air["PM₁₀ (µg/m³)"].notna()]
            latest_month_pm = float(df_pm_recent["PM₁₀ (µg/m³)"].tail(12).mean())
            pm_status = (t("cli.pm.below") if pm25 < latest_month_pm else t("cli.pm.above"))
            pm_color  = "#007A6E" if pm25 < 25 else ("#F59E0B" if pm25 < 35 else "#C0392B")
            pm_advice = t("cli.pm.good") if pm25 < 25 else t("cli.pm.moderate") if pm25 < 35 else t("cli.pm.poor")
            st.markdown(f"""
<div style="background:#f8fafc;border-left:4px solid {pm_color};border-radius:0 12px 12px 0;
            padding:12px 20px;margin:8px 0;font-size:0.88rem;color:#374151;">
  {t("cli.live_reading", pm25=pm25, status=pm_status, avg=latest_month_pm, advice=pm_advice)}
</div>
""", unsafe_allow_html=True)
        except Exception:
            pass

except Exception as e:
    st.warning(t("cli.warn.air", error=e))

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: GLOBAL CO₂ TREND (MAUNA LOA)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(section_header(t("cli.sec.co2"), color=MD_TEAL), unsafe_allow_html=True)

df_co2 = fetch_co2_trend()
if not df_co2.empty:
    latest_co2 = float(df_co2["mean"].iloc[-1])
    latest_yr  = int(df_co2["year"].iloc[-1])
    fig_co2 = go.Figure(go.Scatter(
        x=df_co2["year"], y=df_co2["mean"],
        mode="lines",
        fill="tozeroy",
        fillcolor=MD_TEAL + "20",
        line=dict(color=MD_TEAL, width=2),
        hovertemplate="%{x}: %{y:.1f} ppm CO₂<extra></extra>",
    ))
    fig_co2.add_annotation(
        x=latest_yr, y=latest_co2,
        text=f"<b>{latest_co2:.1f} ppm ({latest_yr})</b>",
        showarrow=True, arrowhead=2, ax=-60, ay=-30,
        font=dict(size=12, color=MD_RED),
    )
    fig_co2.update_layout(
        template=PLOTLY_TEMPLATE,
        yaxis_title="CO₂ (ppm)",
        xaxis_title=t("common.year"),
        margin=dict(l=50, r=20, t=30, b=40),
    )
    st.plotly_chart(fig_co2, use_container_width=True)
    st.markdown(insight_box(
        t("cli.insight.co2", co2=latest_co2, year=latest_yr)
    ), unsafe_allow_html=True)
    st.caption(t("cli.cap.co2"))
else:
    st.info(t("cli.info.co2"))
