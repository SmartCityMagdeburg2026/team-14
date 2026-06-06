# Tax revenue & tax rates — City of Magdeburg

> *Deutsche Fassung:* [README.md](./README.md).

Two datasets from the City of Magdeburg on municipal taxation: tax **revenue**
(actual amounts per year) and tax **rates/multipliers** (legal tariffs per tax
type and year).

## Contents

```
.
├── convert.py     builds json/ from csv/ (Python stdlib only)
├── csv/           originals (Latin-1, ;-separated, German number format)
│   ├── steuereinnahmen-2010-2025.csv
│   └── steuersaetze-1991-2026.csv
└── json/          prepared (UTF-8, real JSON numbers)
    ├── index.json
    ├── steuereinnahmen-2010-2025.json
    └── steuersaetze-1991-2026.json
```

`convert.py` re-encodes to UTF-8, parses the German number format
(`1.670.167,05` → `1670167.05`), drops empty columns and sets missing values to
`null`.

## Datasets

### `steuereinnahmen-2010-2025.json` — actual revenue per year (EUR)

One row per budget year (2010–2025), one column per tax type (trade tax, property
tax A/B, dog/entertainment/second-home tax, municipal shares of income/VAT, etc.).
All amounts in **euros**.

```jsonc
{
  "unit": "EUR",
  "columns": [
    { "key": "jahr",          "label": "Haushaltsjahr",  "unit": null,  "type": "integer" },
    { "key": "gewerbesteuer", "label": "Gewerbesteuer",  "unit": "EUR", "type": "number" }
  ],
  "rows": [ { "jahr": 2025, "gewerbesteuer": 177681865.94, … } ]
}
```

> Note: property tax B is split into residential/non-residential from 2025
> (property tax reform) — older years are `null` there, newer years are `null` in
> the legacy "bis 2024" column. The spelling of the column labels matches the
> original file 1:1 (including the typo "Beherbegrungssteuer"). Labels are kept in
> German; only the schema field names are English.

### `steuersaetze-1991-2026.json` — tariffs/multipliers per tax type

One row per **tax type × assessment year** (1991–2026). `tarif` is either a
percentage (e.g. the trade-tax multiplier `450`) or a euro amount, depending on
`waehrung`. Date fields (`vom`, `ab`, `bis`) in `DD.MM.YYYY` format.

```jsonc
{
  "columns": [ { "key": "abgabenart", … }, { "key": "tarif", "type": "number" }, … ],
  "rows": [ {
    "abgabenart": "Gewerbesteuer", "veranlagungsjahr": 2026,
    "tarif": 450.0, "waehrung": "Prozent", "satzung": "Haushaltssatzung"
  } ]
}
```

## Regenerating the data

```bash
python3 convert.py     # reads csv/, writes json/
```
