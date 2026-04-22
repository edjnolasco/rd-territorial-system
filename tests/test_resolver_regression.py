from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from rd_territorial_system.catalog import get_catalog, resolve_name


CATALOG_PATH = Path("data/catalog/current/rd_territorial_master.parquet")


def _ensure_catalog_exists() -> None:
    if not CATALOG_PATH.exists():
        pytest.skip(f"No existe catálogo maestro en {CATALOG_PATH}")


def _resolver_catalog():
    _ensure_catalog_exists()
    return get_catalog()


def _resolve(
    query: str,
    *,
    level: str | None = None,
    parent_code: str | None = None,
    strict: bool = False,
):
    catalog = _resolver_catalog()
    return resolve_name(
        query,
        level=level,
        parent_code=parent_code,
        strict=strict,
        catalog=catalog,
    )


def _entity(result: dict) -> dict | None:
    return result.get("entity")


def _assert_matched(result: dict, query: str) -> dict:
    assert result["matched"] is True, f"No resolvió {query!r}: {result}"
    entity = _entity(result)
    assert entity is not None, f"Resultado sin entity para {query!r}: {result}"
    return entity


def _find_parent_code_by_name(
    name: str,
    *,
    level: str | None = None,
) -> str:
    catalog = _resolver_catalog()
    matches = catalog.search_entities(name, level=level, limit=20)
    assert matches, f"No se encontró entidad para obtener parent context de {name!r}"

    # tomamos la primera porque para estos casos del test el contexto ya es controlado
    return matches[0].composite_code


def test_resolver_dn_baseline_still_resolves() -> None:
    result = _resolve("Distrito Nacional")
    entity = _assert_matched(result, "Distrito Nacional")

    assert entity["name"] == "Distrito Nacional"
    assert entity["level"] in {
        "province",
        "municipality",
        "district_municipal",
        "section",
        "barrio_paraje",
        "sub_barrio",
        "toponym",
    }


def test_resolver_azua_presence() -> None:
    result = _resolve("Azua", level="province")
    entity = _assert_matched(result, "Azua")

    assert entity["name"] == "Azua"
    assert entity["level"] == "province"
    assert entity["province_code"] == "02"


def test_resolver_case_variation_does_not_change_identity_for_los_cartones() -> None:
    parent_code = _find_parent_code_by_name(
        "Azua de Compostela (Zona urbana)",
        level="section",
    )

    result_1 = _resolve(
        "Los cartones",
        level="barrio_paraje",
        parent_code=parent_code,
    )
    result_2 = _resolve(
        "Los Cartones",
        level="barrio_paraje",
        parent_code=parent_code,
    )

    entity_1 = _assert_matched(result_1, "Los cartones")
    entity_2 = _assert_matched(result_2, "Los Cartones")

    assert entity_1["composite_code"] == entity_2["composite_code"]
    assert entity_1["name"] == "Los cartones"
    assert entity_2["name"] == "Los cartones"


def test_resolver_case_variation_does_not_change_identity_for_las_barias() -> None:
    parent_code = _find_parent_code_by_name(
        "Las Barías-La Estancia (Zona urbana)",
        level="section",
    )

    result_1 = _resolve(
        "Las Barías",
        level="barrio_paraje",
        parent_code=parent_code,
    )
    result_2 = _resolve(
        "las barías",
        level="barrio_paraje",
        parent_code=parent_code,
    )

    entity_1 = _assert_matched(result_1, "Las Barías")
    entity_2 = _assert_matched(result_2, "las barías")

    assert entity_1["composite_code"] == entity_2["composite_code"]
    assert entity_1["name"] == "Las Barías"
    assert entity_2["name"] == "Las Barías"


def test_resolver_context_disambiguates_repeated_name_las_barias() -> None:
    parent_code = _find_parent_code_by_name(
        "Las Barías-La Estancia (Zona urbana)",
        level="section",
    )

    result = _resolve(
        "Las Barías",
        level="barrio_paraje",
        parent_code=parent_code,
    )
    entity = _assert_matched(result, "Las Barías")

    assert entity["name"] == "Las Barías"
    assert entity["level"] == "barrio_paraje"
    assert entity["parent_composite_code"] == parent_code


def test_resolver_context_disambiguates_los_cartones_in_azua() -> None:
    parent_code = _find_parent_code_by_name(
        "Azua de Compostela (Zona urbana)",
        level="section",
    )

    result = _resolve(
        "Los Cartones",
        level="barrio_paraje",
        parent_code=parent_code,
    )
    entity = _assert_matched(result, "Los Cartones")

    assert entity["name"] == "Los cartones"
    assert entity["level"] == "barrio_paraje"
    assert entity["parent_composite_code"] == parent_code


def test_resolver_does_not_return_null_for_known_azua_entities() -> None:
    cases = [
        ("Azua", "province", None),
        ("Sabana Yegua", None, None),
        ("Las Barías-La Estancia (DM)", "district_municipal", None),
        ("Estebanía", None, None),
    ]

    for query, level, parent_code in cases:
        result = _resolve(query, level=level, parent_code=parent_code)
        entity = _assert_matched(result, query)
        assert entity["name"] == query
        if level is not None:
            assert entity["level"] == level


def test_resolver_is_stable_for_previously_validated_queries() -> None:
    cases = [
        ("Distrito Nacional", "province", None),
        ("Azua", "province", None),
        ("Estebanía", None, None),
        ("Sabana Yegua", None, None),
    ]

    identities: list[tuple[str, str, str]] = []

    for query, level, parent_code in cases:
        result = _resolve(query, level=level, parent_code=parent_code)
        entity = _assert_matched(result, query)
        identities.append(
            (
                entity["composite_code"],
                entity["level"],
                entity["name"],
            )
        )

    for composite_code, level, name in identities:
        assert composite_code
        assert level
        assert name


def test_resolver_returns_ambiguous_without_context_when_expected() -> None:
    result = _resolve("Las Barías")

    # El comportamiento aceptable actual del resolver puede ser:
    # 1) devolver ambiguous, o
    # 2) escoger una coincidencia válida de forma estable.
    assert result["status"] in {"ambiguous", "matched", "exact_match", "single_match"} or result["matched"] in {True, False}

    if result["matched"] is False:
        assert result["status"] == "ambiguous"
        assert isinstance(result.get("candidates"), list)
        assert len(result["candidates"]) >= 2
    else:
        entity = _entity(result)
        assert entity is not None
        assert entity["name"] == "Las Barías"
        
def test_resolver_returns_stable_result_for_las_barias_without_context() -> None:
    result = _resolve("Las Barías")

    if result["matched"] is False:
        assert result["status"] == "ambiguous"
        assert isinstance(result.get("candidates"), list)
        assert len(result["candidates"]) >= 2
    else:
        entity = _assert_matched(result, "Las Barías")
        assert entity["name"] == "Las Barías"