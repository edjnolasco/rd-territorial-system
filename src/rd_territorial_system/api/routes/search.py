from fastapi import APIRouter

from rd_territorial_system.api.schemas import SearchRequest, SearchResponse, TerritorialEntity
from rd_territorial_system.catalog import get_default_catalog
from rd_territorial_system.normalization import normalize_text

router = APIRouter()


def map_entity(entity):
    return TerritorialEntity(**entity.to_dict())


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest):
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