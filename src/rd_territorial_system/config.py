from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RECONCILIATION_DIR = DATA_DIR / "reconciliation"

ONE_RAW_DIR = RAW_DATA_DIR / "one"
GADM_ADM1_ZIP = RAW_DATA_DIR / "gadm" / "gadm41_DOM_1.json.zip"
GADM_ADM2_ZIP = RAW_DATA_DIR / "gadm" / "gadm41_DOM_2.json.zip"

PROVINCES_OUTPUT = PROCESSED_DATA_DIR / "provinces.geojson"
MUNICIPALITIES_OUTPUT = PROCESSED_DATA_DIR / "municipalities.geojson"
MASTER_OUTPUT = PROCESSED_DATA_DIR / "territorial_master.csv"
MATCH_REPORT_OUTPUT = PROCESSED_DATA_DIR / "match_report.csv"
COVERAGE_REPORT_OUTPUT = PROCESSED_DATA_DIR / "coverage_report.csv"
INGESTION_REPORT_OUTPUT = PROCESSED_DATA_DIR / "ingestion_report.json"
UNMATCHED_MUNICIPALITIES_OUTPUT = PROCESSED_DATA_DIR / "unmatched_municipalities.csv"
LOW_CONFIDENCE_OUTPUT = PROCESSED_DATA_DIR / "low_confidence_matches.csv"

MUNICIPALITY_OVERRIDES_CSV = RECONCILIATION_DIR / "municipality_overrides.csv"
