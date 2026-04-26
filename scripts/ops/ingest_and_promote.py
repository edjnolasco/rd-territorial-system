import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

MASTER_CSV = Path("data/catalog/current/rd_territorial_master.csv")
CANDIDATE_CSV = Path("data/catalog/current/rd_territorial_master_candidate.csv")
MANIFEST = Path("data/catalog/config/provinces_manifest.json")


def codes(path: Path) -> list[str]:
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    return sorted(
        df["province_code"].dropna().astype(str).str.zfill(2).unique().tolist()
    )


def run(cmd: list[str]) -> None:
    print("\n$ " + " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def assert_codes(path: Path, expected: list[str], label: str) -> None:
    actual = codes(path)
    expected = sorted([str(x).zfill(2) for x in expected])

    print(f"{label} expected:", expected)
    print(f"{label} actual  :", actual)

    if actual != expected:
        raise SystemExit(
            f"ERROR: {label} no coincide. expected={expected}, actual={actual}"
        )


def promote() -> None:
    shutil.copy2(CANDIDATE_CSV, MASTER_CSV)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--province-code", required=True)
    parser.add_argument("--expected-before", nargs="+", required=True)
    parser.add_argument("--expected-after", nargs="+", required=True)
    args = parser.parse_args()

    province_code = str(args.province_code).zfill(2)

    # -------------------------------
    # 1. Validar estado actual
    # -------------------------------
    assert_codes(MASTER_CSV, args.expected_before, "master before")

    # -------------------------------
    # 2. Generar candidate (CSV-only)
    # -------------------------------
    if province_code == "02":
        run([
            "python", "scripts/build_master_catalog.py",
            "--ingest-azua",
            # 🔥 CAMBIO: data/raw → data_pipeline/raw
            "--azua-txt", "data_pipeline/raw/azua/azua_completo.txt",
            "--master-catalog", str(MASTER_CSV),
            "--output-catalog", str(CANDIDATE_CSV),
        ])
    else:
        run([
            "python", "scripts/build_master_catalog.py",
            "--ingest-province",
            "--manifest-path", str(MANIFEST),
            "--province-code", province_code,
            "--master-catalog", str(MASTER_CSV),
            "--output-catalog", str(CANDIDATE_CSV),
        ])

    # -------------------------------
    # 3. Validaciones (CSV-only)
    # -------------------------------
    run([
        "python", "scripts/ops/check_candidate.py",  # 🔥 CAMBIO
        "--candidate", str(CANDIDATE_CSV),
        "--province-code", province_code,
    ])

    run([
        "python", "scripts/ops/check_expected_provinces.py",  # 🔥 CAMBIO
        "--candidate", str(CANDIDATE_CSV),
        "--expected", *args.expected_after,
    ])

    # -------------------------------
    # 4. Promoción
    # -------------------------------
    promote()

    # -------------------------------
    # 5. Validar master final
    # -------------------------------
    assert_codes(MASTER_CSV, args.expected_after, "master after")

    # -------------------------------
    # 6. Ejecutar tests
    # -------------------------------
    run(["python", "-m", "pytest", "-q"])

    mark_manifest_integrated(province_code)

    print("\nOK: provincia integrada, fijada en master y marcada en manifest.")


def mark_manifest_integrated(province_code: str) -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError(f"No existe el manifest: {MANIFEST}")

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    target = str(province_code).zfill(2)

    updated = False

    for item in data.get("provinces", []):
        if str(item.get("province_code", "")).zfill(2) == target:
            item["enabled"] = True
            item["integrated"] = True
            item["loaded"] = True
            item["status"] = "integrated"
            updated = True
            break

    if not updated:
        raise SystemExit(f"ERROR: provincia {target} no existe en el manifest.")

    MANIFEST.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()