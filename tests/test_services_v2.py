import pandas as pd

from rd_territorial_system.services import (
    load_coverage_report,
    load_low_confidence_matches,
    load_unmatched_municipalities,
)


def test_load_csv_outputs(tmp_path, monkeypatch) -> None:
    coverage = tmp_path / "coverage_report.csv"
    unmatched = tmp_path / "unmatched_municipalities.csv"
    low = tmp_path / "low_confidence_matches.csv"

    coverage.write_text("metric,value\nrows_total,2\n", encoding="utf-8")
    unmatched.write_text("province_name,municipality_name\nSanto Domingo,Inexistente\n", encoding="utf-8")
    low.write_text("province_name,municipality_name\n", encoding="utf-8")

    monkeypatch.setattr("rd_territorial_system.services.COVERAGE_REPORT_OUTPUT", coverage)
    monkeypatch.setattr("rd_territorial_system.services.UNMATCHED_MUNICIPALITIES_OUTPUT", unmatched)
    monkeypatch.setattr("rd_territorial_system.services.LOW_CONFIDENCE_OUTPUT", low)

    assert isinstance(load_coverage_report(), pd.DataFrame)
    assert isinstance(load_unmatched_municipalities(), pd.DataFrame)
    assert isinstance(load_low_confidence_matches(), pd.DataFrame)
