from rd_territorial_system.parsers.territorial_txt import parse_territorial_line


def test_parse_province_line():
    row = parse_territorial_line("05 02 00 00 00 000 00 Azua", 4)

    assert row is not None
    assert row.level_name == "province"
    assert row.composite_code == "0502"
    assert row.parent_composite_code is None
    assert row.display_name == "Azua"


def test_parse_municipality_line():
    row = parse_territorial_line("05 02 01 00 00 000 00 Azua", 5)

    assert row is not None
    assert row.level_name == "municipality"
    assert row.composite_code == "050201"
    assert row.parent_composite_code == "0502"


def test_parse_district_municipal_line():
    row = parse_territorial_line("05 02 01 03 00 000 00 Las Barías-La Estancia (DM)", 10)

    assert row is not None
    assert row.level_name == "district_municipal"
    assert row.composite_code == "05020103"
    assert row.parent_composite_code == "050201"
    assert row.display_name == "Las Barías-la Estancia (DM)" or row.display_name == "Las Barías-La Estancia (DM)"


def test_parse_section_line():
    row = parse_territorial_line("05 02 01 03 01 000 00 Las Barías-La Estancia (Zona urbana)", 11)

    assert row is not None
    assert row.level_name == "section"
    assert row.composite_code == "0502010301"
    assert row.parent_composite_code == "05020103"


def test_parse_barrio_paraje_line():
    row = parse_territorial_line("05 02 01 03 01 001 00 Las Barías", 12)

    assert row is not None
    assert row.level_name == "barrio_paraje"
    assert row.composite_code == "0502010301001"
    assert row.parent_composite_code == "0502010301"


def test_parse_sub_barrio_line():
    row = parse_territorial_line("05 02 01 03 01 001 01 Las Barías", 13)

    assert row is not None
    assert row.level_name == "sub_barrio"
    assert row.composite_code == "050201030100101"
    assert row.parent_composite_code == "0502010301001"


def test_same_visible_name_different_codes_are_preserved():
    row1 = parse_territorial_line("05 02 01 03 01 001 00 Las Barías", 12)
    row2 = parse_territorial_line("05 02 01 03 01 001 01 Las Barías", 13)

    assert row1 is not None and row2 is not None
    assert row1.display_name == row2.display_name
    assert row1.composite_code != row2.composite_code


def test_capitalization_is_normalized_but_not_identity():
    row1 = parse_territorial_line("05 02 01 01 01 001 00 Los cartones", 8)
    row2 = parse_territorial_line("05 02 01 01 01 001 01 Los Cartones", 9)

    assert row1 is not None and row2 is not None
    assert row1.display_name == "Los Cartones"
    assert row2.display_name == "Los Cartones"
    assert row1.composite_code != row2.composite_code