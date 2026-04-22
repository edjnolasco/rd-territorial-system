from rd_territorial_system.catalog import Catalog, TerritorialEntity
from rd_territorial_system.normalization import normalize_text


def make_entity(
    *,
    code: str,
    level: str,
    name: str,
    parent_code: str = "",
    full_path: str | None = None,
) -> TerritorialEntity:
    (
        region_code,
        province_code,
        municipality_code,
        district_municipal_code,
        section_code,
        barrio_paraje_code,
        sub_barrio_code,
    ) = code.split("-")

    return TerritorialEntity(
        region_code=region_code,
        province_code=province_code,
        municipality_code=municipality_code,
        district_municipal_code=district_municipal_code,
        section_code=section_code,
        barrio_paraje_code=barrio_paraje_code,
        sub_barrio_code=sub_barrio_code,
        level=level,
        name=name,
        official_name=name,
        normalized_name=normalize_text(name) or "",
        parent_composite_code=parent_code,
        composite_code=code,
        full_path=full_path or name,
        is_official=True,
        source="AZUA_TEST",
        valid_from=None,
        valid_to=None,
        notes=None,
    )


def build_azua_fixture_catalog() -> Catalog:
    district = make_entity(
        code="05-02-01-03-00-000-00",
        level="district_municipal",
        name="Las Barías-La Estancia (DM)",
        parent_code="05-02-01-00-00-000-00",
        full_path="Azua > Azua > Las Barías-La Estancia (DM)",
    )
    section = make_entity(
        code="05-02-01-03-01-000-00",
        level="section",
        name="Las Barías-La Estancia (Zona urbana)",
        parent_code=district.composite_code,
        full_path="Azua > Azua > Las Barías-La Estancia (DM) > Las Barías-La Estancia (Zona urbana)",
    )
    barrio = make_entity(
        code="05-02-01-03-01-001-00",
        level="barrio_paraje",
        name="Las Barías",
        parent_code=section.composite_code,
        full_path=(
            "Azua > Azua > Las Barías-La Estancia (DM) > "
            "Las Barías-La Estancia (Zona urbana) > Las Barías"
        ),
    )
    sub_barrio = make_entity(
        code="05-02-01-03-01-001-01",
        level="sub_barrio",
        name="Las Barías",
        parent_code=barrio.composite_code,
        full_path=(
            "Azua > Azua > Las Barías-La Estancia (DM) > "
            "Las Barías-La Estancia (Zona urbana) > Las Barías > Las Barías"
        ),
    )

    return Catalog([district, section, barrio, sub_barrio])


def test_azua_same_visible_name_can_exist_in_multiple_levels():
    catalog = build_azua_fixture_catalog()

    results = catalog.search_entities("Las Barías")

    assert len(results) == 2
    assert {item.level for item in results} == {"barrio_paraje", "sub_barrio"}


def test_azua_resolve_barrio_by_level():
    catalog = build_azua_fixture_catalog()

    result = catalog.resolve_name("Las Barías", level="barrio_paraje")

    assert result.status == "matched"
    assert result.matched is True
    assert result.entity is not None
    assert result.entity["composite_code"] == "05-02-01-03-01-001-00"
    assert result.entity["level"] == "barrio_paraje"


def test_azua_resolve_sub_barrio_by_level():
    catalog = build_azua_fixture_catalog()

    result = catalog.resolve_name("Las Barías", level="sub_barrio")

    assert result.status == "matched"
    assert result.matched is True
    assert result.entity is not None
    assert result.entity["composite_code"] == "05-02-01-03-01-001-01"
    assert result.entity["level"] == "sub_barrio"


def test_azua_parent_code_disambiguates_family():
    catalog = build_azua_fixture_catalog()

    barrio_result = catalog.resolve_name(
        "Las Barías",
        parent_code="05-02-01-03-01-000-00",
    )
    sub_barrio_result = catalog.resolve_name(
        "Las Barías",
        parent_code="05-02-01-03-01-001-00",
    )

    assert barrio_result.status == "matched"
    assert barrio_result.entity is not None
    assert barrio_result.entity["composite_code"] == "05-02-01-03-01-001-00"

    assert sub_barrio_result.status == "matched"
    assert sub_barrio_result.entity is not None
    assert sub_barrio_result.entity["composite_code"] == "05-02-01-03-01-001-01"


def test_azua_resolve_district_municipal_by_code():
    catalog = build_azua_fixture_catalog()

    entity = catalog.resolve_code("05-02-01-03-00-000-00")

    assert entity is not None
    assert entity.level == "district_municipal"
    assert entity.name == "Las Barías-La Estancia (DM)"


def test_azua_search_section_name_returns_section_only():
    catalog = build_azua_fixture_catalog()

    results = catalog.search_entities("Las Barías-La Estancia (Zona urbana)")

    assert len(results) == 1
    assert results[0].level == "section"
    assert results[0].composite_code == "05-02-01-03-01-000-00"