# Example project — KISS-MD & Mietspiegel

Two runnable visualisation examples over the bundled Magdeburg datasets, in
JavaScript (Chart.js, in the browser) and in Python (pandas + matplotlib,
saved as PNG).

> *Deutsche Fassung:* [README.md](./README.md).

```
examples/
├── README.md / README.en.md
├── web/
│   ├── index.html                           Weather Magdeburg (JS + Chart.js)
│   └── mietspiegel.html                     Rent index Magdeburg (JS + Chart.js)
└── python/
    ├── plot.py                              Weather Magdeburg (pandas + matplotlib)
    ├── mietspiegel.py                       Rent index Magdeburg (pandas + matplotlib)
    ├── requirements.txt
    ├── witterung_24_monate.png              ← produced by plot.py
    └── mietspiegel_entwicklung.png          ← produced by mietspiegel.py
```

## What the examples show

| Example | Source | Visualisation |
|---|---|---|
| **Weather** (`web/index.html`, `python/plot.py`) | [`../json/wetter/witterungsverhaeltnisse-monatlich.json`](../json/wetter/) | Dual-axis chart: mean air temperature (line) + rainfall (bars), last 24 months |
| **Rent index** (`web/mietspiegel.html`, `python/mietspiegel.py`) | [`../../mietspiegel-2024/nach-wohnflaeche.json`](../../mietspiegel-2024/) | Line chart: net cold rent per m² (floor area 50–80 m²) across selected districts, 2012–2026 |

Dataset schemas:

- KISS-MD data — [`../README.en.md`](../README.en.md)
- Rent index — [`../../mietspiegel-2024/README.en.md`](../../mietspiegel-2024/README.en.md)

## Running the web examples

Start a static web server in the **`data/` directory** (one level
above `kiss-md/`), so the relative paths to both data sources resolve:

```bash
cd data
python3 -m http.server 8000
# → http://localhost:8000/kiss-md/examples/web/                 (weather)
# → http://localhost:8000/kiss-md/examples/web/mietspiegel.html (rent index)
```

The relative fetches in `index.html` (`../../json/wetter/…`) and `mietspiegel.html`
(`../../mietspiegel-2024/…`) then resolve cleanly with no build step.

## Running the Python examples

```bash
cd data/kiss-md/examples/python
pip install -r requirements.txt

python3 plot.py            # produces witterung_24_monate.png + console stats
python3 mietspiegel.py     # produces mietspiegel_entwicklung.png + console stats
```

## Using your own dataset

In either language you only need to point the fetch / file path at a
different dataset (see [`../index.json`](../index.json) for KISS-MD or
[`../../mietspiegel-2024/index.json`](../../mietspiegel-2024/index.json) for
the rent index) and adjust the column-name / filter values (`c.label === '…'`,
`r.wohnflaechenklasse === '…'`).

> **About labels:** All 322 KISS-MD datasets have been manually reviewed
> (`labelSource: "human-reviewed"`); obviously wrong column labels were set
> to null. Where a column shows `label: null`, its meaning could not be
> reliably derived from the raw data — fall back to `key`, `sample`, and the
> dataset's `description` text. Mietspiegel data carries real column names
> from the original source throughout.
>
> All labels and titles remain in **German** to match the original
> Magdeburg sources; only the schema field names are English.
