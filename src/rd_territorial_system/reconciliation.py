from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import MUNICIPALITY_OVERRIDES_CSV
from .normalization import canonical_municipality, canonical_province


def load_municipality_overrides(path: Path = MUNICIPALITY_OVERRIDES_CSV) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}

    df = pd.read_csv(path)
    required = {"province_name", "municipality_name", "gadm_municipality_name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en municipality_overrides.csv: {sorted(missing)}")

    mapping = {}
    for _, row in df.iterrows():
        key = (
            canonical_province(row["province_name"]),
            canonical_municipality(row["municipality_name"]),
        )
        mapping[key] = canonical_municipality(row["gadm_municipality_name"])
    return mapping
