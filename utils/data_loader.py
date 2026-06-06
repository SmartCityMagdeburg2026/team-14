import json
import pandas as pd
import streamlit as st
from utils.constants import DATA_ROOT, MONTHS_DE


@st.cache_data
def load_kiss(relative_path: str) -> pd.DataFrame:
    """Load any KISS-MD dataset by path relative to data/kiss-md/json/."""
    path = DATA_ROOT / "kiss-md" / "json" / relative_path
    raw = json.loads(path.read_bytes())
    label_map = {c["key"]: c.get("label") or c["key"] for c in raw["columns"]}
    return pd.DataFrame(raw["rows"]).rename(columns=label_map)


@st.cache_data
def load_klima_monat() -> pd.DataFrame:
    path = DATA_ROOT / "sensor-data" / "json" / "klima-monat.json"
    raw = json.loads(path.read_bytes())
    df = pd.DataFrame(raw["rows"])
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


@st.cache_data
def load_klima_tag(year_from: int = 2000) -> pd.DataFrame:
    path = DATA_ROOT / "sensor-data" / "json" / "klima-tag.json"
    raw = json.loads(path.read_bytes())
    rows = [r for r in raw["rows"] if int(r["date"][:4]) >= year_from]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_mietspiegel(by: str = "wohnflaeche") -> pd.DataFrame:
    fname = "nach-wohnflaeche.json" if by == "wohnflaeche" else "nach-baualter.json"
    path = DATA_ROOT / "mietspiegel-2024" / fname
    raw = json.loads(path.read_bytes())
    df = pd.DataFrame(raw["rows"])
    df = df.dropna(subset=["nettokaltmiete_pro_qm"])
    return df


@st.cache_data
def load_steuereinnahmen() -> pd.DataFrame:
    path = DATA_ROOT / "steuereinnahmen" / "json" / "steuereinnahmen-2010-2025.json"
    raw = json.loads(path.read_bytes())
    df = pd.DataFrame(raw["rows"])
    # Coalesce Grundsteuer-B across the 2024/2025 split
    df["grundsteuer_b"] = (
        df.get("grundsteuer-b-bis-2024", pd.Series(0, index=df.index)).fillna(0)
        + df.get("grundsteuer-b-ab-2025-wohngrundstuecke", pd.Series(0, index=df.index)).fillna(0)
        + df.get("grundsteuer-b-ab-2025-nichtwohngrundstuecke", pd.Series(0, index=df.index)).fillna(0)
    )
    return df


def sort_by_month(df: pd.DataFrame, month_col: str = "Monat") -> pd.DataFrame:
    """Sort a DataFrame that has a German month-name column chronologically."""
    df = df.copy()
    df["_month_num"] = df[month_col].map(MONTHS_DE)
    df = df.sort_values("_month_num").drop(columns="_month_num")
    return df
