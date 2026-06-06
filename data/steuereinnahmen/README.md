# Steuereinnahmen & Steuersätze — Landeshauptstadt Magdeburg

> *English version:* [README.en.md](./README.en.md).

Zwei Datensätze der Stadt Magdeburg zur kommunalen Besteuerung:
Steuer**einnahmen** (Ist-Beträge je Jahr) und Steuer**sätze/Hebesätze**
(rechtliche Tarife je Abgabenart und Jahr).

## Inhalt

```
.
├── convert.py     erzeugt json/ aus csv/ (nur Python-Stdlib)
├── csv/           Originale (Latin-1, ;-getrennt, deutsches Zahlenformat)
│   ├── steuereinnahmen-2010-2025.csv
│   └── steuersaetze-1991-2026.csv
└── json/          aufbereitet (UTF-8, echte JSON-Zahlen)
    ├── index.json
    ├── steuereinnahmen-2010-2025.json
    └── steuersaetze-1991-2026.json
```

`convert.py` rekodiert nach UTF-8, parst das deutsche Zahlenformat
(`1.670.167,05` → `1670167.05`), entfernt leere Spalten und setzt Fehlwerte
auf `null`.

## Datensätze

### `steuereinnahmen-2010-2025.json` — Ist-Einnahmen je Jahr (EUR)

Eine Zeile pro Haushaltsjahr (2010–2025), eine Spalte je Steuerart
(Gewerbesteuer, Grundsteuer A/B, Hunde-, Vergnügungs-, Zweitwohnungssteuer,
Gemeindeanteile an Einkommen-/Umsatzsteuer u. a.). Alle Beträge in **Euro**.

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

> Hinweis: Die Grundsteuer B ist ab 2025 in Wohn-/Nichtwohngrundstücke
> aufgeteilt (Grundsteuerreform) — ältere Jahre haben dort `null`, neuere `null`
> in der Alt-Spalte „bis 2024". Die Schreibweise der Spalten-Labels entspricht
> 1:1 der Originaldatei (inkl. Tippfehler „Beherbegrungssteuer").

### `steuersaetze-1991-2026.json` — Tarife/Hebesätze je Abgabenart

Eine Zeile je **Abgabenart × Veranlagungsjahr** (1991–2026). `tarif` ist je nach
`waehrung` ein Prozentsatz (z. B. Gewerbesteuer-Hebesatz `450`) oder ein
EUR-Betrag. Datumsfelder (`vom`, `ab`, `bis`) im Format `TT.MM.JJJJ`.

```jsonc
{
  "columns": [ { "key": "abgabenart", … }, { "key": "tarif", "type": "number" }, … ],
  "rows": [ {
    "abgabenart": "Gewerbesteuer", "veranlagungsjahr": 2026,
    "tarif": 450.0, "waehrung": "Prozent", "satzung": "Haushaltssatzung"
  } ]
}
```

## Daten neu erzeugen

```bash
python3 convert.py     # liest csv/, schreibt json/
```
