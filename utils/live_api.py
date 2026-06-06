import csv
import io
import os
import zipfile
import requests
import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:  # type: ignore[no-redef]
        return None

from utils.constants import LAT, LON

load_dotenv()

def _load_custom_env() -> None:
    """Parse non-standard .env lines of the form 'API key name : KEY' / 'value  : VAL'."""
    env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    try:
        with open(env_path) as _f:
            lines = [l.rstrip("\n") for l in _f if l.strip()]
        i = 0
        while i < len(lines) - 1:
            if ":" in lines[i] and ":" in lines[i + 1]:
                key = lines[i].split(":", 1)[1].strip()
                val = lines[i + 1].split(":", 1)[1].strip()
                if key and val and not os.getenv(key):
                    os.environ[key] = val
                i += 2
            else:
                i += 1
    except Exception:
        pass

_load_custom_env()

_HAFAS_KEY  = os.getenv("NASA_HAFAS_API_KEY", "")
_HAFAS_BASE = os.getenv("HAFAS_BASE_URL", "https://nasa.demo.hafas.de/restproxy/2.49")
_GTFS_ZIP   = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "data",
    "OEV-Daten_NASA_GmbH", "GTFS", "gtfs_mvb_std_kn.zip",
))


@st.cache_data(ttl=600)
def fetch_weather() -> dict | None:
    try:
        r = requests.get(
            "https://api.brightsky.dev/current_weather",
            params={"lat": LAT, "lon": LON},
            timeout=5,
        )
        r.raise_for_status()
        return r.json().get("weather", {})
    except Exception:
        return None


@st.cache_data(ttl=600)
def fetch_elbe_level() -> dict | None:
    url = (
        "https://www.pegelonline.wsv.de/webservices/rest-api/v2"
        "/stations/MAGDEBURG-STROMBR%C3%9CCKE/W/currentmeasurement.json"
    )
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=600)
def fetch_air_quality() -> float | None:
    url = f"https://data.sensor.community/airrohr/v1/filter/area={LAT},{LON},10"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        sensors = r.json()
        pm25_values = []
        for s in sensors:
            for sv in s.get("sensordatavalues", []):
                if sv.get("value_type") == "P2":
                    try:
                        pm25_values.append(float(sv["value"]))
                    except (ValueError, TypeError):
                        pass
        return round(sum(pm25_values) / len(pm25_values), 1) if pm25_values else None
    except Exception:
        return None


@st.cache_data(ttl=1800)
def fetch_weather_forecast() -> list:
    """Returns list of daily forecast dicts for the next 3 days from Bright Sky."""
    try:
        today = datetime.now().date()
        end   = today + timedelta(days=3)
        r = requests.get(
            "https://api.brightsky.dev/weather",
            params={"lat": LAT, "lon": LON,
                    "date": today.isoformat(),
                    "last_date": end.isoformat()},
            timeout=8,
        )
        r.raise_for_status()
        hours = r.json().get("weather", [])
        by_day = defaultdict(list)
        for h in hours:
            day = (h.get("timestamp") or "")[:10]
            if day:
                by_day[day].append(h)
        result = []
        for day_str in sorted(by_day.keys()):
            hs = by_day[day_str]
            temps = [h["temperature"] for h in hs if h.get("temperature") is not None]
            conds = [h.get("condition") or "" for h in hs if h.get("condition")]
            result.append({
                "date": day_str,
                "temp_max": max(temps) if temps else None,
                "temp_min": min(temps) if temps else None,
                "condition": max(set(conds), key=conds.count) if conds else "dry",
            })
        return result
    except Exception:
        return []


@st.cache_data(ttl=3600)
def fetch_city_news() -> list:
    """Tries Magdeburg city RSS feeds. Returns list of dicts or [] on failure."""
    feeds = [
        "https://www.magdeburg.de/RSS/",
        "https://www.magdeburg.de/rss.xml",
        "https://www.magdeburg.de/Start/B%C3%BCrger-Stadt/Newsroom/Pressemitteilungen?format=feed&type=rss",
    ]
    for url in feeds:
        try:
            r = requests.get(url, timeout=6,
                             headers={"User-Agent": "Mozilla/5.0 (compatible)"})
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            channel = root.find("channel") or root
            items = []
            for item in channel.findall("item")[:5]:
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link")  or "").strip()
                desc  = (item.findtext("description") or "").strip()
                pub   = (item.findtext("pubDate") or "")[:16].strip()
                if title:
                    items.append({"title": title[:90], "link": link,
                                  "summary": desc[:130] if desc else "", "date": pub})
            if items:
                return items
        except Exception:
            continue
    return []


@st.cache_data(ttl=86400, show_spinner=False)
def load_mvb_stops() -> list:
    """Load MVB stop list from static GTFS zip. Deduplicates by name, sorted A–Z."""
    try:
        with zipfile.ZipFile(_GTFS_ZIP) as z:
            with z.open("stops.txt") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                seen, stops = set(), []
                for row in reader:
                    name = row.get("stop_name", "").strip().strip('"')
                    sid  = row.get("stop_id",   "").strip().strip('"')
                    lat  = row.get("stop_lat",  "").strip().strip('"')
                    lon  = row.get("stop_lon",  "").strip().strip('"')
                    if name and sid and name not in seen:
                        seen.add(name)
                        stops.append({
                            "name":   name,
                            "ext_id": sid,
                            "lat":    float(lat) if lat else None,
                            "lon":    float(lon) if lon else None,
                        })
                return sorted(stops, key=lambda x: x["name"])
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_departures(ext_id: str, max_journeys: int = 12) -> list:
    """Fetch live departures from HAFAS departureBoard for a given stop extId."""
    if not _HAFAS_KEY:
        return []
    try:
        now = datetime.now()
        r = requests.get(
            f"{_HAFAS_BASE}/departureBoard",
            params={
                "extId":       ext_id,
                "date":        now.strftime("%Y%m%d"),
                "time":        now.strftime("%H%M"),
                "maxJourneys": max_journeys,
                "format":      "json",
                "accessId":    _HAFAS_KEY,
            },
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if "errorCode" in data:
            return []
        departures = []
        for dep in data.get("Departure", []):
            sched = (dep.get("time") or "")[:5]
            rt    = (dep.get("rtTime") or "")[:5]
            delay_min = None
            if rt and sched and rt != sched:
                try:
                    sh, sm = map(int, sched.split(":"))
                    rh, rm = map(int, rt.split(":"))
                    delay_min = (rh * 60 + rm) - (sh * 60 + sm)
                    if delay_min < -120:
                        delay_min += 1440
                except ValueError:
                    pass
            departures.append({
                "line":      dep.get("name", ""),
                "direction": dep.get("direction", ""),
                "time":      sched,
                "rt_time":   rt,
                "delay_min": delay_min,
                "platform":  dep.get("platform") or dep.get("track") or "",
                "cancelled": bool(dep.get("cancelled", False)),
            })
        return departures
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def fetch_uv_index() -> float | None:
    """Fetch current UV index from Open-Meteo (free, no key required)."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": LAT, "longitude": LON, "current": "uv_index",
                    "timezone": "Europe/Berlin"},
            timeout=6,
        )
        r.raise_for_status()
        return r.json().get("current", {}).get("uv_index")
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_recent_daily_weather(days: int = 14):
    """Fetch recent daily weather from BrightSky, aggregated from hourly data."""
    import pandas as pd
    end   = datetime.now().date()
    start = end - timedelta(days=days)
    try:
        r = requests.get(
            "https://api.brightsky.dev/weather",
            params={"lat": LAT, "lon": LON,
                    "date": start.isoformat(), "last_date": end.isoformat()},
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json().get("weather", [])
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["timestamp"].str[:10])
        daily = df.groupby("date").agg(
            TMK=("temperature", "mean"),
            TXK=("temperature", "max"),
            TNK=("temperature", "min"),
            RSK=("precipitation", "sum"),
        ).reset_index()
        return daily
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_co2_trend():
    """Fetch annual mean CO₂ from NOAA Mauna Loa Observatory (global reference)."""
    import pandas as pd
    try:
        r = requests.get(
            "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
            timeout=10,
        )
        r.raise_for_status()
        lines = [ln for ln in r.text.splitlines() if not ln.strip().startswith("#") and ln.strip()]
        from io import StringIO
        df = pd.read_csv(StringIO("\n".join(lines)), header=None,
                         names=["year", "mean", "unc"])
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["mean"] = pd.to_numeric(df["mean"], errors="coerce")
        return df.dropna(subset=["year", "mean"]).sort_values("year")
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_service_disruptions() -> list:
    """Fetch active service disruptions from HAFAS HIM search."""
    if not _HAFAS_KEY:
        return []
    try:
        today = datetime.now().strftime("%Y%m%d")
        r = requests.get(
            f"{_HAFAS_BASE}/himsearch",
            params={
                "dateB":    today,
                "dateE":    today,
                "format":   "json",
                "accessId": _HAFAS_KEY,
            },
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if "errorCode" in data:
            return []
        result = []
        for him in data.get("him", [])[:5]:
            head = him.get("head") or him.get("hd") or "Service Notice"
            text = him.get("text") or him.get("tx") or ""
            impacts = him.get("impactL") or []
            line_names = [
                i.get("name", "") for i in impacts
                if i.get("type") == "LINE" and i.get("name")
            ]
            result.append({
                "head":    str(head)[:80],
                "text":    str(text)[:200],
                "affects": ", ".join(line_names[:4]),
            })
        return result
    except Exception:
        return []
