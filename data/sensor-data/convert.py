#!/usr/bin/env python3
"""Convert the raw DWD Klimaarchiv exports (station 03126 Magdeburg) under raw/
into clean, visualization-friendly JSON under json/.

For each granularity (daily, monthly) the long historical series and the recent
("aktuell") series are merged into one continuous timeline, deduplicated by date
(recent wins on overlap). Missing values (-999) become null; column codes are
annotated with the German label + unit taken from the Metadaten_Parameter file.

Run:  python3 convert.py        (no third-party deps, stdlib only)
"""
import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "json")

STATION = {
    "id": "03126",
    "name": "Magdeburg",
    "source": "DWD — Climate Data Center (Klimaarchiv Tag/Monat)",
    "url": "https://dwd.de/DE/leistungen/klimadatendeutschland/klarchivtagmonat.html",
    "license": "GeoNutzV / DWD — frei nutzbar mit Quellenangabe",
}

# Columns that are constant or bookkeeping → dropped from the row payload.
DROP = {"STATIONS_ID", "eor"}

# Fallback labels/units for columns the Metadaten_Parameter file does not list
# (quality flags, date columns).
FALLBACK = {
    "MESS_DATUM": ("Messdatum", None),
    "MESS_DATUM_BEGINN": ("Messzeitraum Beginn", None),
    "MESS_DATUM_ENDE": ("Messzeitraum Ende", None),
    "QN_3": ("Qualitätsniveau (Wind/Druck)", None),
    "QN_4": ("Qualitätsniveau (Niederschlag/Temperatur)", None),
    "QN_6": ("Qualitätsniveau (Niederschlag)", None),
}


def read_text(path):
    with open(path, encoding="latin-1") as f:
        return f.read()


def parse_param_meta(bundle_dir):
    """Parameter code -> (label, unit) from Metadaten_Parameter_*.txt (latin-1)."""
    out = {}
    for p in glob.glob(os.path.join(bundle_dir, "Metadaten_Parameter_*.txt")):
        rows = list(csv.reader(read_text(p).splitlines(), delimiter=";"))
        if not rows:
            continue
        head = [h.strip() for h in rows[0]]
        try:
            i_par = head.index("Parameter")
            i_desc = head.index("Parameterbeschreibung")
            i_unit = head.index("Einheit")
        except ValueError:
            continue
        for r in rows[1:]:
            if len(r) <= i_unit:
                continue
            code = r[i_par].strip()
            if not code:
                continue
            label = r[i_desc].strip()
            unit = r[i_unit].strip() or None
            if code not in out and label:
                out[code] = (label, unit)
    return out


def parse_produkt(path):
    """Return (header_codes, list_of_row_dicts) with -999 -> None, numbers coerced."""
    rows = list(csv.reader(read_text(path).splitlines(), delimiter=";"))
    header = [h.strip() for h in rows[0]]
    out = []
    for r in rows[1:]:
        if not r or all(c.strip() == "" for c in r):
            continue
        rec = {}
        for code, raw in zip(header, r):
            if code in DROP:
                continue
            v = raw.strip()
            if v == "" or v == "-999":
                rec[code] = None
            else:
                try:
                    rec[code] = int(v) if v.lstrip("-").isdigit() else float(v)
                except ValueError:
                    rec[code] = v
        out.append(rec)
    return header, out


def iso_date(yyyymmdd):
    s = str(yyyymmdd)
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def build(granularity, files, date_key):
    meta = {}
    for bundle_dir in {os.path.dirname(f) for f in files}:
        meta.update(parse_param_meta(bundle_dir))

    merged = {}          # date -> row
    col_order = []       # union of column codes, first-seen order
    for path in files:   # historical first, recent second (recent overwrites)
        header, recs = parse_produkt(path)
        for c in header:
            if c not in DROP and c not in col_order:
                col_order.append(c)
        for rec in recs:
            d = iso_date(rec[date_key])
            rec = {"date": d, **rec}
            merged[d] = rec

    dates = sorted(merged)
    rows = [merged[d] for d in dates]

    columns = []
    for code in col_order:
        label, unit = meta.get(code, FALLBACK.get(code, (None, None)))
        columns.append({"key": code, "label": label, "unit": unit})

    return {
        "station": STATION,
        "granularity": granularity,
        "period": {"start": dates[0], "end": dates[-1]} if dates else None,
        "columns": [{"key": "date", "label": "Datum (ISO)", "unit": None}] + columns,
        "rowCount": len(rows),
        "rows": rows,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    daily_files = sorted(glob.glob(os.path.join(RAW, "*daily*", "produkt_klima_tag_*.txt")))
    month_files = sorted(glob.glob(os.path.join(RAW, "*month*", "produkt_klima_monat_*.txt")))

    datasets = {
        "klima-tag.json": build("daily", daily_files, "MESS_DATUM"),
        "klima-monat.json": build("monthly", month_files, "MESS_DATUM_BEGINN"),
    }

    index = {"station": STATION, "datasets": []}
    for name, ds in datasets.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(ds, f, ensure_ascii=False, indent=2)
            f.write("\n")
        index["datasets"].append({
            "path": name,
            "granularity": ds["granularity"],
            "period": ds["period"],
            "rowCount": ds["rowCount"],
            "columnCount": len(ds["columns"]),
        })
        print(f"{name}: {ds['rowCount']} rows, {len(ds['columns'])} cols, "
              f"{ds['period']['start']}..{ds['period']['end']}")

    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
