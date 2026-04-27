from __future__ import annotations

from typing import Any

from rd_territorial_system.api.catalog_metadata import get_catalog_version
from rd_territorial_system.catalog import resolve_name
from rd_territorial_system.core.enrichment import enrich_resolve_payload


def resolve(
    text: str,
    *,
    level: str | None = None,
    parent_code: str | None = None,
    rules_version: str = "v1",
) -> dict[str, Any]:
    result = resolve_name(
        text,
        level=level,
        parent_code=parent_code,
        strict=False,
    )

    result = enrich_resolve_payload(result, rules_version)

    return {
        **result,
        "catalog_version": get_catalog_version(),
    }


def batch_resolve(
    items: list[str],
    *,
    level: str | None = None,
    parent_code: str | None = None,
    rules_version: str = "v1",
) -> list[dict[str, Any]]:
    return [
        resolve(
            item,
            level=level,
            parent_code=parent_code,
            rules_version=rules_version,
        )
        for item in items
    ]