from importlib.resources import files
from pathlib import Path

# =========================
# 🔥 DATA EMBEBIDA (RUNTIME)
# =========================

PACKAGE_DATA_ROOT = files("rd_territorial_system") / "data"

DATA_DIR = Path(PACKAGE_DATA_ROOT)
CATALOG_DIR = DATA_DIR / "catalog"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RECONCILIATION_DIR = DATA_DIR / "reconciliation"

PROVINCES_OUTPUT = PROCESSED_DATA_DIR / "provinces.geojson"
MUNICIPALITIES_OUTPUT = PROCESSED_DATA_DIR / "municipalities.geojson"
MASTER_OUTPUT = PROCESSED_DATA_DIR / "territorial_master.csv"
MATCH_REPORT_OUTPUT = PROCESSED_DATA_DIR / "match_report.csv"
COVERAGE_REPORT_OUTPUT = PROCESSED_DATA_DIR / "coverage_report.csv"
INGESTION_REPORT_OUTPUT = PROCESSED_DATA_DIR / "ingestion_report.json"
UNMATCHED_MUNICIPALITIES_OUTPUT = PROCESSED_DATA_DIR / "unmatched_municipalities.csv"
LOW_CONFIDENCE_OUTPUT = PROCESSED_DATA_DIR / "low_confidence_matches.csv"

MUNICIPALITY_OVERRIDES_CSV = RECONCILIATION_DIR / "municipality_overrides.csv"

# =========================
# ⚙️ DATA EXTERNA (PIPELINE)
# =========================

# Estas rutas SOLO se usan en scripts, no en runtime
PROJECT_ROOT = Path.cwd()

DATA_PIPELINE_DIR = PROJECT_ROOT / "data_pipeline"
RAW_DATA_DIR = DATA_PIPELINE_DIR / "raw"

ONE_RAW_DIR = RAW_DATA_DIR / "one"
GADM_ADM1_ZIP = RAW_DATA_DIR / "gadm" / "gadm41_DOM_1.json.zip"
GADM_ADM2_ZIP = RAW_DATA_DIR / "gadm" / "gadm41_DOM_2.json.zip"