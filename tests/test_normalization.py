from rd_territorial_system.normalization import (
    normalize_text,
    canonical_province,
    canonical_municipality,
    match_score,
)


# 🔴 normalize_text

def test_normalize_basic():
    assert normalize_text("  Santo Domingo  ") == "santo domingo"


def test_normalize_accents():
    assert normalize_text("Sánchez Ramírez") == "sanchez ramirez"


def test_normalize_special_chars():
    assert normalize_text("Sto. Dgo!") == "sto domingo"


def test_normalize_replacements():
    assert normalize_text("Sto Dgo") == "sto domingo"
    assert normalize_text("MTS") == "matas"  # regla mts → matas


def test_normalize_none():
    assert normalize_text(None) is None


def test_normalize_empty():
    assert normalize_text("   ") == ""


# 🔴 canonical_province

def test_canonical_province_alias():
    assert canonical_province("DN") == "distrito nacional"


def test_canonical_province_variant():
    assert canonical_province("Dajabón") == "dajabon"


def test_canonical_province_direct():
    assert canonical_province("Santiago") == "santiago"


def test_canonical_province_none():
    assert canonical_province(None) is None


# 🔴 canonical_municipality

def test_canonical_municipality_alias():
    assert canonical_municipality("Zona Colonial") == "santo domingo de guzman"


def test_canonical_municipality_variant():
    assert canonical_municipality("Sosúa") == "sosua"


def test_canonical_municipality_direct():
    assert canonical_municipality("Jarabacoa") == "jarabacoa"


def test_canonical_municipality_none():
    assert canonical_municipality(None) is None


# 🔴 match_score

def test_match_score_exact():
    assert match_score("Santo Domingo", "santo domingo") == 100


def test_match_score_province_alias():
    assert match_score("DN", "Distrito Nacional") == 98


def test_match_score_municipality_alias():
    assert match_score("Zona Colonial", "Santo Domingo de Guzmán") == 98


def test_match_score_partial():
    score = match_score("Santo Domingo", "Santo")
    assert score == 85


def test_match_score_overlap():
    score = match_score("San Pedro de Macoris", "San Pedro")
    assert score > 0


def test_match_score_none():
    assert match_score(None, "test") == 0


def test_match_score_no_match():
    assert match_score("abc", "xyz") == 0