from .services import (
    load_provinces,
    load_municipalities,
    load_match_report,
    load_coverage_report,
    load_ingestion_report,
    load_unmatched_municipalities,
    load_low_confidence_matches,
    get_province_names,
    get_municipality_names,
    find_province_by_name,
    find_municipality_by_name,
    locate_point,
)

# 🔥 Nuevo motor (catalog-based)
from .catalog import (
    get_catalog,
    get_default_catalog,
    resolve_name,
    resolve_code,
    search_entities,
    Catalog,
    TerritorialEntity,
    ResolveResult,
)

__version__ = "3.0.0"

__all__ = [
    # 🔹 API existente (compatibilidad)
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

    # 🔥 Nueva API (motor real)
    "get_catalog",
    "get_default_catalog",
    "resolve_name",
    "resolve_code",
    "search_entities",
    "Catalog",
    "TerritorialEntity",
    "ResolveResult",

    "__version__",
]