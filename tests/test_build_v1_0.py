from pathlib import Path
import json
import zipfile
import pandas as pd

from rd_territorial_system.builder import build_from_one_gadm


def _write_zip(path: Path, payload: dict) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(path.name.replace(".zip", ""), json.dumps(payload))


def test_build_v1_6_with_sheet_name(tmp_path, monkeypatch) -> None:
    xlsx_path = tmp_path / "one_source.xlsx"

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame({"foo": [1]}).to_excel(writer, sheet_name="Notas", index=False)
        pd.DataFrame({
            "provincia": ["Distrito Nacional", "Santo Domingo"],
            "municipio": ["Santo Domingo de Guzmán", "Santo Domingo Norte"],
        }).to_excel(writer, sheet_name="Division", index=False)

    one_dir = tmp_path / "one"
    one_dir.mkdir()
    target = one_dir / "one_source.xlsx"
    target.write_bytes(xlsx_path.read_bytes())

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
            {"type": "Feature", "properties": {"NAME_1": "Santo Domingo", "NAME_2": "Santo Domingo Norte", "ID_1": "RD-32", "ID_2": "RD-32-02"}, "geometry": None},
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

    summary = build_from_one_gadm(sheet_name="Division")
    assert summary["provinces_output"] == 2
    assert summary["municipalities_output"] == 2

    report = json.loads((out_dir / "ingestion_report.json").read_text(encoding="utf-8"))
    assert report["sheet_selected"] == "Division"
    assert report["rows_input"] == 2
