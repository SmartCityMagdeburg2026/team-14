# Sensor data — DWD climate station Magdeburg (03126)

> *Deutsche Fassung:* [README.md](./README.md).

Weather/climate time series from DWD station **03126 "Magdeburg"**, from the
**DWD Climate Data Center (climate archive day/month)**. Source: Deutscher
Wetterdienst, free to use with attribution (GeoNutzV).

## Contents

```
.
├── convert.py        builds json/ from raw/ (Python stdlib only)
├── json/
│   ├── index.json    overview of both time series
│   ├── klima-tag.json    daily values 1881-01-01 … today (~52,000 rows)
│   └── klima-monat.json  monthly values 1834-01-01 … today (~2,300 rows)
└── raw/              unmodified original DWD exports (.txt + metadata)
    ├── klarchiv_03126_daily_his/   historical daily values (quality-checked)
    ├── klarchiv_03126_daily_akt/   recent daily values
    ├── klarchiv_03126_month_his/   historical monthly values
    └── klarchiv_03126_month_akt/   recent monthly values
```

`convert.py` **merges** the historical and the recent series per granularity into
one continuous timeline (deduplicated by date, recent wins on overlap), replaces
missing values (`-999`) with `null`, and adds German column labels + units from
the `Metadaten_Parameter` files.

> Note: `json/klima-tag.json` is ~19 MB. For browser visualizations, filter only
> the required time range from `rows`.

## Schema

```jsonc
{
  "station": { "id": "03126", "name": "Magdeburg", "source": "DWD …", "url": "…" },
  "granularity": "daily",                 // or "monthly"
  "period": { "start": "1881-01-01", "end": "2026-05-24" },
  "columns": [
    { "key": "date", "label": "Datum (ISO)",                        "unit": null },
    { "key": "TMK",  "label": "Tagesmittel der Lufttemperatur",     "unit": "°C" },
    { "key": "RSK",  "label": "tägliche Niederschlagshöhe",         "unit": "mm" },
    { "key": "FM",   "label": "Tagesmittel der Windgeschwindigkeit","unit": "m/sec" }
  ],
  "rowCount": 52405,
  "rows": [ { "date": "1881-01-01", "TMK": -0.3, "RSK": 0.0, … } ]
}
```

Most important daily columns: `TMK` mean temperature, `TXK` maximum, `TNK` minimum
(°C) · `RSK` precipitation (mm) · `SDK` sunshine duration (h) · `NM` cloud cover
(eighths) · `FM` mean wind, `FX` wind gust (m/s) · `PM` air pressure (hPa) ·
`UPM` relative humidity (%). Monthly values carry `MO_`/`MX_` prefixes (e.g.
`MO_TT` monthly mean temperature, `MO_RR` precipitation total).

`QN_*` columns are the DWD quality levels. The exact code definitions are in the
`raw/**/Metadaten_*` files.

> Column labels and units are kept in **German** to match the original DWD source;
> only the schema field names are English.

## Regenerating the data

```bash
python3 convert.py     # reads raw/, writes json/
```

To update the series: place new DWD exports into the matching `raw/` folders and
run `convert.py` again.
