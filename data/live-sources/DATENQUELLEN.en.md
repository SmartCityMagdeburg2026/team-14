# Live data sources — Smart City Hackathon Magdeburg

> *Deutsche Fassung:* [DATENQUELLEN.md](./DATENQUELLEN.md).

This folder complements the **static, ready-to-use datasets** under
[`../data/`](../data/) with **live sources**: APIs you call at runtime from your
app (weather, river levels, real-time transit, air quality, parking …). It lists
endpoints, response formats and **self-contained code examples** to integrate
them — independent of framework or language.

> Use only public / open-data sources with attribution and **no personal data**
> (see the notes in [`../README.md`](../README.md)).

## Three integration patterns

| # | Pattern | When | Examples here |
|---|---------|------|---------------|
| 1 | **Browser fetch** directly | API sends CORS headers | Weather, level, air, GovData |
| 2 | **Preprocess** → static JSON | large / strictly rate-limited / rarely changes | OSM/Overpass, GTFS schedule |
| 3 | **Server proxy** via your backend | API without CORS headers | GTFS-RT |

Pattern 2 is exactly what the finished datasets under [`../data/`](../data/) are —
fetched/converted once and committed as JSON (e.g. `../data/sensor-data/convert.py`).
For pattern 3 this repo already ships a backend: the FastAPI starter under
[`../deploy/`](../deploy/) — that's where you add a proxy endpoint (example below).

**Magdeburg anchor** (sensible query centre): `{ lat: 52.1205, lon: 11.6276 }`.
**Bounding box** of the city area: `52.05, 11.55, 52.20, 11.75` (S,W,N,E).

## Overview

| Source | Pattern | CORS | Endpoint (short) |
|--------|---------|------|------------------|
| Bright Sky / DWD — weather | 1 | ✅ | `api.brightsky.dev/current_weather` |
| PEGELONLINE / WSV — Elbe level | 1 | ✅ | `pegelonline.wsv.de/webservices/rest-api/v2` |
| Sensor.Community — air quality | 1 | ✅ | `data.sensor.community/airrohr/v1/filter` |
| GovData CKAN — open datasets | 1 | ✅ | `ckan.govdata.de/api/3/action/package_search` |
| OSM tiles + LVermGeo WMS — maps | 1 | n/a¹ | `tile.openstreetmap.org` · `geodatenportal.sachsen-anhalt.de` |
| OpenStreetMap via Overpass | 2 | ✅ | `overpass-api.de/api/interpreter` |
| GTFS schedule (gtfs.de) | 2 | ✅ | `download.gtfs.de/germany/nv_free/latest.zip` |
| GTFS-RT — real-time transit | 3 | ❌ | `realtime.gtfs.de/realtime-free.pb` |

¹ Tile/WMS layers are `<img>` requests, not `fetch` → CORS does not apply.

---

## 1 · Browser-side APIs

Directly via `fetch` from the browser. No proxy, no API key.

### Bright Sky / DWD — weather

- **Endpoint**: `https://api.brightsky.dev/current_weather?lat=<lat>&lon=<lon>`
- **Docs**: <https://brightsky.dev/docs/> · Auth: none · Rate limit: fair use

```js
const md = { lat: 52.1205, lon: 11.6276 };
const url = `https://api.brightsky.dev/current_weather?lat=${md.lat}&lon=${md.lon}`;
const { weather } = await fetch(url).then(r => r.json());
// weather.temperature (°C), weather.wind_speed (km/h),
// weather.precipitation (mm), weather.cloud_cover (%), weather.condition
```

### PEGELONLINE / WSV — Elbe water level

- **Base**: `https://www.pegelonline.wsv.de/webservices/rest-api/v2`
- **Docs**: <https://pegelonline.wsv.de/webservice/dokuRestapi> · Auth/rate limit: none

```js
const base = 'https://www.pegelonline.wsv.de/webservices/rest-api/v2';
const STATION = 'MAGDEBURG-STROMBR%C3%9CCKE';            // keep URL-encoded!

// current value (water level in cm):
const now = await fetch(`${base}/stations/${STATION}/W/currentmeasurement.json`)
  .then(r => r.json());                                   // → { timestamp, value }

// history (ISO-8601 duration: P1D = 24 h, P7D = 7 days):
const series = await fetch(`${base}/stations/${STATION}/W/measurements.json?start=P7D`)
  .then(r => r.json());                                   // → [ { timestamp, value }, … ]
```

### Sensor.Community — air quality (citizen sensor network)

- **Endpoint**: `https://data.sensor.community/airrohr/v1/filter/area=<lat>,<lon>,<radius_km>`
- **Docs**: <https://github.com/opendata-stuttgart/meta/wiki/APIs> · max ~1 req / 5 min

```js
const r = await fetch('https://data.sensor.community/airrohr/v1/filter/area=52.1205,11.6276,10')
  .then(r => r.json());
// Per entry: sensordatavalues[] with value_type 'P1' = PM10, 'P2' = PM2.5 (µg/m³).
// Average over several sensors. WHO 24h guideline values: PM10 45, PM2.5 15 µg/m³.
```

### GovData CKAN — open datasets (catalogue search)

- **Endpoint**: `https://ckan.govdata.de/api/3/action/package_search`
- **Docs**: <https://docs.ckan.org/en/latest/api/>

```js
const p = new URLSearchParams({ q: 'Magdeburg', rows: 10, sort: 'metadata_modified desc' });
const d = await fetch(`https://ckan.govdata.de/api/3/action/package_search?${p}`)
  .then(r => r.json());
const datasets = d.result.results;            // d.result.count = total hits
// Filter via fq=, e.g. fq=res_format:CSV  or  fq=organization:magdeburg
```

### Map base layers

Usable as tile/WMS layers in any mapping library (Leaflet, MapLibre, OpenLayers …) —
no proxy needed:

- **OSM tiles**: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
- **LVermGeo Saxony-Anhalt** orthophoto WMS (open data):
  `https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_OpenData_WMS/guest`,
  layer `lsa_lvermgeo_dop_020`.

---

## 2 · Preprocessed sources

Fetch large or strictly limited sources **once**, filter them, and commit the
result as JSON — your app never hits the API at runtime. (This is exactly how the
datasets under [`../data/`](../data/) were produced.)

### OpenStreetMap via Overpass

- **Endpoint**: `https://overpass-api.de/api/interpreter` (fallbacks:
  `overpass.kumi.systems`, `overpass.private.coffee`)
- **Docs**: <https://wiki.openstreetmap.org/wiki/Overpass_API> ·
  query builder: <https://overpass-turbo.eu/>
- **Why preprocess?** strictly rate-limited (~2 req/s), data rarely changes.

Example: fetch charging stations, tram stops and bicycle parking in the city area
and save as JSON (Python, just `requests`):

```python
import json, requests

BBOX = "52.05,11.55,52.20,11.75"      # S,W,N,E
query = f"""
[out:json][timeout:60];
(
  nwr["amenity"="charging_station"]({BBOX});
  nwr["railway"="tram_stop"]({BBOX});
  nwr["amenity"="bicycle_parking"]({BBOX});
);
out center tags;
"""
r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=90)
elements = r.json()["elements"]       # per element: lat/lon (or center.lat/lon) + tags
json.dump(elements, open("osm-poi.json", "w"), ensure_ascii=False, indent=2)
```

### GTFS schedule (gtfs.de)

- **Source**: `https://download.gtfs.de/germany/nv_free/latest.zip` · licence CC-BY 4.0
- **Docs**: <https://gtfs.org/> · **Why preprocess?** ~200 MB ZIP,
  `stop_times.txt` >500 MB unzipped — not for the browser.

Approach: load the ZIP server-side, filter to the Magdeburg bbox (stops from
`stops.txt`, trips from `trips.txt`/`stop_times.txt`) and write a lean JSON.
`route_type`: `0` tram · `1` subway · `2` rail · `3` bus · `4` ferry · `11`
trolleybus. For "running today?" check the weekday **and** validity period from
`calendar.txt` (`YYYYMMDD`, 0 = Monday).

---

## 3 · Server-proxy APIs

These backends send **no** CORS headers — a direct browser `fetch` fails. Solution:
forward them **same-origin** through your own backend. The FastAPI starter under
[`../deploy/`](../deploy/) is a direct fit.

### Adding a proxy to the FastAPI starter

General pattern — forward a CORS-less JSON API **same-origin**. Add to
`deploy/app/main.py` (`httpx` is part of `fastapi[standard]`):

```python
import httpx
from fastapi import Request, Response

UPSTREAM = "https://example-api.invalid"     # target API without CORS headers

@app.get("/api/proxy/{path:path}")
async def proxy(path: str, request: Request):
    async with httpx.AsyncClient(timeout=10) as client:
        up = await client.get(f"{UPSTREAM}/{path}", params=request.query_params,
                              headers={"Accept": "application/json"})
    return Response(content=up.content, status_code=up.status_code,
                    media_type="application/json")
```

The browser then calls `/api/proxy/…` **same-origin** instead of contacting the
foreign API directly.

### GTFS-RT — real-time transit

- **Feed**: `https://realtime.gtfs.de/realtime-free.pb` (Protocol Buffers, all of DE)
- **Docs**: <https://gtfs.org/realtime/>
- **Why server-side?** Protobuf + Germany-wide data volume are nothing for the
  browser → decode in the backend, filter to Magdeburg, serve as JSON.
- **Note**: the `nv_free` feed contains **only `TripUpdate`s (delays), no
  `VehiclePosition`s** — you'd have to interpolate vehicle positions from the
  schedule (pattern 2) between stops.

Endpoint in the FastAPI starter (additionally install `gtfs-realtime-bindings` +
`protobuf`):

```python
import httpx
from google.transit import gtfs_realtime_pb2

@app.get("/api/gtfs-rt.json")
async def gtfs_rt():
    async with httpx.AsyncClient(timeout=15) as client:
        raw = (await client.get("https://realtime.gtfs.de/realtime-free.pb")).content
    feed = gtfs_realtime_pb2.FeedMessage(); feed.ParseFromString(raw)
    updates = []
    for e in feed.entity:
        if not e.HasField("trip_update"):
            continue
        tu = e.trip_update
        updates.append({
            "tripId": tu.trip.trip_id,
            "stops": [{"stopId": s.stop_id, "delay": s.arrival.delay}
                      for s in tu.stop_time_update],
        })
    return {"updates": updates}   # filter to Magdeburg stop_ids from the GTFS schedule
```

---

## Recurring patterns (framework-neutral)

**Fetch with timeout** (abort hanging requests):

```js
async function getJSON(url, ms = 5000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } finally { clearTimeout(t); }
}
```

**Polling** (live sources like parking/transit): load once immediately, then on an
interval; `clearInterval` on cleanup.

```js
async function poll(url, render, everyMs = 30_000) {
  const tick = async () => render(await getJSON(url));
  await tick();
  const id = setInterval(tick, everyMs);
  return () => clearInterval(id);     // return a cleanup function
}
```

**Tip**: cache values when the source changes rarely (weather ~10 min); when
polling, keep the previous display if a single request fails.

---

## Adding a new source

1. **Check CORS**: `curl -I <url>` — if `access-control-allow-origin` is missing,
   a direct browser fetch won't work → pattern 3 (proxy via [`../deploy/`](../deploy/)).
2. **Clarify auth / rate limit / response shape** (test quickly with `curl`).
3. **Large or rarely changing?** → pattern 2: fetch once, filter, commit JSON
   (model: the `convert.py` scripts under [`../data/`](../data/)).
4. **Otherwise** pattern 1: integrate directly via `fetch`.

## More sources & ideas

**Obvious extensions**: Nextbike (bike sharing), OpenRouteService
(routing/isochrones), SMARD (electricity market data), Transparenzportal Magdeburg
(council documents).

**With caveats**: UBA air data v4 (no CORS headers → proxy needed), Open Bike
Sensor (CSV downloads only → pattern 2).

## Links

GTFS <https://gtfs.org/> · GTFS-RT <https://gtfs.org/realtime/> · Overpass
<https://wiki.openstreetmap.org/wiki/Overpass_API> · Overpass Turbo
<https://overpass-turbo.eu/> · Smart City Magdeburg <https://www.magdeburg.de/smartcity>

Questions? → [`../README.md`](../README.md). Good luck! 🚀
