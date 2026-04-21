from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

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
            f"{region_code}-{province_code}-{municipality_code}-{district_municipal_code}-00-000-00"
        )
    if level == "barrio_paraje":
        return f"{region_code}-{province_code}-{municipality_code}-{district_municipal_code}-{section_code}-000-00"
    if level == "sub_barrio":
        return f"{region_code}-{province_code}-{municipality_code}-{district_municipal_code}-{section_code}-{barrio_paraje_code}-00"
    return ""


def _read_csv_with_fallback(path: Path) -> pd.DataFrame:
    last_error = None
    for encoding in TEXT_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"No se pudo leer el CSV {path}. Último error: {last_error}")


def _read_txt_with_fallback(path: Path) -> pd.DataFrame:
    last_error = None
    for encoding in TEXT_ENCODINGS:
        try:
            raw = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise ValueError(f"No se pudo leer el TXT {path}. Último error: {last_error}")

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"El TXT {path} está vacío")

    records: list[dict[str, Any]] = []

    # Se ignora la primera línea de encabezado.
    # Formato esperado por línea:
    # region province municipality district_municipal section barrio_paraje sub_barrio name...
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 8:
            continue

        record = {
            "region_code": parts[0],
            "province_code": parts[1],
            "municipality_code": parts[2],
            "district_municipal_code": parts[3],
            "section_code": parts[4],
            "barrio_paraje_code": parts[5],
            "sub_barrio_code": parts[6],
            "name": " ".join(parts[7:]).strip(),
        }
        records.append(record)

    if not records:
        raise ValueError(f"No se pudieron extraer registros válidos desde {path}")

    return pd.DataFrame(records)


def _read_source(path: Path, sheet_name: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return _read_csv_with_fallback(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet_name)
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
            df[col] = df[col].astype(str).str.replace(".0", "", regex=False).str.strip()

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
                "district_municipal_code": _normalize_code(row.get("district_municipal_code"), 2),
                "section_code": _normalize_code(row.get("section_code"), 2),
                "barrio_paraje_code": _normalize_code(row.get("barrio_paraje_code"), 3),
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
    out = out.drop_duplicates(subset=["composite_code"], keep="first").reset_index(drop=True)

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

    return out


def load_existing_catalog(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=CATALOG_COLUMNS)

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = _read_csv_with_fallback(path)

    missing = [col for col in CATALOG_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"El catálogo existente {path} no tiene las columnas esperadas. Faltan: {missing}"
        )

    return df[CATALOG_COLUMNS].copy()


def merge_catalogs(
    existing_df: pd.DataFrame,
    new_df: pd.DataFrame,
    *,
    overwrite: bool = True,
) -> pd.DataFrame:
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
            df[col] = df[col].where(df[col].notna(), None)
            df[col] = df[col].map(lambda x: str(x).strip() if x is not None else None)

    if "is_official" in df.columns:
        df["is_official"] = df["is_official"].fillna(False).astype(bool)

    return df


def write_outputs(
    df: pd.DataFrame,
    *,
    output_csv: Path,
    output_parquet: Path | None = None,
    output_metadata: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    df = normalize_catalog_dtypes(df)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    if output_parquet:
        output_parquet.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_parquet, index=False)

    if output_metadata and metadata is not None:
        output_metadata.parent.mkdir(parents=True, exist_ok=True)
        output_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build RD territorial master catalog from source structure."
    )
    parser.add_argument(
        "--input", required=True, help="Ruta del archivo fuente (.csv, .xlsx, .xls o .txt)"
    )
    parser.add_argument("--sheet-name", default=None, help="Nombre de hoja si la entrada es Excel")
    parser.add_argument(
        "--output-csv",
        default="data/catalog/current/rd_territorial_master.csv",
        help="Ruta del catálogo maestro CSV",
    )
    parser.add_argument(
        "--output-parquet",
        default="data/catalog/current/rd_territorial_master.parquet",
        help="Ruta del catálogo maestro Parquet",
    )
    parser.add_argument("--source-label", default="ONE", help="Etiqueta de fuente")
    parser.add_argument("--valid-from", default=None, help="Fecha de vigencia inicial")
    parser.add_argument("--valid-to", default=None, help="Fecha de vigencia final")
    parser.add_argument("--notes", default=None, help="Notas para las filas generadas")
    parser.add_argument("--skip-parquet", action="store_true", help="No generar Parquet")
    parser.add_argument("--metadata-path", default=None, help="Ruta opcional para metadata JSON")
    parser.add_argument(
        "--append", action="store_true", help="Fusiona contra el catálogo existente"
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="En modo --append, si el composite_code ya existe, lo reemplaza",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    output_parquet = None if args.skip_parquet else Path(args.output_parquet)
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
        "output_parquet": str(output_parquet) if output_parquet else None,
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

    write_outputs(
        df_final,
        output_csv=output_csv,
        output_parquet=output_parquet,
        output_metadata=metadata_path,
        metadata=metadata,
    )

    print(f"Catalog generated: {output_csv}")
    if output_parquet:
        print(f"Parquet generated: {output_parquet}")
    print(f"Mode: {mode}")
    print(f"Rows in final catalog: {len(df_final)}")


if __name__ == "__main__":
    main()
