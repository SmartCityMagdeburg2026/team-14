# Mietspiegel Magdeburg 2024 — Handout

Aggregated values from the **qualified rent index of the City of Magdeburg,
2024 edition** (German: *Mietspiegel*): the average net cold rent per square
metre by district, broken down by floor-area class and construction-era
class, for the years **2012–2026**.

Source: City of Magdeburg, Mietspiegel 2024 publication
(<https://www.magdeburg.de/Magdeburg-erleben/Bauen-Wohnen/Mietspiegel/>).

> *Deutsche Fassung:* [README.md](./README.md).

## Contents

```
.
├── index.json                  Manifest
├── nach-wohnflaeche.json       Rents × district × floor-area class × year
└── nach-baualter.json          Rents × district × construction-era class × year
```

| File | Rows | Districts | Classes | Years |
|---|---|---|---|---|
| `nach-wohnflaeche.json` | 1,461 | 37 | 4 | 2012–2026 |
| `nach-baualter.json` | 1,791 | 34 | 5 | 2012–2026 |

## Dataset schema

```jsonc
{
  "id": "mietspiegel-2024/nach-wohnflaeche",
  "title": "Mietspiegel 2024 — Nettokaltmiete je m² nach Wohnflächenklasse und Stadtteil",
  "labelSource": "human-reviewed",
  "labelNotice": "Column labels come straight from the original Mietspiegel headers; nothing was guessed.",
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

**Important:** wherever the sample was too small to produce a statistically
meaningful average, the Mietspiegel omits the value. In the JSON those
cells appear as `nettokaltmiete_pro_qm: null` and `stichprobengroesse: null`.
Filter them out before plotting (e.g. `r => r.nettokaltmiete_pro_qm != null`).

## Glossary

The labels are kept in German to match the source. Quick reference:

- **Jahr** — year
- **Stadtteil** — city district
- **Wohnflächenklasse** — floor-area class
- **Baualtersklasse** — construction-era class
- **Nettokaltmiete pro m²** — net cold rent per square metre
  (basic rent excluding utilities and operating costs), in EUR/m²
- **Stichprobengröße** — sample size (number of leases that fed into the
  reported average)

### Floor-area classes (`nach-wohnflaeche.json`)

- `unter 20qm` — under 20 m²
- `20 bis unter 50 qm` — 20 to under 50 m²
- `50 bis unter 80 qm` — 50 to under 80 m²
- `ab 80 qm` — 80 m² and above

### Construction-era classes (`nach-baualter.json`)

- `vor 1925` — built before 1925
- `1926 - 1959` — built 1926–1959
- `1960 - 1992` — built 1960–1992
- `1993 - 2002` — built 1993–2002
- `2003 - 2014` — built 2003–2014

## Example code

A runnable example (JS + Python) lives in
[`../kiss-md/examples/`](../kiss-md/examples/README.en.md). See
`web/mietspiegel.html` and `python/mietspiegel.py`.

## A note on these data

In contrast to the KISS-MD tables, the Mietspiegel source already ships with
clear German column names — converting to JSON was a matter of type and
encoding normalisation, not guessing. Every dataset is therefore marked
`labelSource: "human-reviewed"`.
