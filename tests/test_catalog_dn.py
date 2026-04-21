from __future__ import annotations

import pytest

from rd_territorial_system import get_default_catalog, resolve_code, resolve_name, search_entities


@pytest.fixture(scope="module")
def catalog():
    return get_default_catalog()


def test_resolve_distrito_nacional_as_province():
    result = resolve_name("Distrito Nacional", level="province")

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["level"] == "province"
    assert result["entity"]["name"] == "Distrito Nacional"
    assert result["entity"]["composite_code"] == "10-01-00-00-00-000-00"
    assert (
        result["canonical_name"]
        if "canonical_name" in result
        else result["entity"]["name"] == "Distrito Nacional"
    )


def test_resolve_dn_alias_as_province():
    result = resolve_name("DN", level="province")

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["level"] == "province"
    assert result["entity"]["name"] == "Distrito Nacional"
    assert result["entity"]["composite_code"] == "10-01-00-00-00-000-00"


def test_resolve_santo_domingo_de_guzman_as_municipality():
    result = resolve_name("Santo Domingo de Guzmán", level="municipality")

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["level"] == "municipality"
    assert result["entity"]["name"] == "Santo Domingo de Guzmán"
    assert result["entity"]["composite_code"] == "10-01-01-00-00-000-00"
    assert result["entity"]["parent_composite_code"] == "10-01-00-00-00-000-00"


def test_resolve_los_peralejos_as_barrio_paraje():
    result = resolve_name("Los Peralejos", level="barrio_paraje")

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["level"] == "barrio_paraje"
    assert result["entity"]["name"] == "Los Peralejos"
    assert result["entity"]["composite_code"] == "10-01-01-01-01-001-00"
    assert result["entity"]["parent_composite_code"] == "10-01-01-01-01-000-00"


def test_resolve_brisas_del_norte_as_sub_barrio():
    result = resolve_name("Brisas del Norte", level="sub_barrio")

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["level"] == "sub_barrio"
    assert result["entity"]["name"] == "Brisas del Norte"
    assert result["entity"]["composite_code"] == "10-01-01-01-01-001-03"
    assert result["entity"]["parent_composite_code"] == "10-01-01-01-01-001-00"


def test_resolve_code_returns_expected_entity():
    entity = resolve_code("10-01-01-01-01-001-03")

    assert entity is not None
    assert entity["name"] == "Brisas del Norte"
    assert entity["level"] == "sub_barrio"
    assert entity["parent_composite_code"] == "10-01-01-01-01-001-00"
    assert entity["parent_path"] == [
        "Distrito Nacional",
        "Santo Domingo de Guzmán",
        "Santo Domingo de Guzmán",
        "Santo Domingo de Guzmán (Zona urbana)",
        "Los Peralejos",
    ]


def test_search_entities_returns_known_matches():
    results = search_entities("Los Peralejos", level="barrio_paraje")

    assert len(results) >= 1
    assert any(item["composite_code"] == "10-01-01-01-01-001-00" for item in results)


def test_resolve_returns_not_found_for_unknown_value():
    result = resolve_name("Sector Inventado DN", level="barrio_paraje", strict=False)

    assert result["matched"] is False
    assert result["status"] == "not_found"
    assert result["entity"] is None
    assert result["candidates"] == []


def test_ambiguous_same_name_same_level_villa_maria():
    """
    En el DN sembrado, 'Villa María' aparece varias veces como sub_barrio
    bajo distintos barrios/parajes. Eso debe producir ambigüedad cuando
    se consulta solo por nombre + nivel.
    """
    result = resolve_name("Villa María", level="sub_barrio", strict=False)

    assert result["matched"] is False
    assert result["status"] == "ambiguous"
    assert len(result["candidates"]) >= 2

    candidate_codes = {item["composite_code"] for item in result["candidates"]}
    assert "10-01-01-01-01-002-07" in candidate_codes  # Palma Real > Villa María
    assert "10-01-01-01-01-056-02" in candidate_codes  # Villa Consuelo > Villa María
    assert "10-01-01-01-01-063-05" in candidate_codes  # Mejoramiento Social > Villa María


def test_parent_code_disambiguates_villa_maria_under_palma_real():
    """
    parent_code del barrio/paraje Palma Real:
    10-01-01-01-01-002-00
    """
    result = resolve_name(
        "Villa María",
        level="sub_barrio",
        parent_code="10-01-01-01-01-002-00",
        strict=False,
    )

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["name"] == "Villa María"
    assert result["entity"]["level"] == "sub_barrio"
    assert result["entity"]["composite_code"] == "10-01-01-01-01-002-07"
    assert result["entity"]["parent_composite_code"] == "10-01-01-01-01-002-00"


def test_parent_code_disambiguates_san_miguel_under_ciudad_colonial():
    """
    San Miguel aparece repetido. Aquí lo desambiguamos usando Ciudad Colonial
    como parent_code: 10-01-01-01-01-065-00
    """
    result = resolve_name(
        "San Miguel",
        level="sub_barrio",
        parent_code="10-01-01-01-01-065-00",
        strict=False,
    )

    assert result["matched"] is True
    assert result["status"] == "matched"
    assert result["entity"]["name"] == "San Miguel"
    assert result["entity"]["composite_code"] == "10-01-01-01-01-065-02"


def test_catalog_instance_is_available(catalog):
    assert catalog is not None
    assert catalog.active_version in {"current", "v1", "2024.1"}


def test_strict_mode_raises_for_not_found():
    with pytest.raises(LookupError):
        resolve_name("No Existe DN", level="sub_barrio", strict=True)


def test_strict_mode_raises_for_ambiguous():
    with pytest.raises(LookupError):
        resolve_name("Villa María", level="sub_barrio", strict=True)
