import sys
import os
import argparse
import pandas as pd


def normalize_codes(values) -> list[str]:
    result = []
    for value in values:
        code = str(value).strip()
        if code:
            result.append(code.zfill(2))
    return sorted(set(result))


def run(candidate_path: str, expected_codes: list[str]) -> None:
    if not os.path.exists(candidate_path):
        print(f"ERROR: No existe el archivo candidate: {candidate_path}")
        sys.exit(1)

    # 🔥 CSV ONLY
    df = pd.read_csv(candidate_path, dtype=str, encoding="utf-8-sig").fillna("")

    if "province_code" not in df.columns:
        print("ERROR: El candidate no contiene la columna 'province_code'.")
        sys.exit(1)

    actual_codes = normalize_codes(df["province_code"].tolist())
    expected_codes = normalize_codes(expected_codes)

    print("expected:", expected_codes)
    print("actual  :", actual_codes)

    missing = sorted(set(expected_codes) - set(actual_codes))
    unexpected = sorted(set(actual_codes) - set(expected_codes))

    if missing:
        print("missing :", missing)

    if unexpected:
        print("unexpected:", unexpected)

    if actual_codes != expected_codes:
        print("ERROR: El acumulado de provincias no coincide con lo esperado.")
        sys.exit(1)

    print("Expected provinces OK.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        required=True,
        help="Ruta al CSV candidate",
    )
    parser.add_argument(
        "--expected",
        required=True,
        nargs="+",
        help="Lista de códigos de provincia esperados. Ej: 01 02 03 04",
    )

    args = parser.parse_args()
    run(args.candidate, args.expected)