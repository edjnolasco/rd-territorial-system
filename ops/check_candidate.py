import argparse
import os
import sys

import pandas as pd


def normalize_series_as_str(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip()


def run(candidate_path: str, province_code: str) -> None:
    if not os.path.exists(candidate_path):
        print(f"ERROR: No existe el archivo candidate: {candidate_path}")
        sys.exit(1)

    df = pd.read_csv(candidate_path, dtype=str, encoding="utf-8-sig").fillna("")

    required_columns = {
        "province_code",
        "composite_code",
        "parent_composite_code",
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        print(
            "ERROR: Faltan columnas requeridas en candidate: "
            f"{sorted(missing_columns)}"
        )
        sys.exit(1)

    province_code = str(province_code).zfill(2)
    province_rows = len(
        df[normalize_series_as_str(df["province_code"]).str.zfill(2) == province_code]
    )
    dupes = int(df["composite_code"].duplicated().sum())

    parent_series = normalize_series_as_str(df["parent_composite_code"])
    composite_series = normalize_series_as_str(df["composite_code"])

    parents_missing = df[
        (parent_series != "")
        & ~parent_series.isin(composite_series)
    ]
    missing_parent_count = len(parents_missing)

    print("candidate:", candidate_path)
    print("province_code:", province_code)
    print("rows:", province_rows)
    print("duplicated composite_code:", dupes)
    print("missing parent:", missing_parent_count)

    if province_rows == 0:
        print(f"ERROR: Provincia {province_code} no fue incorporada.")
        sys.exit(1)

    if dupes != 0:
        print("ERROR: Hay composite_code duplicados.")
        sys.exit(1)

    if missing_parent_count != 0:
        print("ERROR: Hay parent_composite_code sin correspondencia.")
        sys.exit(1)

    print("Candidate OK.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        required=True,
        help="Ruta al CSV candidate",
    )
    parser.add_argument(
        "--province-code",
        required=True,
        help="Código de provincia, por ejemplo: 04",
    )

    args = parser.parse_args()
    run(args.candidate, args.province_code)