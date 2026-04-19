from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

ONE_RAW_DIR = RAW_DATA_DIR / "one"
ONE_DISTRICT_RAW_CSV = ONE_RAW_DIR / "one_district_municipals.csv"

GADM_ADM1_ZIP = RAW_DATA_DIR / "gadm" / "gadm41_DOM_1.json.zip"
GADM_ADM2_ZIP = RAW_DATA_DIR / "gadm" / "gadm41_DOM_2.json.zip"

PROVINCES_OUTPUT = PROCESSED_DATA_DIR / "provinces.geojson"
MUNICIPALITIES_OUTPUT = PROCESSED_DATA_DIR / "municipalities.geojson"
MASTER_OUTPUT = PROCESSED_DATA_DIR / "territorial_master.csv"
MATCH_REPORT_OUTPUT = PROCESSED_DATA_DIR / "match_report.csv"
COVERAGE_REPORT_OUTPUT = PROCESSED_DATA_DIR / "coverage_report.csv"
INGESTION_REPORT_OUTPUT = PROCESSED_DATA_DIR / "ingestion_report.json"
DISTRICT_MUNICIPALS_OUTPUT = PROCESSED_DATA_DIR / "district_municipals.csv"
