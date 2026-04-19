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
    "municipality_name": [
        "municipality_name",
        "municipio",
        "nombre_municipio",
        "mun_name",
    ],
}


def load_geojson_from_zip(zip_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        json_members = [name for name in zf.namelist() if name.endswith(".json")]
        if not json_members:
            raise ValueError(f"No se encontró JSON dentro de {zip_path}")
        with zf.open(json_members[0]) as f:
            return json.load(f)


def _rename_semantic_columns(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, str]]:
    normalized_map = {normalize_text(str(col)): col for col in df.columns}
    renames: dict[str, str] = {}

    for target, candidates in COLUMN_CANDIDATES.items():
        for candidate in candidates:
            source = normalized_map.get(normalize_text(candidate))
            if source:
                renames[source] = target
                break

    return df.rename(columns=renames), renames


def discover_one_main_table(one_dir: Path | None = None) -> Path:
    target_dir = Path(one_dir) if one_dir is not None else Path(ONE_RAW_DIR)

    if not target_dir.exists():
        raise FileNotFoundError(f"No existe el directorio ONE: {target_dir}")

    candidates = sorted(
        [
            p
            for p in target_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in {".csv", ".xlsx"}
            and "district" not in p.name.lower()
        ]
    )

    if not candidates:
        raise FileNotFoundError(
            f"No se encontró archivo CSV/XLSX principal en {target_dir}"
        )

    return candidates[0]


def profile_excel_sheets(path: Path) -> list[dict[str, Any]]:
    xls = pd.ExcelFile(path)
    profiles: list[dict[str, Any]] = []

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name)
            _, renames = _rename_semantic_columns(df)
            profiles.append(
                {
                    "sheet_name": sheet_name,
                    "columns_original": [str(col) for col in df.columns],
                    "columns_mapped": renames,
                    "rows": int(len(df)),
                    "has_province_name": "province_name" in set(renames.values()),
                    "has_municipality_name": "municipality_name"
                    in set(renames.values()),
                    "readable": True,
                }
            )
        except Exception as exc:  # pragma: no cover
            profiles.append(
                {
                    "sheet_name": sheet_name,
                    "columns_original": [],
                    "columns_mapped": {},
                    "rows": 0,
                    "has_province_name": False,
                    "has_municipality_name": False,
                    "readable": False,
                    "error": str(exc),
                }
            )

    return profiles


def select_best_excel_sheet(path: Path) -> str:
    profiles = profile_excel_sheets(path)
    best: dict[str, Any] | None = None
    best_score = -1.0

    for profile in profiles:
        if not profile.get("readable", True):
            continue

        score = 0.0
        if profile["has_province_name"]:
            score += 10.0
        if profile["has_municipality_name"]:
            score += 10.0
        score += min(profile["rows"], 1000) / 1000.0

        if score > best_score:
            best = profile
            best_score = score

    if best is None:
        raise ValueError(f"No fue posible seleccionar una hoja utilizable en {path}")

    return str(best["sheet_name"])


def load_one_table(
    path: Path,
    sheet_name: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = Path(path)

    report: dict[str, Any] = {
        "source_path": str(path.resolve()),
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
        selected = sheet_name if sheet_name is not None else select_best_excel_sheet(path)
        report["sheet_selected"] = selected
        df = pd.read_excel(path, sheet_name=selected)
    else:
        raise ValueError(f"Formato ONE no soportado: {path.suffix}")

    report["columns_original"] = [str(col) for col in df.columns]
    df, renames = _rename_semantic_columns(df)
    report["columns_mapped"] = renames

    return df, report


def load_one_hierarchy_auto(
    path: Path | None = None,
    sheet_name: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    target = Path(path) if path is not None else discover_one_main_table()
    df, report = load_one_table(target, sheet_name=sheet_name)

    required = {"province_name", "municipality_name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Faltan columnas obligatorias en archivo ONE: {sorted(missing)}"
        )

    return df, report