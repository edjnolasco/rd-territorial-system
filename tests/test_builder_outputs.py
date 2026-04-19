from pathlib import Path
import json
import zipfile
import pandas as pd

from rd_territorial_system.builder import build_from_one_gadm


def _write_zip(path: Path, payload: dict) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(path.name.replace(".zip", ""), json.dumps(payload))


def test_build_v2_0_outputs_reports(tmp_path, monkeypatch) -> None:
    one_dir = tmp_path / "one"
    one_dir.mkdir()
    (one_dir / "one.csv").write_text(
        "provincia,municipio\n"
        "Distrito Nacional,Santo Domingo de Guzmán\n"
        "Santo Domingo,Inexistente\n",
        encoding="utf-8",
    )

    adm1 = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"NAME_1": "Distrito Nacional", "ID_1": "RD-01"}, "geometry": None},
            {"type": "Feature", "properties": {"NAME_1": "Santo Domingo", "ID_1": "RD-32"}, "geometry": None},
        ],
    }
    adm2 = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"NAME_1": "Distrito Nacional", "NAME_2": "Santo Domingo de Guzman", "ID_1": "RD-01", "ID_2": "RD-01-01"}, "geometry": None},
        ],
    }

    adm1_zip = tmp_path / "gadm41_DOM_1.json.zip"
    adm2_zip = tmp_path / "gadm41_DOM_2.json.zip"
    _write_zip(adm1_zip, adm1)
    _write_zip(adm2_zip, adm2)

    out_dir = tmp_path / "processed"
    out_dir.mkdir()

    monkeypatch.setattr("rd_territorial_system.ingestion.ONE_RAW_DIR", one_dir)
    monkeypatch.setattr("rd_territorial_system.builder.GADM_ADM1_ZIP", adm1_zip)
    monkeypatch.setattr("rd_territorial_system.builder.GADM_ADM2_ZIP", adm2_zip)
    monkeypatch.setattr("rd_territorial_system.builder.PROVINCES_OUTPUT", out_dir / "provinces.geojson")
    monkeypatch.setattr("rd_territorial_system.builder.MUNICIPALITIES_OUTPUT", out_dir / "municipalities.geojson")
    monkeypatch.setattr("rd_territorial_system.builder.MASTER_OUTPUT", out_dir / "territorial_master.csv")
    monkeypatch.setattr("rd_territorial_system.builder.MATCH_REPORT_OUTPUT", out_dir / "match_report.csv")
    monkeypatch.setattr("rd_territorial_system.builder.COVERAGE_REPORT_OUTPUT", out_dir / "coverage_report.csv")
    monkeypatch.setattr("rd_territorial_system.builder.INGESTION_REPORT_OUTPUT", out_dir / "ingestion_report.json")
    monkeypatch.setattr("rd_territorial_system.builder.UNMATCHED_MUNICIPALITIES_OUTPUT", out_dir / "unmatched_municipalities.csv")
    monkeypatch.setattr("rd_territorial_system.builder.LOW_CONFIDENCE_OUTPUT", out_dir / "low_confidence_matches.csv")

    summary = build_from_one_gadm(low_confidence_threshold=90)
    assert summary["master_rows"] == 2
    assert summary["municipality_unmatched"] == 1

    unmatched = pd.read_csv(out_dir / "unmatched_municipalities.csv")
    assert len(unmatched) == 1
