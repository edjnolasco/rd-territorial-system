import json
from pathlib import Path
from typing import Any

from rd_territorial_system.api.settings import get_settings


class CatalogMetadataError(Exception):
    pass


def load_catalog_metadata(metadata_path: Path | None = None) -> dict[str, Any]:
    path = metadata_path or get_settings().metadata_path

    if not path.exists():
        raise CatalogMetadataError(f"Metadata file not found at {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except Exception as exc:
        raise CatalogMetadataError(f"Failed to read metadata: {exc}") from exc

    required_fields = {
        "catalog_version",
        "generated_at",
        "entity_count",
        "province_count",
        "source_of_truth",
    }

    missing = required_fields - data.keys()
    if missing:
        raise CatalogMetadataError(
            f"Missing required metadata fields: {sorted(missing)}"
        )

    return data