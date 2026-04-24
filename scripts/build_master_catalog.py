from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Asegura que la raíz del repo esté en sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from rd_territorial_system.normalization import normalize_text  # noqa: E402


COLUMN_ALIASES = {
    "región": "region_code",
    "region": "region_code",
    "provincia": "province_code",
    "municipio": "municipality_code",
    "distrito municipal": "district_municipal_code",
    "distrito_municipal": "district_municipal_code",
    "sección": "section_code",
    "seccion": "section_code",
    "barrio/paraje": "barrio_paraje_code",
    "barrio_paraje": "barrio_paraje_code",
    "sub-barrio": "sub_barrio_code",
    "sub_barrio": "sub_barrio_code",
    "toponimia o nombre": "name",
    "nombre": "name",
}

REQUIRED_COLUMNS = [
    "region_code",
    "province_code",
    "municipality_code",
    "district_municipal_code",
    "section_code",
    "barrio_paraje_code",
    "sub_barrio_code",
    "name",
]

CATALOG_COLUMNS = [
    "region_code",
    "province_code",
    "municipality_code",
    "district_municipal_code",
    "section_code",
    "barrio_paraje_code",
    "sub_barrio_code",
    "level",
    "name",
    "official_name",
    "normalized_name",
    "parent_composite_code",
    "composite_code",
    "full_path",
    "is_official",
    "source",
    "valid_from",
    "valid_to",
    "notes",
]

LEVEL_ORDER = (
    "province",
    "municipality",
    "district_municipal",
    "section",
    "barrio_paraje",
    "sub_barrio",
    "toponym",
)

TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

CODE_COLUMNS = [
    "region_code",
    "province_code",
    "municipality_code",
    "district_municipal_code",
    "section_code",
    "barrio_paraje_code",
    "sub_barrio_code",
    "parent_composite_code",
    "composite_code",
]

TXT_DATA_LINE_RE = re.compile(
    r"""
    ^(?P<region>\d{2})\s+
    (?P<province>\d{2})\s+
    (?P<municipality>\d{2})\s+
    (?P<district_municipal>\d{2})\s+
    (?P<section>\d{2})\s+
    (?P<barrio_paraje>\d{3})\s+
    (?P<sub_barrio>\d{2})\s+
    (?P<name>.+?)\s*$
    """,
    re.VERBOSE,
)

DEFAULT_AZUA_TXT = Path("data/raw/azua/azua_completo.txt")
DEFAULT_MASTER_CATALOG = Path("data/catalog/current/rd_territorial_master.csv")
DEFAULT_OUTPUT_CATALOG = Path("data/catalog/current/rd_territorial_master_candidate.csv")


def _clean_header(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _standardize_columns(columns: list[str]) -> list[str]:
    result = []
    for col in columns:
        key = _clean_header(col)
        result.append(COLUMN_ALIASES.get(key, key))
    return result


def _normalize_code(value: Any, width: int) -> str:
    text = str(value if value is not None else "").strip()
    if text == "" or text.lower() == "nan":
        return "0".zfill(width)
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(width)


def _clean_name(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _cast_code_columns_for_merge(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    inferred_code_cols = [
        col for col in df.columns if col.endswith("_code") or col == "composite_code"
    ]

    for col in set(CODE_COLUMNS + inferred_code_cols):
        if col in df.columns:
            df[col] = df[col].fillna("").astype("string")

    return df


def _catalog_province_codes(df: pd.DataFrame) -> list[str]:
    if df.empty or "province_code" not in df.columns:
        return []

    return sorted(
        {
            str(value).replace(".0", "").strip().zfill(2)
            for value in df["province_code"].dropna().astype(str)
            if str(value).strip() != ""
        }
    )


def _validate_candidate_accumulated(
    *,
    existing_df: pd.DataFrame,
    final_df: pd.DataFrame,
    expected_new_code: str,
) -> None:
    master_codes = _catalog_province_codes(existing_df)
    actual_codes = _catalog_province_codes(final_df)
    expected_codes = sorted(set(master_codes + [str(expected_new_code).zfill(2)]))

    if actual_codes != expected_codes:
        raise AssertionError(
            "El candidate no preserva el acumulado esperado. "
            f"Esperado={expected_codes}, observado={actual_codes}"
        )


def build_composite_code(row: dict[str, Any]) -> str:
    return "-".join(
        [
            _normalize_code(row.get("region_code"), 2),
            _normalize_code(row.get("province_code"), 2),
            _normalize_code(row.get("municipality_code"), 2),
            _normalize_code(row.get("district_municipal_code"), 2),
            _normalize_code(row.get("section_code"), 2),
            _normalize_code(row.get("barrio_paraje_code"), 3),
            _normalize_code(row.get("sub_barrio_code"), 2),
        ]
    )


def infer_level(row: dict[str, Any]) -> str:
    sub_barrio_code = _normalize_code(row.get("sub_barrio_code"), 2)
    barrio_paraje_code = _normalize_code(row.get("barrio_paraje_code"), 3)
    section_code = _normalize_code(row.get("section_code"), 2)
    district_municipal_code = _normalize_code(row.get("district_municipal_code"), 2)
    municipality_code = _normalize_code(row.get("municipality_code"), 2)
    province_code = _normalize_code(row.get("province_code"), 2)

    if sub_barrio_code != "00":
        return "sub_barrio"
    if barrio_paraje_code != "000":
        return "barrio_paraje"
    if section_code != "00":
        return "section"
    if district_municipal_code != "00":
        return "district_municipal"
    if municipality_code != "00":
        return "municipality"
    if province_code != "00":
        return "province"
    return "toponym"


def build_parent_code(row: dict[str, Any], level: str) -> str:
    region_code = _normalize_code(row.get("region_code"), 2)
    province_code = _normalize_code(row.get("province_code"), 2)
    municipality_code = _normalize_code(row.get("municipality_code"), 2)
    district_municipal_code = _normalize_code(row.get("district_municipal_code"), 2)
    section_code = _normalize_code(row.get("section_code"), 2)
    barrio_paraje_code = _normalize_code(row.get("barrio_paraje_code"), 3)

    if level == "province":
        return ""
    if level == "municipality":
        return f"{region_code}-{province_code}-00-00-00-000-00"
    if level == "district_municipal":
        return f"{region_code}-{province_code}-{municipality_code}-00-00-000-00"
    if level == "section":
        return (
            f"{region_code}-{province_code}-{municipality_code}-"
            f"{district_municipal_code}-00-000-00"
        )
    if level == "barrio_paraje":
        return (
            f"{region_code}-{province_code}-{municipality_code}-"
            f"{district_municipal_code}-{section_code}-000-00"
        )
    if level == "sub_barrio":
        return (
            f"{region_code}-{province_code}-{municipality_code}-"
            f"{district_municipal_code}-{section_code}-{barrio_paraje_code}-00"
        )
    return ""


def _read_csv_with_fallback(path: Path) -> pd.DataFrame:
    last_error = None

    for encoding in TEXT_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding, dtype=str).fillna("")
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(f"No se pudo leer el CSV {path}. Último error: {last_error}")


def _read_txt_with_fallback(path: Path) -> pd.DataFrame:
    last_error = None
    raw = None

    for encoding in TEXT_ENCODINGS:
        try:
            raw = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc

    if raw is None:
        raise ValueError(f"No se pudo leer el TXT {path}. Último error: {last_error}")

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"El TXT {path} está vacío")

    records: list[dict[str, Any]] = []

    for line in lines:
        match = TXT_DATA_LINE_RE.match(line)
        if not match:
            continue

        groups = match.groupdict()
        records.append(
            {
                "region_code": groups["region"],
                "province_code": groups["province"],
                "municipality_code": groups["municipality"],
                "district_municipal_code": groups["district_municipal"],
                "section_code": groups["section"],
                "barrio_paraje_code": groups["barrio_paraje"],
                "sub_barrio_code": groups["sub_barrio"],
                "name": _clean_name(groups["name"]),
            }
        )

    if not records:
        raise ValueError(
            f"No se pudieron extraer registros válidos desde {path}. "
            "Verifica el formato del TXT."
        )

    return pd.DataFrame(records)


def _read_source(path: Path, sheet_name: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return _read_csv_with_fallback(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet_name, dtype=str).fillna("")
    if suffix == ".txt":
        return _read_txt_with_fallback(path)

    raise ValueError(f"Formato no soportado: {suffix}")


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")


def _build_full_paths(records: list[dict[str, Any]]) -> None:
    by_code = {record["composite_code"]: record for record in records}

    for record in records:
        parent_code = record["parent_composite_code"]
        if not parent_code:
            record["full_path"] = record["name"]
            continue

        parts = [record["name"]]
        visited = set()

        while parent_code:
            if parent_code in visited:
                break
            visited.add(parent_code)

            parent = by_code.get(parent_code)
            if not parent:
                break

            parts.append(parent["name"])
            parent_code = parent["parent_composite_code"]

        record["full_path"] = " > ".join(reversed(parts))


def transform_source_to_catalog(
    df: pd.DataFrame,
    *,
    source_label: str,
    valid_from: str | None = None,
    valid_to: str | None = None,
    notes: str | None = None,
) -> pd.DataFrame:
    df = df.copy()
    df.columns = _standardize_columns(list(df.columns))
    _validate_columns(df)

    for col in REQUIRED_COLUMNS:
        if col == "name":
            df[col] = df[col].map(_clean_name)
        else:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )

    records: list[dict[str, Any]] = []

    for row in df.to_dict(orient="records"):
        level = infer_level(row)
        composite_code = build_composite_code(row)
        parent_composite_code = build_parent_code(row, level)
        name = _clean_name(row.get("name"))

        records.append(
            {
                "region_code": _normalize_code(row.get("region_code"), 2),
                "province_code": _normalize_code(row.get("province_code"), 2),
                "municipality_code": _normalize_code(row.get("municipality_code"), 2),
                "district_municipal_code": _normalize_code(
                    row.get("district_municipal_code"), 2
                ),
                "section_code": _normalize_code(row.get("section_code"), 2),
                "barrio_paraje_code": _normalize_code(
                    row.get("barrio_paraje_code"), 3
                ),
                "sub_barrio_code": _normalize_code(row.get("sub_barrio_code"), 2),
                "level": level,
                "name": name,
                "official_name": name,
                "normalized_name": normalize_text(name) or "",
                "parent_composite_code": parent_composite_code,
                "composite_code": composite_code,
                "full_path": "",
                "is_official": True,
                "source": source_label,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "notes": notes,
            }
        )

    _build_full_paths(records)

    out = pd.DataFrame(records, columns=CATALOG_COLUMNS)
    out = out.drop_duplicates(
        subset=["composite_code"],
        keep="first",
    ).reset_index(drop=True)

    level_rank = {name: idx for idx, name in enumerate(LEVEL_ORDER)}
    out["__level_rank"] = out["level"].map(level_rank)

    out = (
        out.sort_values(
            by=[
                "region_code",
                "province_code",
                "municipality_code",
                "district_municipal_code",
                "section_code",
                "barrio_paraje_code",
                "sub_barrio_code",
                "__level_rank",
                "name",
            ]
        )
        .drop(columns="__level_rank")
        .reset_index(drop=True)
    )

    return normalize_catalog_dtypes(out)


def load_existing_catalog(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=CATALOG_COLUMNS)

    df = _read_csv_with_fallback(path)

    missing = [col for col in CATALOG_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"El catálogo existente {path} no tiene las columnas esperadas. "
            f"Faltan: {missing}"
        )

    return normalize_catalog_dtypes(df[CATALOG_COLUMNS].copy())


def merge_catalogs(
    existing_df: pd.DataFrame,
    new_df: pd.DataFrame,
    *,
    overwrite: bool = True,
) -> pd.DataFrame:
    existing_df = normalize_catalog_dtypes(existing_df)
    new_df = normalize_catalog_dtypes(new_df)

    if existing_df.empty:
        merged = new_df.copy()
    else:
        base = existing_df.set_index("composite_code", drop=False)
        incoming = new_df.set_index("composite_code", drop=False)

        if overwrite:
            common_cols = [col for col in incoming.columns if col in base.columns]

            base = _cast_code_columns_for_merge(base)
            incoming = _cast_code_columns_for_merge(incoming)

            base.update(incoming[common_cols])
            only_new = incoming.loc[~incoming.index.isin(base.index)]
            merged = pd.concat([base, only_new], axis=0)
        else:
            only_new = incoming.loc[~incoming.index.isin(base.index)]
            merged = pd.concat([base, only_new], axis=0)

        merged = merged.reset_index(drop=True)

    level_rank = {name: idx for idx, name in enumerate(LEVEL_ORDER)}
    merged["__level_rank"] = merged["level"].map(level_rank)

    merged = (
        merged.sort_values(
            by=[
                "region_code",
                "province_code",
                "municipality_code",
                "district_municipal_code",
                "section_code",
                "barrio_paraje_code",
                "sub_barrio_code",
                "__level_rank",
                "name",
            ]
        )
        .drop(columns="__level_rank")
        .reset_index(drop=True)
    )

    return normalize_catalog_dtypes(merged[CATALOG_COLUMNS])


def normalize_catalog_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    string_columns = [
        "region_code",
        "province_code",
        "municipality_code",
        "district_municipal_code",
        "section_code",
        "barrio_paraje_code",
        "sub_barrio_code",
        "level",
        "name",
        "official_name",
        "normalized_name",
        "parent_composite_code",
        "composite_code",
        "full_path",
        "source",
        "valid_from",
        "valid_to",
        "notes",
    ]

    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].where(df[col].notna(), "")
            df[col] = df[col].map(lambda x: str(x).strip())

    if "is_official" in df.columns:
        df["is_official"] = df["is_official"].fillna(False).astype(bool)

    return df


def write_catalog_csv(
    df: pd.DataFrame,
    *,
    output_csv: Path,
    output_metadata: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    df = normalize_catalog_dtypes(df)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    if output_metadata and metadata is not None:
        output_metadata.parent.mkdir(parents=True, exist_ok=True)
        output_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def ingest_azua_to_catalog(
    azua_txt_path: str,
    master_catalog_path: str,
    output_catalog_path: str | None = None,
    *,
    source_label: str = "AZUA_TXT",
    valid_from: str | None = None,
    valid_to: str | None = None,
    notes: str | None = "Ingesta de Azua desde TXT estructurado.",
    overwrite_existing: bool = False,
) -> Path:
    azua_path = Path(azua_txt_path)
    if not azua_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de Azua en: {azua_path}\n"
            "Colócalo en data/raw/azua/azua_completo.txt "
            "o usa --azua-txt con una ruta válida."
        )

    master_path = Path(master_catalog_path)
    destination = Path(output_catalog_path) if output_catalog_path else master_path

    df_source = _read_source(azua_path)
    df_new = transform_source_to_catalog(
        df_source,
        source_label=source_label,
        valid_from=valid_from,
        valid_to=valid_to,
        notes=notes,
    )

    df_existing = load_existing_catalog(master_path)

    if not overwrite_existing:
        collisions = set(df_existing["composite_code"]).intersection(
            set(df_new["composite_code"])
        )
        if collisions:
            sample = sorted(collisions)[:20]
            raise AssertionError(
                "Colisión de composite_code detectada contra el catálogo maestro. "
                f"Ejemplos: {sample}"
            )

    df_final = merge_catalogs(
        df_existing,
        df_new,
        overwrite=overwrite_existing,
    )

    _validate_candidate_accumulated(
        existing_df=df_existing,
        final_df=df_final,
        expected_new_code="02",
    )

    write_catalog_csv(
        df_final,
        output_csv=destination,
    )

    return destination


def load_manifest(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el manifiesto: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if "provinces" not in data or not isinstance(data["provinces"], list):
        raise ValueError("El manifiesto debe contener una lista 'provinces'.")

    return data


def get_manifest_entry(
    manifest: dict[str, Any],
    *,
    province_code: str | None = None,
    province_name: str | None = None,
) -> dict[str, Any]:
    candidates = manifest.get("provinces", [])

    if province_code:
        matches = [
            item
            for item in candidates
            if str(item.get("province_code", "")).zfill(2)
            == str(province_code).zfill(2)
        ]
    elif province_name:
        target = str(province_name).strip().casefold()
        matches = [
            item
            for item in candidates
            if str(item.get("province_name", "")).strip().casefold() == target
        ]
    else:
        raise ValueError("Debes indicar province_code o province_name.")

    if not matches:
        raise ValueError(
            "No se encontró una entrada en el manifiesto para "
            f"province_code={province_code} province_name={province_name}"
        )

    if len(matches) > 1:
        raise ValueError(
            "Se encontraron múltiples entradas en el manifiesto para "
            f"province_code={province_code} province_name={province_name}"
        )

    entry = matches[0]
    if not bool(entry.get("enabled", True)):
        raise ValueError(
            f"La provincia {entry.get('province_name')} "
            f"({entry.get('province_code')}) está deshabilitada en el manifiesto."
        )

    return entry


def ingest_province_from_manifest(
    manifest_path: str | Path,
    *,
    province_code: str | None,
    province_name: str | None,
    master_catalog_path: str,
    output_catalog_path: str | None = None,
    overwrite_existing: bool = False,
    valid_from: str | None = None,
    valid_to: str | None = None,
    notes: str | None = None,
) -> Path:
    manifest = load_manifest(manifest_path)
    entry = get_manifest_entry(
        manifest,
        province_code=province_code,
        province_name=province_name,
    )

    input_file = Path(entry["input_path"])
    if not input_file.exists():
        raise FileNotFoundError(
            f"No se encontró la fuente declarada en el manifiesto: {input_file}"
        )

    source_label = entry.get("source_label", f'{entry["province_name"].upper()}_TXT')
    manifest_notes = entry.get("notes")
    final_notes = notes if notes is not None else manifest_notes
    expected_code = str(entry["province_code"]).zfill(2)

    df_source = _read_source(input_file)
    df_source.columns = _standardize_columns(list(df_source.columns))

    if "province_code" not in df_source.columns:
        raise ValueError(
            "La fuente no contiene la columna province_code después de normalizar "
            "encabezados."
        )

    unique_province_codes = sorted(
        {
            str(value).replace(".0", "").strip().zfill(2)
            for value in df_source["province_code"].dropna().astype(str)
            if str(value).strip() != ""
        }
    )

    if unique_province_codes != [expected_code]:
        raise AssertionError(
            "La fuente no corresponde exclusivamente a la provincia declarada "
            "en el manifiesto. "
            f"Esperado={[expected_code]}, observado={unique_province_codes}"
        )

    df_new = transform_source_to_catalog(
        df_source,
        source_label=source_label,
        valid_from=valid_from,
        valid_to=valid_to,
        notes=final_notes,
    )

    master_path = Path(master_catalog_path)
    df_existing = load_existing_catalog(master_path)

    if not overwrite_existing:
        collisions = set(df_existing["composite_code"]).intersection(
            set(df_new["composite_code"])
        )
        if collisions:
            sample = sorted(collisions)[:20]
            raise AssertionError(
                "Colisión de composite_code detectada contra el catálogo maestro. "
                f"Ejemplos: {sample}"
            )

    df_final = merge_catalogs(
        df_existing,
        df_new,
        overwrite=overwrite_existing,
    )

    _validate_candidate_accumulated(
        existing_df=df_existing,
        final_df=df_final,
        expected_new_code=expected_code,
    )

    destination = Path(output_catalog_path) if output_catalog_path else master_path

    write_catalog_csv(
        df_final,
        output_csv=destination,
    )

    return destination


def validate_catalog_csv(csv_path: str) -> None:
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"No existe el catálogo CSV: {path}")

    df = _read_csv_with_fallback(path)

    missing = [col for col in CATALOG_COLUMNS if col not in df.columns]
    if missing:
        raise AssertionError(
            f"El catálogo CSV no tiene las columnas esperadas. Faltan: {missing}"
        )

    duplicated_codes = df[df["composite_code"].duplicated(keep=False)]
    if not duplicated_codes.empty:
        sample = duplicated_codes["composite_code"].dropna().astype(str).unique()[:20]
        raise AssertionError(
            "El catálogo contiene composite_code duplicados. "
            f"Ejemplos: {list(sample)}"
        )

    province_codes = _catalog_province_codes(df)
    if not province_codes:
        raise AssertionError("El catálogo no contiene province_code válidos.")

    print(f"Catálogo válido: {path}")
    print(f"Filas: {len(df)}")
    print(f"Provincias: {province_codes}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build RD territorial master catalog from source structure."
    )

    parser.add_argument(
        "--ingest-azua",
        action="store_true",
        help="Ejecuta el flujo de ingesta de Azua sobre el catálogo maestro existente.",
    )
    parser.add_argument(
        "--azua-txt",
        default=str(DEFAULT_AZUA_TXT),
        help="Ruta del TXT de Azua. Default: data/raw/azua/azua_completo.txt",
    )
    parser.add_argument(
        "--master-catalog",
        default=str(DEFAULT_MASTER_CATALOG),
        help="Ruta del catálogo maestro CSV base.",
    )
    parser.add_argument(
        "--output-catalog",
        default=str(DEFAULT_OUTPUT_CATALOG),
        help=(
            "Ruta del catálogo CSV de salida para ingesta incremental. "
            "Default: data/catalog/current/rd_territorial_master_candidate.csv"
        ),
    )
    parser.add_argument(
        "--input",
        required=False,
        help="Ruta del archivo fuente (.csv, .xlsx, .xls o .txt) para el flujo genérico.",
    )
    parser.add_argument(
        "--sheet-name",
        default=None,
        help="Nombre de hoja si la entrada es Excel.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_MASTER_CATALOG),
        help="Ruta del catálogo CSV de salida para el flujo genérico.",
    )
    parser.add_argument("--source-label", default="ONE", help="Etiqueta de fuente.")
    parser.add_argument("--valid-from", default=None, help="Fecha de vigencia inicial.")
    parser.add_argument("--valid-to", default=None, help="Fecha de vigencia final.")
    parser.add_argument("--notes", default=None, help="Notas para las filas generadas.")
    parser.add_argument(
        "--metadata-path",
        default=None,
        help="Ruta opcional para metadata JSON.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Fusiona contra el catálogo CSV existente en el flujo genérico.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="En modo append, si el composite_code ya existe, lo reemplaza.",
    )
    parser.add_argument(
        "--ingest-province",
        action="store_true",
        help="Ejecuta la ingesta de una provincia usando el manifiesto.",
    )
    parser.add_argument(
        "--manifest-path",
        default="data/catalog/config/provinces_manifest.json",
        help="Ruta del manifiesto de provincias.",
    )
    parser.add_argument(
        "--province-code",
        default=None,
        help="Código de provincia a ingerir desde el manifiesto.",
    )
    parser.add_argument(
        "--province-name",
        default=None,
        help="Nombre de provincia a ingerir desde el manifiesto.",
    )
    parser.add_argument(
        "--validate-catalog",
        action="store_true",
        help="Valida el catálogo CSV indicado por --master-catalog.",
    )

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # --------------------------------------
    # MODO 0: VALIDACIÓN CSV
    # --------------------------------------
    if args.validate_catalog:
        validate_catalog_csv(args.master_catalog)
        return

    # --------------------------------------
    # MODO 1: INGESTA AZUA
    # --------------------------------------
    if args.ingest_azua:
        destination = ingest_azua_to_catalog(
            azua_txt_path=args.azua_txt,
            master_catalog_path=args.master_catalog,
            output_catalog_path=args.output_catalog or None,
            source_label=(
                args.source_label if args.source_label != "ONE" else "AZUA_TXT"
            ),
            valid_from=args.valid_from,
            valid_to=args.valid_to,
            notes=args.notes or "Ingesta de Azua desde TXT estructurado.",
            overwrite_existing=args.overwrite_existing,
        )
        print(f"Catálogo CSV actualizado en: {destination}")
        return

    # --------------------------------------
    # MODO 2: INGESTA DESDE MANIFIESTO
    # --------------------------------------
    if args.ingest_province:
        if not args.province_code and not args.province_name:
            raise SystemExit(
                "Con --ingest-province debes indicar --province-code o --province-name."
            )

        destination = ingest_province_from_manifest(
            manifest_path=args.manifest_path,
            province_code=args.province_code,
            province_name=args.province_name,
            master_catalog_path=args.master_catalog,
            output_catalog_path=args.output_catalog or None,
            overwrite_existing=args.overwrite_existing,
            valid_from=args.valid_from,
            valid_to=args.valid_to,
            notes=args.notes,
        )
        print(f"Catálogo CSV actualizado desde manifiesto en: {destination}")
        return

    # --------------------------------------
    # MODO 3: FLUJO GENÉRICO
    # --------------------------------------
    if not args.input:
        raise SystemExit(
            "Debes indicar --input para el flujo genérico, "
            "o usar --ingest-azua / --ingest-province / --validate-catalog."
        )

    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    metadata_path = Path(args.metadata_path) if args.metadata_path else None

    df_source = _read_source(input_path, sheet_name=args.sheet_name)
    df_new = transform_source_to_catalog(
        df_source,
        source_label=args.source_label,
        valid_from=args.valid_from,
        valid_to=args.valid_to,
        notes=args.notes,
    )

    if args.append:
        df_existing = load_existing_catalog(output_csv)
        df_final = merge_catalogs(
            df_existing,
            df_new,
            overwrite=args.overwrite_existing,
        )
        mode = "append"
    else:
        df_final = df_new
        mode = "replace"

    metadata = {
        "mode": mode,
        "input": str(input_path),
        "output_csv": str(output_csv),
        "input_rows": int(len(df_source)),
        "new_rows_transformed": int(len(df_new)),
        "final_rows": int(len(df_final)),
        "levels": df_final["level"].value_counts().to_dict(),
        "source_label": args.source_label,
        "valid_from": args.valid_from,
        "valid_to": args.valid_to,
        "append": bool(args.append),
        "overwrite_existing": bool(args.overwrite_existing),
    }

    write_catalog_csv(
        df_final,
        output_csv=output_csv,
        output_metadata=metadata_path,
        metadata=metadata,
    )

    print(f"Catalog CSV generated: {output_csv}")
    print(f"Mode: {mode}")
    print(f"Rows in final catalog: {len(df_final)}")


if __name__ == "__main__":
    main()