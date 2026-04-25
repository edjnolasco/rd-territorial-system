from fastapi import APIRouter, HTTPException, Query

from rd_territorial_system.api.openapi_responses import (
    COMMON_ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
)
from rd_territorial_system.api.schemas import (
    ChildrenResponse,
    EntityLookupResponse,
    Level,
    ProvinceEntitiesResponse,
    TerritorialEntity,
)
from rd_territorial_system.catalog import get_default_catalog

router = APIRouter(tags=["entities"])


def map_entity(entity):
    return TerritorialEntity(**entity.to_dict())


@router.get(
    "/entities/{composite_code}",
    response_model=EntityLookupResponse,
    summary="Get territorial entity by code",
    description=(
        "Retrieves a territorial entity from the national catalog using its "
        "composite territorial code."
    ),
    response_description="Territorial entity lookup result",
    responses={
    404: NOT_FOUND_RESPONSE,
    **COMMON_ERROR_RESPONSES,
    },
)
def get_entity(composite_code: str) -> EntityLookupResponse:
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


@router.get(
    "/entities/{composite_code}/children",
    response_model=ChildrenResponse,
    summary="Get child territorial entities",
    description=(
        "Retrieves child territorial entities for a given parent composite code. "
        "Supports optional filtering by territorial level."
    ),
    response_description="Child territorial entities for the requested parent",
    responses={
    404: NOT_FOUND_RESPONSE,
    **COMMON_ERROR_RESPONSES,
    },
)
def get_children(
    composite_code: str,
    level: Level | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> ChildrenResponse:
    catalog = get_default_catalog()

    if catalog.resolve_code(composite_code) is None:
        raise HTTPException(status_code=404)

    children = catalog.get_children(composite_code, level=level, limit=limit)

    return {
        "parent_code": composite_code,
        "count": len(children),
        "items": [map_entity(c) for c in children],
    }


@router.get(
    "/provinces/{province_code}/entities",
    response_model=ProvinceEntitiesResponse,
    summary="Get territorial entities by province",
    description=(
        "Retrieves territorial entities that belong to a province identified by "
        "its province code. Supports optional filtering by territorial level."
    ),
    response_description="Territorial entities for the requested province",
    responses=COMMON_ERROR_RESPONSES,
)
def get_province_entities(
    province_code: str,
    level: Level | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
) -> ProvinceEntitiesResponse:
    catalog = get_default_catalog()

    items = catalog.get_by_province(province_code, level=level, limit=limit)

    return {
        "province_code": province_code.zfill(2),
        "count": len(items),
        "items": [map_entity(i) for i in items],
    }