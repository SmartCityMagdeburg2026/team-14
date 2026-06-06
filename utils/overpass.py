"""Cached OpenStreetMap Overpass API fetchers for Magdeburg POI layers."""

import requests
import streamlit as st

# Magdeburg bounding box: south, west, north, east
_BBOX = "52.05,11.55,52.20,11.75"
_URL  = "https://overpass-api.de/api/interpreter"
_TIMEOUT = 20


def _query(ql: str) -> list:
    """POST an Overpass QL query, return parsed elements list."""
    try:
        r = requests.post(_URL, data={"data": ql}, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json().get("elements", [])
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_parking() -> list:
    """OSM parking nodes and way-centres in Magdeburg."""
    ql = f"""
[out:json][timeout:20];
(
  node["amenity"="parking"]({_BBOX});
  way["amenity"="parking"]({_BBOX});
);
out center tags;
"""
    items = []
    for el in _query(ql):
        tags = el.get("tags", {})
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            c = el.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
        if lat is None or lon is None:
            continue
        capacity = tags.get("capacity", "")
        name     = tags.get("name", tags.get("access", "Public parking"))
        p_type   = tags.get("parking", "")
        items.append({
            "lat": lat, "lon": lon,
            "name": name or "Parking",
            "capacity": capacity,
            "type": p_type,
        })
    return items


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_charging() -> list:
    """OSM EV charging stations in Magdeburg."""
    ql = f"""
[out:json][timeout:20];
node["amenity"="charging_station"]({_BBOX});
out;
"""
    items = []
    for el in _query(ql):
        tags = el.get("tags", {})
        lat, lon = el.get("lat"), el.get("lon")
        if lat is None or lon is None:
            continue
        sockets  = tags.get("capacity", tags.get("socket:type2:output", ""))
        operator = tags.get("operator", tags.get("brand", ""))
        name     = tags.get("name", operator or "EV Charging Station")
        items.append({
            "lat": lat, "lon": lon,
            "name": name,
            "operator": operator,
            "sockets": str(sockets),
            "fee": tags.get("fee", ""),
        })
    return items


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_transit_stops() -> list:
    """OSM bus and tram stops in Magdeburg."""
    ql = f"""
[out:json][timeout:20];
(
  node["highway"="bus_stop"]({_BBOX});
  node["railway"="tram_stop"]({_BBOX});
  node["public_transport"="stop_position"]["bus"="yes"]({_BBOX});
  node["public_transport"="stop_position"]["tram"="yes"]({_BBOX});
);
out;
"""
    seen  = set()
    items = []
    for el in _query(ql):
        tags = el.get("tags", {})
        lat, lon = el.get("lat"), el.get("lon")
        if lat is None or lon is None:
            continue
        name = tags.get("name", "Stop")
        key  = (round(lat, 4), round(lon, 4), name)
        if key in seen:
            continue
        seen.add(key)
        is_tram = (tags.get("railway") == "tram_stop"
                   or tags.get("tram") == "yes")
        items.append({
            "lat": lat, "lon": lon,
            "name": name,
            "type": "tram" if is_tram else "bus",
            "ref": tags.get("ref", ""),
        })
    return items


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_restaurants() -> list:
    """OSM restaurants, cafés, bars and fast-food outlets in Magdeburg."""
    ql = f"""
[out:json][timeout:25];
(
  node["amenity"~"^(restaurant|cafe|bar|fast_food|food_court)$"]({_BBOX});
  way["amenity"~"^(restaurant|cafe|bar|fast_food|food_court)$"]({_BBOX});
);
out center tags;
"""
    items = []
    for el in _query(ql):
        tags = el.get("tags", {})
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            c = el.get("center", {})
            lat, lon = c.get("lat"), c.get("lon")
        if lat is None or lon is None:
            continue
        items.append({
            "lat": lat, "lon": lon,
            "name": tags.get("name", ""),
            "amenity": tags.get("amenity", "restaurant"),
            "cuisine": tags.get("cuisine", ""),
        })
    return items
