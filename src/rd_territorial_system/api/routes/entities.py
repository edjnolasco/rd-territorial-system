from fastapi import APIRouter, HTTPException, Query

from rd_territorial_system.api.schemas import (
    ChildrenResponse,
    EntityLookupResponse,
    Level,
    ProvinceEntitiesResponse,
    TerritorialEntity,
)
from rd_territorial_system.catalog import get_default_catalog

router = APIRouter()


def map_entity(entity):
    return TerritorialEntity(**entity.to_dict())


@router.get("/entities/{composite_code}", response_model=EntityLookupResponse)
def get_entity(composite_code: str):
    catalog = get_default_catalog()
    entity = catalog.resolve_code(composite_code)

    if entity is None:
        raise HTTPException(
            status_code=404,
            detail="No territorial entity found for composite_code.",
        )

    return {
        "matched": True,
        "status": "matched",
        "entity": map_entity(entity),
    }


@router.get("/entities/{composite_code}/children", response_model=ChildrenResponse)
def get_children(
    composite_code: str,
    level: Level | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    catalog = get_default_catalog()

    if catalog.resolve_code(composite_code) is None:
        raise HTTPException(status_code=404)

    children = catalog.get_children(composite_code, level=level, limit=limit)

    return {
        "parent_code": composite_code,
        "count": len(children),
        "items": [map_entity(c) for c in children],
    }


@router.get("/provinces/{province_code}/entities", response_model=ProvinceEntitiesResponse)
def get_province_entities(
    province_code: str,
    level: Level | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
):
    catalog = get_default_catalog()

    items = catalog.get_by_province(province_code, level=level, limit=limit)

    return {
        "province_code": province_code.zfill(2),
        "count": len(items),
        "items": [map_entity(i) for i in items],
    }