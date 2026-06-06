# KISS-MD Datensätze — Handout

322 Datensätze aus dem **Kommunalen Informations- und Statistiksystem
Magdeburg (KISS-MD)**, aufbereitet als JSON zur direkten Nutzung in
Web-Dashboards. Quelle: Stadt Magdeburg, Amt für Statistik
(<https://statistik.magdeburg.de/KISS-MD/>).

## Inhalt

```
.
├── index.json                       Manifest aller Datensätze
├── json/<kategorie>/<datensatz>.json  aufbereiteter Datensatz (für Visualisierung)
├── xlsx/<kategorie>/<datensatz>.xlsx  Original-Export aus KISS-MD (gleicher Slug)
└── examples/                        lauffähiges Beispielprojekt
    ├── README.md                    →  Anleitung zum Starten
    ├── web/index.html               JavaScript + Chart.js (Witterung)
    ├── web/mietspiegel.html         JavaScript + Chart.js (Mietspiegel)
    ├── python/plot.py               pandas + matplotlib (Witterung)
    └── python/mietspiegel.py        pandas + matplotlib (Mietspiegel)
```

Schwester-Datensatz im selben Bündel: [`../mietspiegel-2024/`](../mietspiegel-2024/)
(aggregierte Mieten 2012–2026 je Stadtteil).

- **322 Datensätze** in **13 Kategorien** (Bevölkerung, Wirtschaft, Verkehr,
  Energie, Wetter, Bildung, Bauen & Wohnen, Arbeitsmarkt, Gesundheit, …)
- **alle Datensätze manuell überprüft** (`labelSource: "human-reviewed"`);
  unzuverlässige Labels wurden auf `null` gesetzt
- alle Pfade ASCII-slugifiziert (z. B. `bevoelkerung/...`,
  `oeffentliche-ordnung/...`) — keine Umlaute oder Leerzeichen in URLs

> **Quick-Start:** lauffähiges Beispielprojekt mit JS- und Python-Code unter
> [`examples/`](./examples/README.md) — Visualisierungen aus Witterungs- und
> Mietspiegel-Daten, side-by-side.

## Schema

### Manifest `index.json`

```jsonc
{
  "datasetCount": 322,
  "categoryCount": 13,
  "categories": [{
    "slug": "wetter", "name": "Wetter", "count": 2,
    "datasets": [{
      "id":          "wetter/witterungsverhaeltnisse-monatlich",
      "title":       "Witterungsverhältnisse - monatlich",
      "subcategory": "Witterung in Magdeburg",
      "tableId":     "QB_41",
      "rowCount":    1711,
      "columnCount": 22,
      "path":        "json/wetter/witterungsverhaeltnisse-monatlich.json",
      "xlsxPath":    "xlsx/wetter/witterungsverhaeltnisse-monatlich.xlsx"
    }]
  }]
}
```

### Einzeldatensatz

```jsonc
{
  "id":          "wetter/witterungsverhaeltnisse-monatlich",
  "title":       "Witterungsverhältnisse - monatlich",
  "category":    "Wetter",
  "subcategory": "Witterung in Magdeburg",
  "labelSource": "human-reviewed",
  "labelNotice": "Spalten-Labels und Einheiten wurden manuell aus den Rohdaten verifiziert.",
  "description": "Monatliche Witterungsdaten Magdeburg…",
  "columns": [
    { "key": "var1", "label": "Jahr",                        "unit": null, "type": "integer", "role": "year",     "sample": [2025, 2024, 2023] },
    { "key": "var2", "label": "Monat",                       "unit": null, "type": "string",  "role": "month_de", "sample": ["Juni","Mai"] },
    { "key": "var3", "label": "Lufttemperatur Monatsmittel", "unit": "°C", "type": "number",  "role": null,       "sample": [19.2, 14.1] }
  ],
  "rowCount": 1711,
  "rows": [
    { "var1": 2025, "var2": "Juni", "var3": 19.2 }
  ]
}
```

Felder auf Datensatz-Ebene:
- **`labelSource`** — `"human-reviewed"`, `"llm-draft"` oder `"none"`
- **`labelNotice`** — kurzer Hinweistext zur Herkunft der Labels (siehe unten)

Felder pro Spalte:
- **`key`** — Zugriffsschlüssel in `rows[i]` (`var1`, `var2`, …)
- **`label`** — deutsche Bezeichnung, `null` wenn unbekannt oder von der
  Validierung als unzuverlässig markiert
- **`unit`** — Einheit (`°C`, `mm`, `%`, `Anzahl`, `EUR`, `1.000 EUR`, …) oder `null`
- **`type`** — `"integer"`, `"number"`, `"string"`, `"mixed"`
- **`role`** — optional `"year"` oder `"month_de"` für Zeitreihen-Achsen
- **`sample`** — die ersten 3 nicht-`null`-Werte zur schnellen Orientierung

Fehlwerte sind durchgängig als `null` codiert.

## Hinweis zu den Labels

Das Quellsystem KISS-MD stellt seine Tabellen ohne maschinenlesbare
Spaltennamen bereit — intern heißen die Spalten nur `var1`, `var2`, … Da es
keine offizielle Bezeichnungsliste gibt, wurden die deutschen Labels und
Einheiten zunächst von einem **Sprachmodell aus Titel, Kategorie und
Stichproben generiert** und anschließend **alle 322 Datensätze manuell
überprüft**. Die Überprüfung ist bewusst konservativ: Spalten-Labels, deren
Bedeutung nicht eindeutig aus den Werten und Spaltennamen herleitbar war,
wurden auf `null` gesetzt. Das ist ehrlicher als zu raten — `null` heißt
schlicht „diese Spalte enthält Daten, deren genaue Bedeutung wir nicht
sichern können".

Im `description`-Feld jedes Datensatzes steht, was bekannt ist und welche
Spalten warum verworfen wurden — z. B. *„var3..var7 sind 5 Altersgruppen mit
Summe = var8 verifiziert; die Grenzen waren aber nicht aus den Rohdaten
ableitbar"*. Die `tableId` (z. B. `K8_T26`) lässt sich im Original-Portal
von KISS-MD zur Klärung nachschlagen.

Spalten mit `label: null` enthalten weiterhin sinnvolle Rohdaten, deren
genaue Zuordnung jedoch unsicher ist — auf `key`, `sample` und den
`description`-Text zurückgreifen.

---

## Beispiel 1 — JavaScript (Vanilla + Chart.js)

Liniendiagramm der monatlichen Durchschnittstemperatur über die letzten zwei
Jahre:

```html
<canvas id="chart" style="max-width:720px"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script type="module">
  const ds = await fetch('./json/wetter/witterungsverhaeltnisse-monatlich.json')
    .then(r => r.json());

  // Passende Spalten finden (Label-basiert, nicht über die var-Keys)
  const yearCol  = ds.columns.find(c => c.role === 'year');
  const monthCol = ds.columns.find(c => c.role === 'month_de');
  const tempCol  = ds.columns.find(c => c.label === 'Lufttemperatur Monatsmittel');

  // letzte 24 Monate, chronologisch aufsteigend
  const recent = ds.rows.slice(0, 24).reverse();
  const labels = recent.map(r => `${r[yearCol.key]} ${r[monthCol.key]}`);
  const values = recent.map(r => r[tempCol.key]);

  new Chart(document.getElementById('chart'), {
    type: 'line',
    data: { labels, datasets: [{ label: tempCol.label, data: values, tension: 0.3 }] },
    options: {
      scales: { y: { title: { display: true, text: tempCol.unit } } },
      plugins: { title: { display: true, text: ds.title } },
    },
  });
</script>
```

Manifest durchsuchen, z. B. alle Datensätze einer Kategorie:

```js
const idx = await fetch('./index.json').then(r => r.json());
const wetter = idx.categories.find(c => c.slug === 'wetter');
console.table(wetter.datasets.map(d => ({ title: d.title, rows: d.rowCount })));
```

## Beispiel 2 — Python (pandas + matplotlib)

```python
import json
import pandas as pd
import matplotlib.pyplot as plt

with open('json/wetter/witterungsverhaeltnisse-monatlich.json', encoding='utf-8') as f:
    ds = json.load(f)

# var-Keys → echte Labels, damit der DataFrame lesbar wird
rename = {c['key']: c['label'] or c['key'] for c in ds['columns']}
df = pd.DataFrame(ds['rows']).rename(columns=rename)

# Letzte 24 Monate, chronologisch
recent = df.head(24).iloc[::-1].reset_index(drop=True)
recent['Zeitachse'] = recent['Jahr'].astype(str) + ' ' + recent['Monat']

temp_col = 'Lufttemperatur Monatsmittel'
ax = recent.plot(x='Zeitachse', y=temp_col, marker='o',
                 figsize=(10, 4), title=ds['title'])
ax.set_ylabel(next(c['unit'] for c in ds['columns'] if c['label'] == temp_col))
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

Alle Datensätze einer Kategorie als DataFrame mit zugehörigen Pfaden:

```python
import json
with open('index.json', encoding='utf-8') as f:
    idx = json.load(f)
verkehr = next(c for c in idx['categories'] if c['slug'] == 'verkehr')
print(pd.DataFrame(verkehr['datasets'])[['title', 'rowCount', 'path']])
```

## Tipps

- **Zeitreihen erkennen** — Spalten mit `role: "year"` / `role: "month_de"` sind
  immer die Zeitachse. Bei reinen Querschnitts-Tabellen (z. B. „Straftaten
  2021 nach Stadtteil") hat `var1` zwar `role: "year"`, aber alle Zeilen
  zeigen dasselbe Jahr → `df['Jahr'].nunique()` prüfen.
- **Einheit ist im Datensatz** — direkt `column.unit` als Achsen-Suffix
  übernehmen, anstatt sie aus dem Label zu parsen.
- **Wide vs. long** — manche Tabellen sind cross-tabs (z. B. Bevölkerung nach
  Alter & Geschlecht: var1=Jahr, var2=Alter, var3..varN=Bevölkerungsgruppen).
  Vor `groupby`/`pivot` einmal in den ersten Zeilen umsehen.
- **Sparse-Spalten** — Spalten mit `"label": null` sind solche, bei denen das
  Modell unsicher war. Meistens enthalten sie wenig Information; im Zweifel
  überspringen.
- **Robuste Datensatz-Auswahl** — verlinke immer über die `id`/`path` aus
  `index.json`, nicht über den Titel: Titel können sich ändern, die slugs
  bleiben stabil.
