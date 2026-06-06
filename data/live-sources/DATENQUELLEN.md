# Live-Datenquellen — Smart City Hackathon Magdeburg

> *English version:* [DATENQUELLEN.en.md](./DATENQUELLEN.en.md).

Dieser Ordner ergänzt die **statischen, bereits aufbereiteten Datensätze** unter
[`../data/`](../data/) um **Live-Quellen**: APIs, die ihr zur Laufzeit eurer App
abruft (Wetter, Pegelstände, ÖPNV-Echtzeit, Luftqualität, Parken …). Hier stehen
Endpunkte, Antwortformate und **eigenständige Code-Beispiele**, mit denen ihr sie
einbindet — unabhängig von Framework oder Sprache.

> Nutzt nur öffentliche/Open-Data-Quellen mit Quellenangabe und **keine
> personenbezogenen Daten** (siehe Hinweise in [`../README.md`](../README.md)).

## Drei Integrationsmuster

| # | Muster | Wann | Beispiele hier |
|---|--------|------|----------------|
| 1 | **Browser-Fetch** direkt | API sendet CORS-Header | Wetter, Pegel, Luft, GovData |
| 2 | **Vorverarbeiten** → statisches JSON | groß / strikt rate-limitiert / selten geändert | OSM/Overpass, GTFS-Fahrplan |
| 3 | **Server-Proxy** über euer Backend | API ohne CORS-Header | GTFS-RT |

Muster 2 ist genau das, was die fertigen Datensätze unter [`../data/`](../data/)
sind — einmal geholt/konvertiert und als JSON eingecheckt (z. B.
`../data/sensor-data/convert.py`). Für Muster 3 bringt dieses Repo bereits ein
Backend mit: den FastAPI-Starter unter [`../deploy/`](../deploy/) — dort hängt ihr
einen Proxy-Endpunkt ein (Beispiel weiter unten).

**Magdeburg-Anker** (sinnvoller Query-Mittelpunkt): `{ lat: 52.1205, lon: 11.6276 }`.
**Bounding-Box** Stadtgebiet: `52.05, 11.55, 52.20, 11.75` (S,W,N,O).

## Überblick

| Quelle | Muster | CORS | Endpoint (Kurz) |
|--------|--------|------|-----------------|
| Bright Sky / DWD — Wetter | 1 | ✅ | `api.brightsky.dev/current_weather` |
| PEGELONLINE / WSV — Elbe-Pegel | 1 | ✅ | `pegelonline.wsv.de/webservices/rest-api/v2` |
| Sensor.Community — Luftqualität | 1 | ✅ | `data.sensor.community/airrohr/v1/filter` |
| GovData CKAN — offene Datensätze | 1 | ✅ | `ckan.govdata.de/api/3/action/package_search` |
| OSM-Tiles + LVermGeo-WMS — Karten | 1 | n/a¹ | `tile.openstreetmap.org` · `geodatenportal.sachsen-anhalt.de` |
| OpenStreetMap via Overpass | 2 | ✅ | `overpass-api.de/api/interpreter` |
| GTFS-Fahrplan (gtfs.de) | 2 | ✅ | `download.gtfs.de/germany/nv_free/latest.zip` |
| GTFS-RT — ÖPNV-Echtzeit | 3 | ❌ | `realtime.gtfs.de/realtime-free.pb` |

¹ Kachel-/WMS-Layer sind `<img>`-Requests, kein `fetch` → CORS spielt keine Rolle.

---

## 1 · Browser-seitige APIs

Direkt per `fetch` aus dem Browser. Kein Proxy, kein API-Key.

### Bright Sky / DWD — Wetter

- **Endpoint**: `https://api.brightsky.dev/current_weather?lat=<lat>&lon=<lon>`
- **Docs**: <https://brightsky.dev/docs/> · Auth: keine · Rate-Limit: fair use

```js
const md = { lat: 52.1205, lon: 11.6276 };
const url = `https://api.brightsky.dev/current_weather?lat=${md.lat}&lon=${md.lon}`;
const { weather } = await fetch(url).then(r => r.json());
// weather.temperature (°C), weather.wind_speed (km/h),
// weather.precipitation (mm), weather.cloud_cover (%), weather.condition
```

### PEGELONLINE / WSV — Elbe-Wasserstand

- **Basis**: `https://www.pegelonline.wsv.de/webservices/rest-api/v2`
- **Docs**: <https://pegelonline.wsv.de/webservice/dokuRestapi> · Auth/Rate-Limit: keine

```js
const base = 'https://www.pegelonline.wsv.de/webservices/rest-api/v2';
const STATION = 'MAGDEBURG-STROMBR%C3%9CCKE';            // URL-kodiert lassen!

// aktueller Wert (Wasserstand in cm):
const now = await fetch(`${base}/stations/${STATION}/W/currentmeasurement.json`)
  .then(r => r.json());                                   // → { timestamp, value }

// Verlauf (ISO-8601-Dauer: P1D = 24 h, P7D = 7 Tage):
const series = await fetch(`${base}/stations/${STATION}/W/measurements.json?start=P7D`)
  .then(r => r.json());                                   // → [ { timestamp, value }, … ]
```

### Sensor.Community — Luftqualität (Bürger-Messnetz)

- **Endpoint**: `https://data.sensor.community/airrohr/v1/filter/area=<lat>,<lon>,<radius_km>`
- **Docs**: <https://github.com/opendata-stuttgart/meta/wiki/APIs> · max ~1 Req/5 min

```js
const r = await fetch('https://data.sensor.community/airrohr/v1/filter/area=52.1205,11.6276,10')
  .then(r => r.json());
// Pro Eintrag: sensordatavalues[] mit value_type 'P1' = PM10, 'P2' = PM2.5 (µg/m³).
// Über mehrere Sensoren mitteln. WHO-24h-Richtwerte: PM10 45, PM2.5 15 µg/m³.
```

### GovData CKAN — offene Datensätze (Katalogsuche)

- **Endpoint**: `https://ckan.govdata.de/api/3/action/package_search`
- **Docs**: <https://docs.ckan.org/en/latest/api/>

```js
const p = new URLSearchParams({ q: 'Magdeburg', rows: 10, sort: 'metadata_modified desc' });
const d = await fetch(`https://ckan.govdata.de/api/3/action/package_search?${p}`)
  .then(r => r.json());
const datasets = d.result.results;            // d.result.count = Treffer gesamt
// Filtern via fq=, z. B. fq=res_format:CSV  oder  fq=organization:magdeburg
```

### Karten-Basislayer

Als Kachel-/WMS-Layer in jeder Karten-Bibliothek (Leaflet, MapLibre, OpenLayers …)
einsetzbar — kein Proxy nötig:

- **OSM-Tiles**: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
- **LVermGeo Sachsen-Anhalt** Orthophoto-WMS (Open Data):
  `https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_OpenData_WMS/guest`,
  Layer `lsa_lvermgeo_dop_020`.

---

## 2 · Vorverarbeitete Quellen

Große oder strikt limitierte Quellen **einmal** abrufen, filtern und das Ergebnis
als JSON einchecken — eure App trifft die API zur Laufzeit nie. (Genau so sind die
Datensätze unter [`../data/`](../data/) entstanden.)

### OpenStreetMap via Overpass

- **Endpoint**: `https://overpass-api.de/api/interpreter` (Fallbacks:
  `overpass.kumi.systems`, `overpass.private.coffee`)
- **Docs**: <https://wiki.openstreetmap.org/wiki/Overpass_API> ·
  Query-Builder: <https://overpass-turbo.eu/>
- **Warum vorverarbeiten?** strikt rate-limitiert (~2 Req/s), Daten ändern sich selten.

Beispiel: Ladesäulen, Tram-Haltestellen und Radabstellanlagen im Stadtgebiet holen
und als JSON speichern (Python, nur `requests`):

```python
import json, requests

BBOX = "52.05,11.55,52.20,11.75"      # S,W,N,O
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
elements = r.json()["elements"]       # je Element: lat/lon (oder center.lat/lon) + tags
json.dump(elements, open("osm-poi.json", "w"), ensure_ascii=False, indent=2)
```

### GTFS-Fahrplan (gtfs.de)

- **Quelle**: `https://download.gtfs.de/germany/nv_free/latest.zip` · Lizenz CC-BY 4.0
- **Docs**: <https://gtfs.org/> · **Warum vorverarbeiten?** ~200 MB ZIP,
  `stop_times.txt` >500 MB entpackt — nichts für den Browser.

Vorgehen: ZIP serverseitig laden, auf die Magdeburg-BBox filtern (Haltestellen aus
`stops.txt`, Fahrten aus `trips.txt`/`stop_times.txt`) und ein schlankes JSON
schreiben. `route_type`: `0` Tram · `1` U-Bahn · `2` Zug · `3` Bus · `4` Fähre ·
`11` O-Bus. Für „fährt heute?" Wochentag **und** Gültigkeitszeitraum aus
`calendar.txt` (`YYYYMMDD`, 0 = Montag) prüfen.

---

## 3 · Server-Proxy-APIs

Diese Backends senden **keine** CORS-Header — ein direkter Browser-`fetch`
scheitert. Lösung: über euer eigenes Backend **same-origin** weiterleiten. Der
FastAPI-Starter unter [`../deploy/`](../deploy/) eignet sich dafür direkt.

### Proxy in den FastAPI-Starter einbauen

Allgemeines Muster — eine CORS-lose JSON-API **same-origin** weiterleiten. In
`deploy/app/main.py` ergänzen (`httpx` ist Teil von `fastapi[standard]`):

```python
import httpx
from fastapi import Request, Response

UPSTREAM = "https://example-api.invalid"     # Ziel-API ohne CORS-Header

@app.get("/api/proxy/{path:path}")
async def proxy(path: str, request: Request):
    async with httpx.AsyncClient(timeout=10) as client:
        up = await client.get(f"{UPSTREAM}/{path}", params=request.query_params,
                              headers={"Accept": "application/json"})
    return Response(content=up.content, status_code=up.status_code,
                    media_type="application/json")
```

Danach ruft der Browser **same-origin** `/api/proxy/…` auf, statt die fremde API
direkt zu kontaktieren.

### GTFS-RT — ÖPNV-Echtzeit

- **Feed**: `https://realtime.gtfs.de/realtime-free.pb` (Protocol Buffers, ganz DE)
- **Docs**: <https://gtfs.org/realtime/>
- **Warum serverseitig?** Protobuf + deutschlandweite Datenmenge sind nichts für
  den Browser → im Backend dekodieren, auf Magdeburg filtern, als JSON ausliefern.
- **Hinweis**: Der `nv_free`-Feed enthält **nur `TripUpdate`s (Verspätungen),
  keine `VehiclePosition`s** — Fahrzeugpositionen müsstet ihr aus dem Fahrplan
  (Muster 2) zwischen den Halten interpolieren.

Endpunkt im FastAPI-Starter (zusätzlich `gtfs-realtime-bindings` + `protobuf`
installieren):

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
    return {"updates": updates}   # auf Magdeburg-stop_ids aus dem GTFS-Fahrplan filtern
```

---

## Wiederkehrende Muster (framework-neutral)

**Fetch mit Timeout** (hängende Requests abbrechen):

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

**Polling** (Live-Quellen wie Parken/ÖPNV): sofort einmal laden, dann Intervall;
beim Aufräumen `clearInterval`.

```js
async function poll(url, render, everyMs = 30_000) {
  const tick = async () => render(await getJSON(url));
  await tick();
  const id = setInterval(tick, everyMs);
  return () => clearInterval(id);     // Cleanup-Funktion zurückgeben
}
```

**Tipp**: Werte cachen, wenn sich die Quelle selten ändert (Wetter ~10 min); bei
Polling die vorherige Anzeige behalten, falls ein einzelner Request scheitert.

---

## Eine neue Quelle hinzufügen

1. **CORS prüfen**: `curl -I <url>` — fehlt `access-control-allow-origin`, geht
   kein direkter Browser-Fetch → Muster 3 (Proxy über [`../deploy/`](../deploy/)).
2. **Auth / Rate-Limit / Antwortform** klären (kurz mit `curl` antesten).
3. **Groß oder selten geändert?** → Muster 2: einmal holen, filtern, JSON einchecken
   (Vorbild: die `convert.py`-Skripte unter [`../data/`](../data/)).
4. **Sonst** Muster 1: direkt per `fetch` einbinden.

## Weitere Quellen & Ideen

**Naheliegende Erweiterungen**: Nextbike (Bike-Sharing), OpenRouteService
(Routing/Isochronen), SMARD (Strommarktdaten), Transparenzportal Magdeburg
(Ratsdokumente).

**Mit Einschränkung**: UBA-Luftdaten v4 (keine CORS-Header → Proxy nötig),
Open Bike Sensor (nur CSV-Downloads → Muster 2).

## Links

GTFS <https://gtfs.org/> · GTFS-RT <https://gtfs.org/realtime/> · Overpass
<https://wiki.openstreetmap.org/wiki/Overpass_API> · Overpass Turbo
<https://overpass-turbo.eu/> · Smart City Magdeburg <https://www.magdeburg.de/smartcity>

Fragen? → [`../README.md`](../README.md). Viel Erfolg! 🚀
