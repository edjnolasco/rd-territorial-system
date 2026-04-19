import json
from rd_territorial_system.services import load_ingestion_report


def test_load_ingestion_report(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "ingestion_report.json"
    report_path.write_text(json.dumps({"source_type": ".xlsx", "sheet_selected": "Division"}), encoding="utf-8")
    monkeypatch.setattr("rd_territorial_system.services.INGESTION_REPORT_OUTPUT", report_path)
    report = load_ingestion_report()
    assert report["source_type"] == ".xlsx"
    assert report["sheet_selected"] == "Division"
