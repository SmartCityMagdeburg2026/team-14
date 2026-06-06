# Sensordaten — DWD Klimastation Magdeburg (03126)

> *English version:* [README.en.md](./README.en.md).

Wetter-/Klimazeitreihen der DWD-Station **03126 „Magdeburg"** aus dem
**DWD Climate Data Center (Klimaarchiv Tag/Monat)**. Quelle: Deutscher
Wetterdienst, frei nutzbar mit Quellenangabe (GeoNutzV).

## Inhalt

```
.
├── convert.py        erzeugt json/ aus raw/ (nur Python-Stdlib)
├── json/
│   ├── index.json    Übersicht beider Zeitreihen
│   ├── klima-tag.json    Tageswerte 1881-01-01 … heute (~52.000 Zeilen)
│   └── klima-monat.json  Monatswerte 1834-01-01 … heute (~2.300 Zeilen)
└── raw/              unveränderte DWD-Originalexporte (.txt + Metadaten)
    ├── klarchiv_03126_daily_his/   historische Tageswerte (qualitätsgeprüft)
    ├── klarchiv_03126_daily_akt/   aktuelle Tageswerte
    ├── klarchiv_03126_month_his/   historische Monatswerte
    └── klarchiv_03126_month_akt/   aktuelle Monatswerte
```

`convert.py` **verschmilzt** die historische und die aktuelle Reihe je Granularität
zu einer durchgehenden Zeitachse (dedupliziert nach Datum, aktuelle Werte gewinnen
bei Überlappung), ersetzt Fehlwerte (`-999`) durch `null` und ergänzt deutsche
Spalten-Labels + Einheiten aus den `Metadaten_Parameter`-Dateien.

> Hinweis: `json/klima-tag.json` ist ~19 MB. Für Browser-Visualisierungen ggf.
> nur den benötigten Zeitraum aus `rows` filtern.

## Schema

```jsonc
{
  "station": { "id": "03126", "name": "Magdeburg", "source": "DWD …", "url": "…" },
  "granularity": "daily",                 // oder "monthly"
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

Wichtigste Tageswerte-Spalten: `TMK` Mitteltemperatur, `TXK` Maximum, `TNK` Minimum
(°C) · `RSK` Niederschlag (mm) · `SDK` Sonnenscheindauer (h) · `NM` Bedeckungsgrad
(Achtel) · `FM` Windmittel, `FX` Windspitze (m/s) · `PM` Luftdruck (hPa) ·
`UPM` relative Feuchte (%). Monatswerte tragen `MO_`/`MX_`-Präfixe (z. B. `MO_TT`
Monatsmitteltemperatur, `MO_RR` Niederschlagssumme).

`QN_*`-Spalten sind die DWD-Qualitätsniveaus. Die genauen Codedefinitionen stehen
in den `raw/**/Metadaten_*`-Dateien.

## Daten neu erzeugen

```bash
python3 convert.py     # liest raw/, schreibt json/
```

Um die Reihen zu aktualisieren: neue DWD-Exporte in die passenden `raw/`-Ordner
legen und `convert.py` erneut ausführen.
