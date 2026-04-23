import sys
import argparse
import pandas as pd


def run(candidate_path: str, province_code: str) -> None:
    df = pd.read_parquet(candidate_path)

    province_rows = len(df[df["province_code"] == province_code])
    dupes = int(df["composite_code"].duplicated().sum())

    parents_missing = df[
        df["parent_composite_code"].notna()
        & (df["parent_composite_code"].astype(str).str.strip() != "")
        & ~df["parent_composite_code"].isin(df["composite_code"])
    ]
    missing_parent_count = len(parents_missing)

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
        help="Ruta al parquet candidate"
    )
    parser.add_argument(
        "--province-code",
        required=True,
        help="Código de provincia (ej: 03)"
    )

    args = parser.parse_args()
    run(args.candidate, args.province_code)