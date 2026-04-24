from collections import Counter

from fastapi import APIRouter

from rd_territorial_system.api.schemas import CatalogStatsResponse, HealthResponse
from rd_territorial_system.catalog import get_default_catalog

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    catalog = get_default_catalog()

    return {
        "status": "ok",
        "service": "rd-territorial-system",
        "api_version": "v1",
        "catalog_format": "csv",
        "catalog_loaded": catalog is not None,
    }


@router.get("/catalog/stats", response_model=CatalogStatsResponse)
def catalog_stats():
    catalog = get_default_catalog()

    levels = Counter(entity.level for entity in catalog.entities)
    provinces = {entity.province_code for entity in catalog.entities}

    return {
        "catalog_version": catalog.active_version,
        "country": "República Dominicana",
        "province_count": len(provinces),
        "entity_count": len(catalog.entities),
        "levels": dict(sorted(levels.items())),
        "source_of_truth": "csv",
    }