from fastapi import APIRouter, HTTPException, Query

from rd_territorial_system.api.schemas import (
    ChildrenResponse,
    EntityLookupResponse,
    Level,
    ProvinceEntitiesResponse,
)
from rd_territorial_system.catalog import get_default_catalog

router = APIRouter()


@router.get("/entities/{composite_code}", response_model=EntityLookupResponse)
def get_entity(composite_code: str):
    catalog = get_default_catalog()
    entity = catalog.resolve_code(composite_code)

    if entity is None:
        raise HTTPException(
            status_code=404,
            detail={
                "matched": False,
                "status": "not_found",
                "message": "No territorial entity found for composite_code.",
            },
        )

    return {
        "matched": True,
        "status": "matched",
        "entity": entity.to_dict(),
    }


@router.get(
    "/entities/{composite_code}/children",
    response_model=ChildrenResponse,
)
def get_children(
    composite_code: str,
    level: Level | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    catalog = get_default_catalog()

    if catalog.resolve_code(composite_code) is None:
        raise HTTPException(
            status_code=404,
            detail=f"No territorial entity found for composite_code: {composite_code}",
        )

    children = catalog.get_children(
        composite_code,
        level=level,
        limit=limit,
    )

    items = [item.to_dict() for item in children]

    return {
        "parent_code": composite_code,
        "count": len(items),
        "items": items,
    }


@router.get(
    "/provinces/{province_code}/entities",
    response_model=ProvinceEntitiesResponse,
)
def get_province_entities(
    province_code: str,
    level: Level | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
):
    catalog = get_default_catalog()

    items = catalog.get_by_province(
        province_code,
        level=level,
        limit=limit,
    )

    payload = [item.to_dict() for item in items]

    return {
        "province_code": str(province_code).strip().zfill(2),
        "count": len(payload),
        "items": payload,
    }