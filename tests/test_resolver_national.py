from rd_territorial_system.catalog import Catalog, TerritorialEntity
from rd_territorial_system.normalization import normalize_text


def make_entity(
    *,
    code: str,
    level: str,
    name: str,
    parent_code: str = "",
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
        full_path=name,
        is_official=True,
        source="NATIONAL_TEST",
        valid_from=None,
        valid_to=None,
        notes=None,
    )


def build_national_fixture_catalog() -> Catalog:
    # Mismo nombre, mismo nivel, padres distintos → ambiguo
    san_miguel_azua = make_entity(
        code="05-02-01-03-01-006-00",
        level="barrio_paraje",
        name="San Miguel",
        parent_code="05-02-01-03-01-000-00",
    )
    san_miguel_padre_las_casas = make_entity(
        code="05-02-04-01-01-020-00",
        level="barrio_paraje",
        name="San Miguel",
        parent_code="05-02-04-01-01-000-00",
    )

    # Mismo nombre entre niveles → no colapsar
    los_cartones_barrio = make_entity(
        code="05-02-01-01-01-001-00",
        level="barrio_paraje",
        name="Los Cartones",
        parent_code="05-02-01-01-01-000-00",
    )
    los_cartones_sub = make_entity(
        code="05-02-01-01-01-001-01",
        level="sub_barrio",
        name="Los Cartones",
        parent_code="05-02-01-01-01-001-00",
    )

    return Catalog(
        [
            san_miguel_azua,
            san_miguel_padre_las_casas,
            los_cartones_barrio,
            los_cartones_sub,
        ]
    )


def test_national_same_name_same_level_is_ambiguous_without_parent():
    catalog = build_national_fixture_catalog()

    result = catalog.resolve_name("San Miguel", level="barrio_paraje")

    assert result.status == "ambiguous"
    assert result.matched is False
    assert len(result.candidates or []) == 2


def test_national_parent_code_disambiguates_same_name_same_level():
    catalog = build_national_fixture_catalog()

    result = catalog.resolve_name(
        "San Miguel",
        level="barrio_paraje",
        parent_code="05-02-01-03-01-000-00",
    )

    assert result.status == "matched"
    assert result.entity is not None
    assert result.entity["composite_code"] == "05-02-01-03-01-006-00"


def test_national_same_name_across_levels_is_preserved():
    catalog = build_national_fixture_catalog()

    results = catalog.search_entities("Los Cartones")

    assert len(results) == 2
    assert {item.level for item in results} == {"barrio_paraje", "sub_barrio"}


def test_national_level_filter_resolves_parent_and_child_name():
    catalog = build_national_fixture_catalog()

    barrio = catalog.resolve_name("Los Cartones", level="barrio_paraje")
    sub_barrio = catalog.resolve_name("Los Cartones", level="sub_barrio")

    assert barrio.status == "matched"
    assert barrio.entity is not None
    assert barrio.entity["composite_code"] == "05-02-01-01-01-001-00"

    assert sub_barrio.status == "matched"
    assert sub_barrio.entity is not None
    assert sub_barrio.entity["composite_code"] == "05-02-01-01-01-001-01"