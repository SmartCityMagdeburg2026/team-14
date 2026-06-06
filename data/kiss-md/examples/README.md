# Beispielprojekt — KISS-MD & Mietspiegel

Zwei lauffähige Visualisierungs-Beispiele über die mitgelieferten Magdeburger
Datensätze, einmal in JavaScript (Chart.js, im Browser) und einmal in Python
(pandas + matplotlib, als PNG).

```
examples/
├── README.md                                ← du bist hier
├── web/
│   ├── index.html                           Witterung Magdeburg (JS + Chart.js)
│   └── mietspiegel.html                     Mietspiegel Magdeburg (JS + Chart.js)
└── python/
    ├── plot.py                              Witterung Magdeburg (pandas + matplotlib)
    ├── mietspiegel.py                       Mietspiegel Magdeburg (pandas + matplotlib)
    ├── requirements.txt
    ├── witterung_24_monate.png              ← wird durch plot.py erzeugt
    └── mietspiegel_entwicklung.png          ← wird durch mietspiegel.py erzeugt
```

## Was zeigen die Beispiele?

| Beispiel | Quelle | Visualisierung |
|---|---|---|
| **Witterung** (`web/index.html`, `python/plot.py`) | [`../json/wetter/witterungsverhaeltnisse-monatlich.json`](../json/wetter/) | Dual-Axis-Chart: Durchschnittstemperatur (Linie) + Niederschlag (Balken), letzte 24 Monate |
| **Mietspiegel** (`web/mietspiegel.html`, `python/mietspiegel.py`) | [`../../mietspiegel-2024/nach-wohnflaeche.json`](../../mietspiegel-2024/) | Liniendiagramm: Nettokaltmiete pro m² (Wohnfläche 50–80 m²) in ausgewählten Stadtteilen über 2012–2026 |

Schema der Datensätze:

- KISS-MD-Daten — [`../README.md`](../README.md)
- Mietspiegel — [`../../mietspiegel-2024/README.md`](../../mietspiegel-2024/README.md)

## Web-Beispiele ausführen

Statischen Webserver im **`data/`-Verzeichnis** starten (eine Ebene
über `kiss-md/`), damit die relativen Pfade zu beiden Datenquellen auflösen:

```bash
cd data
python3 -m http.server 8000
# → http://localhost:8000/kiss-md/examples/web/                 (Witterung)
# → http://localhost:8000/kiss-md/examples/web/mietspiegel.html (Mietspiegel)
```

Der relative Fetch in `index.html` (`../../json/wetter/…`) und in `mietspiegel.html`
(`../../mietspiegel-2024/…`) löst dann sauber auf, ohne Build-Schritt.

## Python-Beispiele ausführen

```bash
cd data/kiss-md/examples/python
pip install -r requirements.txt

python3 plot.py            # erzeugt witterung_24_monate.png + Konsolen-Stats
python3 mietspiegel.py     # erzeugt mietspiegel_entwicklung.png + Konsolen-Stats
```

## Eigene Datensätze einbinden

In beiden Sprachen genügt es, den Fetch- bzw. Pfad-Wert auf einen anderen
Datensatz zeigen zu lassen (siehe [`../index.json`](../index.json) für KISS-MD
bzw. [`../../mietspiegel-2024/index.json`](../../mietspiegel-2024/index.json)
für Mietspiegel) und die Spaltennamen / Filter-Werte (`c.label === '…'`,
`r.wohnflaechenklasse === '…'`) anzupassen.

> **Hinweis zu Labels:** Alle 322 KISS-MD-Datensätze wurden manuell
> nachgepflegt (`labelSource: "human-reviewed"`); offensichtlich falsche
> Spalten-Labels wurden genullt. Wo eine Spalte `label: null` hat, war die
> Bedeutung aus den Rohdaten nicht zuverlässig herzuleiten — auf `key`,
> `sample` und den Datensatz-Beschreibungstext im `description`-Feld
> zurückgreifen. Mietspiegel-Daten haben durchgehend echte Spaltennamen aus
> der Originalquelle.

English version: see [`README.en.md`](./README.en.md).
