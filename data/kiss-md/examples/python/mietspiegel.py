"""Beispiel: Mietspiegel Magdeburg 2024 visualisieren.

Erzeugt eine PNG-Grafik mit der Entwicklung der Nettokaltmiete pro m² für
ausgewählte Stadtteile (mittlere Wohnflächenklasse 50–80 m²) über die Jahre
2012–2026.

Voraussetzungen: pandas, matplotlib (vgl. requirements.txt)
"""
import json
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA = HERE / ".." / ".." / ".." / "mietspiegel-2024" / "nach-wohnflaeche.json"
OUT = HERE / "mietspiegel_entwicklung.png"

KATEGORIE = "50 bis unter 80 qm"
STADTTEILE = ["Altstadt", "Stadtfeld Ost", "Sudenburg", "Buckau",
              "Alte Neustadt", "Neustädter See"]
PALETTE = ["#e63946", "#1d3557", "#2a9d8f", "#f4a261", "#9d4edd", "#6a994e"]

# 1) Datensatz laden
with DATA.open(encoding="utf-8") as f:
    ds = json.load(f)
df = pd.DataFrame(ds["rows"])

# 2) Filter auf gewählte Wohnflächenklasse
df = df[df["wohnflaechenklasse"] == KATEGORIE].copy()

# 3) Pivot: Zeilen=Jahr, Spalten=Stadtteil, Werte=Nettokaltmiete
pivot = (df.pivot_table(index="year", columns="stadtteil",
                        values="nettokaltmiete_pro_qm", aggfunc="mean")
           .reindex(columns=STADTTEILE))

# 4) Plot
fig, ax = plt.subplots(figsize=(11, 5))
for stadtteil, color in zip(STADTTEILE, PALETTE):
    pivot[stadtteil].plot(ax=ax, marker="o", linewidth=2,
                           color=color, label=stadtteil)
ax.set_title(f"Mietspiegel Magdeburg — Nettokaltmiete (Wohnfläche {KATEGORIE})")
ax.set_xlabel("Jahr")
ax.set_ylabel("EUR / m²")
ax.legend(loc="upper left", ncol=2, framealpha=0.9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT, dpi=120)

# 5) Konsolen-Zusammenfassung
print(f"Datensatz : {ds['title']}")
print(f"Quelle    : {ds['source']['system']}")
print(f"Zeilen    : {ds['rowCount']:,}".replace(",", "."))
print(f"")
print(f"Aktuelle Werte ({pivot.index.max()}, {KATEGORIE}):")
latest = pivot.loc[pivot.index.max()].dropna().sort_values(ascending=False)
for stadtteil, value in latest.items():
    print(f"  {stadtteil:25s}  {value:5.2f} EUR/m²")
print(f"")
print(f"Plot gespeichert: {OUT.relative_to(HERE.parent)}")
