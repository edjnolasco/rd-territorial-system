from __future__ import annotations

from typing import Any

from rd_territorial_system import resolve_name


def _map_rules_version_to_catalog_version(rules_version: str | None) -> str | None:
    """
    Traduce el campo rules_version del API al versionado del catálogo.

    Por ahora:
    - "v1" -> None (usa el catálogo default definido en registry.json)
    - "current" -> "current"
    - cualquier otro valor se pasa tal cual, pensando en futuras versiones
      como "2024.1", "2024.2", etc.
    """
    if not rules_version or rules_version == "v1":
        return None

    if rules_version == "current":
        return "current"

    return rules_version


def _build_response_from_catalog_result(
    result: dict[str, Any], rules_version: str | None
) -> dict[str, Any]:
    entity = result.get("entity") or {}
    candidates = result.get("candidates") or []

    return {
        "input": result.get("input"),
        "normalized_text": result.get("normalized_text"),
        "canonical_name": entity.get("name"),
        "entity_id": entity.get("composite_code"),
        "entity_type": entity.get("level"),
        "confidence": float(result.get("confidence", 0.0) or 0.0),
        "matched": bool(result.get("matched", False)),
        "status": result.get("status"),
        "match_strategy": result.get("match_strategy"),
        "rules_version": rules_version or "v1",
        "entity": entity or None,
        "candidates": candidates,
        "trace": result.get("trace") or [],
    }


def resolve_real(
    text: str,
    level: str | None = None,
    rules_version: str | None = "v1",
    strict: bool = False,
    parent_code: str | None = None,
) -> dict[str, Any]:
    """
    Resuelve una entidad territorial usando el catálogo maestro.

    Parámetros:
    - text: texto de entrada
    - level: nivel administrativo esperado
      (province, municipality, district_municipal, section, barrio_paraje, sub_barrio, toponym)
    - rules_version: por ahora se usa como proxy del versionado del catálogo
    - strict: si True, el motor puede lanzar excepción en not_found/ambiguous
    - parent_code: ayuda a desambiguar dentro de una jerarquía concreta
    """
    catalog_version = _map_rules_version_to_catalog_version(rules_version)

    result = resolve_name(
        text=text,
        level=level,
        parent_code=parent_code,
        strict=strict,
        version=catalog_version,
    )

    return _build_response_from_catalog_result(result, rules_version)
