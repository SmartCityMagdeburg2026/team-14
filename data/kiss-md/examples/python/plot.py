"""Beispielskript: Witterungsdaten Magdeburg laden, plotten, speichern.

Erzeugt eine PNG-Grafik mit Durchschnittstemperatur (Linie) und
Niederschlag (Balken) der letzten 24 Monate.

Voraussetzungen: pandas, matplotlib  (z. B. via `pip install -r requirements.txt`)
"""
import json
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless: kein GUI-Backend nötig
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA = HERE / ".." / ".." / "json" / "wetter" / "witterungsverhaeltnisse-monatlich.json"
OUT  = HERE / "witterung_24_monate.png"

# 1) Datensatz laden
with DATA.open(encoding="utf-8") as f:
    ds = json.load(f)

# 2) var-Keys gegen echte Labels tauschen, damit der DataFrame lesbar wird
rename = {c["key"]: (c["label"] or c["key"]) for c in ds["columns"]}
df = pd.DataFrame(ds["rows"]).rename(columns=rename)

# 3) Letzte 24 Monate, chronologisch aufsteigend
recent = df.head(24).iloc[::-1].reset_index(drop=True)
recent["Zeitachse"] = recent["Jahr"].astype(str) + " " + recent["Monat"]

# 4) Spaltennamen für Temperatur & Niederschlag (Label-basiert, nicht über var-Keys)
temp_col = "Lufttemperatur Monatsmittel"
rain_col = "Niederschlagssumme"
temp_unit = next(c["unit"] for c in ds["columns"] if c["label"] == temp_col)
rain_unit = next(c["unit"] for c in ds["columns"] if c["label"] == rain_col)

# 5) Plot mit zwei Y-Achsen
fig, ax1 = plt.subplots(figsize=(10, 4.5))
ax1.plot(recent["Zeitachse"], recent[temp_col], marker="o",
         color="#e63946", linewidth=2, label=temp_col)
ax1.set_ylabel(f"{temp_col}  [{temp_unit}]", color="#e63946")
ax1.tick_params(axis="y", colors="#e63946")
ax1.set_xticks(range(len(recent)))
ax1.set_xticklabels(recent["Zeitachse"], rotation=45, ha="right")

ax2 = ax1.twinx()
ax2.bar(recent["Zeitachse"], recent[rain_col], alpha=0.45,
        color="#457b9d", label=rain_col)
ax2.set_ylabel(f"{rain_col}  [{rain_unit}]", color="#457b9d")
ax2.tick_params(axis="y", colors="#457b9d")

plt.title(f"{ds['title']}  ·  Magdeburg, letzte 24 Monate")
fig.tight_layout()
fig.savefig(OUT, dpi=120)

# 6) Kurzstatistik in die Konsole
print(f"Datensatz : {ds['title']}")
print(f"Kategorie : {ds['category']} / {ds['subcategory']}")
print(f"Zeilen    : {ds['rowCount']:,}".replace(",", "."))
print(f"")
print(f"Letzte 24 Monate:")
print(f"  Ø {temp_col:30s}  {recent[temp_col].mean():6.1f} {temp_unit}")
print(f"  Ø {rain_col:30s}  {recent[rain_col].mean():6.1f} {rain_unit}")
print(f"  max. Temperatur               {recent[temp_col].max():6.1f} {temp_unit}  "
      f"({recent.loc[recent[temp_col].idxmax(), 'Zeitachse']})")
print(f"")
print(f"Plot gespeichert: {OUT.relative_to(HERE.parent)}")
