# Mietspiegel Magdeburg 2024 — Handout

Aggregierte Werte aus dem **qualifizierten Mietspiegel der Landeshauptstadt
Magdeburg 2024**: durchschnittliche Nettokaltmiete pro Quadratmeter je
Stadtteil, gegliedert nach Wohnflächenklasse bzw. Baualtersklasse, für die
Jahre **2012–2026**.

Quelle: Stadt Magdeburg, Mietspiegel-Veröffentlichung 2024
(<https://www.magdeburg.de/Magdeburg-erleben/Bauen-Wohnen/Mietspiegel/>).

## Inhalt

```
.
├── index.json                  Manifest
├── nach-wohnflaeche.json       Mieten × Stadtteil × Wohnflächenklasse × Jahr
└── nach-baualter.json          Mieten × Stadtteil × Baualtersklasse × Jahr
```

| Datei | Zeilen | Stadtteile | Klassen | Jahre |
|---|---|---|---|---|
| `nach-wohnflaeche.json` | 1.461 | 37 | 4 | 2012–2026 |
| `nach-baualter.json` | 1.791 | 34 | 5 | 2012–2026 |

## Schema (Einzeldatensatz)

```jsonc
{
  "id": "mietspiegel-2024/nach-wohnflaeche",
  "title": "Mietspiegel 2024 — Nettokaltmiete je m² nach Wohnflächenklasse und Stadtteil",
  "labelSource": "human-reviewed",
  "labelNotice": "Spalten-Labels stammen direkt aus den Original-Mietspiegel-Headern.",
  "columns": [
    { "key": "year",                  "label": "Jahr",                  "type": "integer", "role": "year" },
    { "key": "stadtteil",             "label": "Stadtteil",             "type": "string" },
    { "key": "wohnflaechenklasse",    "label": "Wohnflächenklasse",     "type": "string" },
    { "key": "nettokaltmiete_pro_qm", "label": "Nettokaltmiete pro m²", "type": "number",  "unit": "EUR/m²" },
    { "key": "stichprobengroesse",    "label": "Stichprobengröße",      "type": "integer", "unit": "Anzahl" }
  ],
  "rows": [
    { "year": 2012, "stadtteil": "Alte Neustadt", "wohnflaechenklasse": "50 bis unter 80 qm",
      "nettokaltmiete_pro_qm": 5.32, "stichprobengroesse": 133 }
  ]
}
```

**Wichtig:** Wo die Stichprobe zu klein war, weist der Mietspiegel keinen Wert
aus. Im JSON erscheinen diese Zellen als `nettokaltmiete_pro_qm: null` und
`stichprobengroesse: null`. Beim Plotten / Filtern entsprechend behandeln
(`r => r.nettokaltmiete_pro_qm != null`).

## Klassen

**Wohnflächenklassen** (`nach-wohnflaeche.json`):

- `unter 20qm`
- `20 bis unter 50 qm`
- `50 bis unter 80 qm`
- `ab 80 qm`

**Baualtersklassen** (`nach-baualter.json`):

- `vor 1925`
- `1926 - 1959`
- `1960 - 1992`
- `1993 - 2002`
- `2003 - 2014`

## Beispielcode

Ein lauffähiges Beispiel (JS + Python) liegt unter
[`../kiss-md/examples/`](../kiss-md/examples/README.md). Schau dort in
`web/mietspiegel.html` bzw. `python/mietspiegel.py`.

## Hinweis zu den Daten

Diese Daten sind im Gegensatz zu den KISS-MD-Tabellen schon im Original mit
klaren, deutschsprachigen Spaltennamen versehen — die Konvertierung war eine
reine Datentyp- und Encoding-Normalisierung, kein Raten. Alle Werte stehen
deshalb unter `labelSource: "human-reviewed"`.

English version: see [`README.en.md`](./README.en.md).
