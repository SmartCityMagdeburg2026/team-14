#!/usr/bin/env python3
"""Convert the raw tax CSVs of the Landeshauptstadt Magdeburg under csv/ into
clean UTF-8 JSON under json/ for easy use in visualization frameworks.

The source CSVs are Latin-1 encoded, semicolon-separated and use the German
number format (e.g. "1.670.167,05"). This script re-encodes to UTF-8, parses
numbers to real JSON numbers, drops empty trailing columns and normalizes
missing values to null.

Run:  python3 convert.py        (stdlib only)
"""
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "csv")
OUT = os.path.join(HERE, "json")

SOURCE = {
    "system": "Landeshauptstadt Magdeburg — Steuerstatistik",
    "holder": "Stadt Magdeburg",
}

UML = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}


def slug(s):
    s = s.strip().lower()
    s = "".join(UML.get(c, c) for c in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def read_rows(path):
    with open(path, encoding="latin-1") as f:
        return list(csv.reader(f, delimiter=";"))


def num(v):
    """German number string -> int/float, or None."""
    v = (v or "").strip()
    if v == "":
        return None
    n = v.replace(".", "").replace(",", ".")
    try:
        f = float(n)
        return int(f) if f.is_integer() and "," not in v and "." not in v else f
    except ValueError:
        return v


def convert_einnahmen():
    rows = read_rows(os.path.join(CSV, "steuereinnahmen-2010-2025.csv"))
    header = [h.strip() for h in rows[0]]
    # keep only non-empty header columns
    keep = [i for i, h in enumerate(header) if h]
    cols = []
    for i in keep:
        h = header[i]
        is_year = i == 0
        cols.append({
            "key": "jahr" if is_year else slug(h),
            "label": h,
            "unit": None if is_year else "EUR",
            "type": "integer" if is_year else "number",
        })
    data = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        rec = {}
        for ci, i in enumerate(keep):
            raw = r[i] if i < len(r) else ""
            rec[cols[ci]["key"]] = num(raw)
        data.append(rec)
    return {
        "title": "Steuereinnahmen der Landeshauptstadt Magdeburg 2010–2025",
        "source": SOURCE,
        "unit": "EUR",
        "note": "Beträge in Euro. Leere Felder (z. B. erst ab 2025 erhobene "
                "Grundsteuer-Varianten) sind null.",
        "columns": cols,
        "rowCount": len(data),
        "rows": data,
    }


def convert_saetze():
    rows = read_rows(os.path.join(CSV, "steuersaetze-1991-2026.csv"))
    header = [h.strip() for h in rows[0]]
    keep = [i for i, h in enumerate(header) if h]
    NUMERIC = {"Veranlagungsjahr", "Tarif", "Mindestbetrag", "Höchstbetrag"}
    cols = []
    for i in keep:
        h = header[i]
        cols.append({"key": slug(h), "label": h,
                     "type": "number" if h in NUMERIC else "string"})
    data = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        rec = {}
        for ci, i in enumerate(keep):
            raw = (r[i] if i < len(r) else "").strip()
            h = header[i]
            rec[cols[ci]["key"]] = num(raw) if h in NUMERIC else (raw or None)
        data.append(rec)
    return {
        "title": "Steuersätze und Hebesätze der Landeshauptstadt Magdeburg 1991–2026",
        "source": SOURCE,
        "note": "Eine Zeile je Abgabenart und Veranlagungsjahr. 'Tarif' ist je "
                "nach 'Waehrung' ein Prozentsatz (Hebesatz) oder ein EUR-Betrag.",
        "columns": cols,
        "rowCount": len(data),
        "rows": data,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    datasets = {
        "steuereinnahmen-2010-2025.json": convert_einnahmen(),
        "steuersaetze-1991-2026.json": convert_saetze(),
    }
    index = {"source": SOURCE, "datasets": []}
    for name, ds in datasets.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(ds, f, ensure_ascii=False, indent=2)
            f.write("\n")
        index["datasets"].append({
            "path": name, "title": ds["title"],
            "rowCount": ds["rowCount"], "columnCount": len(ds["columns"]),
        })
        print(f"{name}: {ds['rowCount']} rows, {len(ds['columns'])} cols")
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
