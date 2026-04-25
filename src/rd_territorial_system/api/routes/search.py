from fastapi import APIRouter

from rd_territorial_system.api.openapi_responses import COMMON_ERROR_RESPONSES
from rd_territorial_system.api.schemas import (
    SearchRequest,
    SearchResponse,
    TerritorialEntity,
)
from rd_territorial_system.catalog import get_default_catalog
from rd_territorial_system.normalization import normalize_text

router = APIRouter(tags=["search"])


def map_entity(entity):
    return TerritorialEntity(**entity.to_dict())


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search territorial entities",
    description=(
        "Searches territorial entities in the national catalog using a text query. "
        "Supports optional filtering by level and parent_code, and limits the number "
        "of returned results."
    ),
    response_description="List of matching territorial entities",
    responses=COMMON_ERROR_RESPONSES,
)
def search(payload: SearchRequest) -> SearchResponse:
    catalog = get_default_catalog()

    items = catalog.search_entities(
        payload.text,
        level=payload.level,
        parent_code=payload.parent_code,
        limit=payload.limit,
    )

    return {
        "input": payload.text,
        "normalized_text": normalize_text(payload.text),
        "count": len(items),
        "items": [map_entity(i) for i in items],
    }