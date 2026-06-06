from pathlib import Path

DATA_ROOT = Path(__file__).parent.parent / "data"

MONTHS_DE = {
    "Januar": 1, "Februar": 2, "März": 3, "April": 4,
    "Mai": 5, "Juni": 6, "Juli": 7, "August": 8,
    "September": 9, "Oktober": 10, "November": 11, "Dezember": 12,
}
MONTHS_DE_ORDER = list(MONTHS_DE.keys())

MD_TEAL = "#007A6E"
MD_ORANGE = "#E87722"
MD_BLUE = "#004B87"
MD_RED = "#C0392B"
MD_GREY = "#95A5A6"

PLOTLY_TEMPLATE = "plotly_white"

LAT, LON = 52.1205, 11.6276
