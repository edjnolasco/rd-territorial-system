from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from .config import ONE_RAW_DIR
from .normalization import normalize_text

COLUMN_CANDIDATES = {
    "province_name": ["province_name", "provincia", "nombre_provincia", "prov_name"],
    "municipality_name": ["municipality_name", "municipio", "nombre_municipio", "mun_name"],
}


def load_geojson_from_zip(zip_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        json_members = [name for name in zf.namelist() if name.endswith(".json")]
        if not json_members:
            raise ValueError(f"No se encontró JSON dentro de {zip_path}")
        with zf.open(json_members[0]) as f:
            return json.load(f)


def _rename_semantic_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    normalized_map = {normalize_text(col): col for col in df.columns}
    renames = {}

    for target, candidates in COLUMN_CANDIDATES.items():
        for candidate in candidates:
            source = normalized_map.get(normalize_text(candidate))
            if source:
                renames[source] = target
                break

    return df.rename(columns=renames), renames


def discover_one_main_table(one_dir: Path = ONE_RAW_DIR) -> Path:
    candidates = sorted([
        p for p in one_dir.iterdir()
        if p.suffix.lower() in {".csv", ".xlsx"} and "district" not in p.name.lower()
    ])
    if not candidates:
        raise FileNotFoundError(f"No se encontró archivo CSV/XLSX en {one_dir}")
    return candidates[0]


def profile_excel_sheets(path: Path) -> list[dict[str, Any]]:
    xls = pd.ExcelFile(path)
    profiles = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name)
        _, renames = _rename_semantic_columns(df)
        profiles.append({
            "sheet_name": sheet_name,
            "columns_original": list(df.columns),
            "columns_mapped": renames,
            "rows": int(len(df)),
            "has_province_name": "province_name" in set(renames.values()),
            "has_municipality_name": "municipality_name" in set(renames.values()),
        })
    return profiles


def select_best_excel_sheet(path: Path) -> str:
    profiles = profile_excel_sheets(path)
    best = None
    best_score = -1.0

    for profile in profiles:
        score = 0.0
        if profile["has_province_name"]:
            score += 10
        if profile["has_municipality_name"]:
            score += 10
        score += min(profile["rows"], 1000) / 1000.0
        if score > best_score:
            best = profile
            best_score = score

    if best is None:
        raise ValueError(f"No fue posible seleccionar una hoja utilizable en {path}")
    return best["sheet_name"]


def load_one_table(path: Path, sheet_name: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    report = {
        "source_path": str(path),
        "source_type": path.suffix.lower(),
        "sheet_selected": None,
        "sheet_profiles": [],
        "columns_original": [],
        "columns_mapped": {},
    }

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".xlsx":
        report["sheet_profiles"] = profile_excel_sheets(path)
        selected = sheet_name or select_best_excel_sheet(path)
        report["sheet_selected"] = selected
        df = pd.read_excel(path, sheet_name=selected)
    else:
        raise ValueError(f"Formato ONE no soportado: {path.suffix}")

    report["columns_original"] = list(df.columns)
    df, renames = _rename_semantic_columns(df)
    report["columns_mapped"] = renames
    return df, report


def load_one_hierarchy_auto(path: Path | None = None, sheet_name: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    target = path or discover_one_main_table()
    df, report = load_one_table(target, sheet_name=sheet_name)

    required = {"province_name", "municipality_name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas obligatorias en archivo ONE: {sorted(missing)}")

    return df, report
