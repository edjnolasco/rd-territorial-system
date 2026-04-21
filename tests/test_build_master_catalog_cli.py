from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_master_catalog import main


def _write_text(path: Path, content: str, encoding: str = "utf-8-sig") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def _read_csv(path: Path) -> pd.DataFrame:
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise ValueError(f"No se pudo leer {path}. Último error: {last_error}")


def _run_cli(args: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_master_catalog.py", *args])
    main()


def test_cli_build_replace_generates_csv_parquet_and_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "dn.txt"
    output_csv = tmp_path / "catalog" / "rd_territorial_master.csv"
    output_parquet = tmp_path / "catalog" / "rd_territorial_master.parquet"
    metadata_path = tmp_path / "catalog" / "build_metadata.json"

    content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 00 00 00 000 00 Distrito Nacional
10 01 01 00 00 000 00 Santo Domingo de Guzmán
10 01 01 01 01 001 03 Brisas del Norte
"""
    _write_text(input_path, content)

    _run_cli(
        [
            "--input",
            str(input_path),
            "--output-csv",
            str(output_csv),
            "--output-parquet",
            str(output_parquet),
            "--metadata-path",
            str(metadata_path),
            "--source-label",
            "ONE 2021",
            "--valid-from",
            "2021-01-01",
        ],
        monkeypatch,
    )

    assert output_csv.exists()
    assert output_parquet.exists()
    assert metadata_path.exists()

    df = _read_csv(output_csv)
    assert len(df) == 3
    assert set(df["composite_code"]) == {
        "10-01-00-00-00-000-00",
        "10-01-01-00-00-000-00",
        "10-01-01-01-01-001-03",
    }

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["mode"] == "replace"
    assert metadata["input_rows"] == 3
    assert metadata["new_rows_transformed"] == 3
    assert metadata["final_rows"] == 3
    assert metadata["source_label"] == "ONE 2021"


def test_cli_append_adds_new_rows_without_overwriting_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    base_input = tmp_path / "dn_base.txt"
    append_input = tmp_path / "dn_append.txt"
    output_csv = tmp_path / "catalog" / "rd_territorial_master.csv"
    output_parquet = tmp_path / "catalog" / "rd_territorial_master.parquet"

    base_content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 00 00 00 000 00 Distrito Nacional
"""
    append_content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 01 00 00 000 00 Santo Domingo de Guzmán
10 01 01 01 01 001 00 Los Peralejos
"""

    _write_text(base_input, base_content)
    _write_text(append_input, append_content)

    _run_cli(
        [
            "--input",
            str(base_input),
            "--output-csv",
            str(output_csv),
            "--output-parquet",
            str(output_parquet),
            "--source-label",
            "ONE 2021",
        ],
        monkeypatch,
    )

    _run_cli(
        [
            "--input",
            str(append_input),
            "--output-csv",
            str(output_csv),
            "--output-parquet",
            str(output_parquet),
            "--source-label",
            "ONE 2021",
            "--append",
        ],
        monkeypatch,
    )

    df = _read_csv(output_csv)
    assert len(df) == 3
    assert set(df["composite_code"]) == {
        "10-01-00-00-00-000-00",
        "10-01-01-00-00-000-00",
        "10-01-01-01-01-001-00",
    }

    province_row = df[df["composite_code"] == "10-01-00-00-00-000-00"].iloc[0]
    assert province_row["name"] == "Distrito Nacional"


def test_cli_append_overwrite_existing_replaces_matching_composite_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    base_input = tmp_path / "dn_base.txt"
    overwrite_input = tmp_path / "dn_overwrite.txt"
    output_csv = tmp_path / "catalog" / "rd_territorial_master.csv"

    base_content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 00 00 00 000 00 Distrito Nacional
"""
    overwrite_content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 00 00 00 000 00 Distrito Nacional Actualizado
"""

    _write_text(base_input, base_content)
    _write_text(overwrite_input, overwrite_content)

    _run_cli(
        [
            "--input",
            str(base_input),
            "--output-csv",
            str(output_csv),
            "--source-label",
            "ONE 2021",
            "--notes",
            "base row",
        ],
        monkeypatch,
    )

    _run_cli(
        [
            "--input",
            str(overwrite_input),
            "--output-csv",
            str(output_csv),
            "--source-label",
            "ONE 2024",
            "--notes",
            "overwrite row",
            "--append",
            "--overwrite-existing",
            "--skip-parquet",
        ],
        monkeypatch,
    )

    df = _read_csv(output_csv)
    assert len(df) == 1

    row = df.iloc[0]
    assert row["composite_code"] == "10-01-00-00-00-000-00"
    assert row["name"] == "Distrito Nacional Actualizado"
    assert row["source"] == "ONE 2024"
    assert row["notes"] == "overwrite row"


def test_cli_skip_parquet_only_writes_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "dn.txt"
    output_csv = tmp_path / "catalog" / "rd_territorial_master.csv"
    output_parquet = tmp_path / "catalog" / "rd_territorial_master.parquet"

    content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 00 00 00 000 00 Distrito Nacional
"""
    _write_text(input_path, content)

    _run_cli(
        [
            "--input",
            str(input_path),
            "--output-csv",
            str(output_csv),
            "--output-parquet",
            str(output_parquet),
            "--source-label",
            "ONE 2021",
            "--skip-parquet",
        ],
        monkeypatch,
    )

    assert output_csv.exists()
    assert not output_parquet.exists()


def test_cli_output_csv_is_utf8_sig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    input_path = tmp_path / "dn.txt"
    output_csv = tmp_path / "catalog" / "rd_territorial_master.csv"

    content = """Región Provincia Municipio Distrito municipal Sección Barrio/paraje Sub-barrio Toponimia o Nombre
10 01 01 00 00 000 00 Santo Domingo de Guzmán
10 01 01 01 01 001 02 Los Ángeles
"""
    _write_text(input_path, content)

    _run_cli(
        [
            "--input",
            str(input_path),
            "--output-csv",
            str(output_csv),
            "--source-label",
            "ONE 2021",
            "--skip-parquet",
        ],
        monkeypatch,
    )

    raw = output_csv.read_bytes()
    # UTF-8 BOM
    assert raw.startswith(b"\xef\xbb\xbf")

    df = pd.read_csv(output_csv, encoding="utf-8-sig")
    assert "Santo Domingo de Guzmán" in set(df["name"])
    assert "Los Ángeles" in set(df["name"])