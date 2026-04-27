# 🔥 API pública (nivel librería)
from rd_territorial_system.core.resolver import batch_resolve, resolve

# 🔥 Motor interno (nivel avanzado)
from .catalog import (
    Catalog,
    ResolveResult,
    TerritorialEntity,
    get_catalog,
    get_default_catalog,
    resolve_code,
    resolve_name,
    search_entities,
)

# 🔧 Servicios (geo / reporting / utilidades)
from .services import (
    find_municipality_by_name,
    find_province_by_name,
    get_municipality_names,
    get_province_names,
    load_coverage_report,
    load_ingestion_report,
    load_low_confidence_matches,
    load_match_report,
    load_municipalities,
    load_provinces,
    load_unmatched_municipalities,
    locate_point,
)

__version__ = "3.0.0"

__all__ = [
    # =========================
    # 🔥 API PRINCIPAL (RECOMENDADA)
    # =========================
    "resolve",
    "batch_resolve",
    # =========================
    # 🔥 MOTOR (USO AVANZADO)
    # =========================
    "get_catalog",
    "get_default_catalog",
    "resolve_name",
    "resolve_code",
    "search_entities",
    "Catalog",
    "TerritorialEntity",
    "ResolveResult",
    # =========================
    # 🔧 UTILIDADES / SERVICIOS
    # =========================
    "load_provinces",
    "load_municipalities",
    "load_match_report",
    "load_coverage_report",
    "load_ingestion_report",
    "load_unmatched_municipalities",
    "load_low_confidence_matches",
    "get_province_names",
    "get_municipality_names",
    "find_province_by_name",
    "find_municipality_by_name",
    "locate_point",
    # =========================
    # META
    # =========================
    "__version__",
]