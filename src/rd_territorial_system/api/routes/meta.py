from fastapi import APIRouter, HTTPException

from rd_territorial_system.api.catalog_metadata import load_catalog_metadata
from rd_territorial_system.api.openapi_responses import INTERNAL_ERROR_RESPONSE

router = APIRouter(tags=["meta"])


@router.get(
    "/health",
    summary="Check API health",
    description="Returns a basic health status for the RD Territorial System API.",
    response_description="API health status",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/catalog/stats",
    summary="Get catalog statistics",
    description=(
        "Returns catalog metadata, including version, generation timestamp, "
        "entity count, province count and source of truth."
    ),
    response_description="Catalog metadata and statistics",
    responses={
        500: INTERNAL_ERROR_RESPONSE,
    },
)
def catalog_stats() -> dict[str, object]:
    try:
        metadata = load_catalog_metadata()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "metadata_error",
                "message": str(e),
            },
        ) from e

    return {
        "catalog_version": metadata["catalog_version"],  # 👈 fuente única
        "generated_at": metadata.get("generated_at"),
        "entity_count": metadata.get("entity_count"),
        "province_count": metadata.get("province_count"),
        "source_of_truth": metadata.get("source_of_truth"),
        "notes": metadata.get("notes"),
    }