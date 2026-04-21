import pandas as pd

from rd_territorial_system import services

# 🔴 Helpers


def _fake_province_feature():
    return {
        "type": "Feature",
        "properties": {"name": "Distrito Nacional", "id": "DN"},
        "geometry": {"type": "Polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]},
    }


def _fake_municipality_feature():
    return {
        "type": "Feature",
        "properties": {
            "name": "Santo Domingo de Guzmán",
            "id": "SDG",
            "province_name": "Distrito Nacional",
        },
        "geometry": {"type": "Polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]},
    }


# 🔴 load_* tests (mock directo)


def test_load_provinces(monkeypatch):
    monkeypatch.setattr(services, "_load_geojson", lambda path: {"features": []})
    result = services.load_provinces()
    assert "features" in result


def test_load_match_report(monkeypatch):
    monkeypatch.setattr(services, "_load_csv", lambda path: pd.DataFrame({"a": [1]}))
    df = services.load_match_report()
    assert not df.empty


# 🔴 get names


def test_get_province_names(monkeypatch):
    monkeypatch.setattr(
        services, "load_provinces", lambda: {"features": [_fake_province_feature()]}
    )

    names = services.get_province_names()
    assert names == ["Distrito Nacional"]


def test_get_municipality_names(monkeypatch):
    monkeypatch.setattr(
        services, "load_municipalities", lambda: {"features": [_fake_municipality_feature()]}
    )

    names = services.get_municipality_names()
    assert names == ["Santo Domingo de Guzmán"]


# 🔴 find by name


def test_find_province_by_name(monkeypatch):
    monkeypatch.setattr(
        services, "load_provinces", lambda: {"features": [_fake_province_feature()]}
    )

    result = services.find_province_by_name("Distrito Nacional")
    assert result is not None


def test_find_province_by_name_not_found(monkeypatch):
    monkeypatch.setattr(services, "load_provinces", lambda: {"features": []})

    result = services.find_province_by_name("X")
    assert result is None


def test_find_municipality_by_name(monkeypatch):
    monkeypatch.setattr(
        services, "load_municipalities", lambda: {"features": [_fake_municipality_feature()]}
    )

    result = services.find_municipality_by_name("Santo Domingo de Guzmán")
    assert result is not None


# 🔴 locate_point


def test_locate_point_no_match(monkeypatch):
    monkeypatch.setattr(services, "load_provinces", lambda: {"features": []})
    monkeypatch.setattr(services, "load_municipalities", lambda: {"features": []})
    monkeypatch.setattr(services, "locate_point_in_features", lambda lat, lon, features: None)

    result = services.locate_point(0.5, 0.5)

    assert result["status"] == "not_found"
    assert result["precision"] == "none"


def test_locate_point_province_only(monkeypatch):
    monkeypatch.setattr(
        services, "load_provinces", lambda: {"features": [_fake_province_feature()]}
    )
    monkeypatch.setattr(services, "load_municipalities", lambda: {"features": []})

    def fake_locate(lat, lon, features):
        return features[0] if features else None

    monkeypatch.setattr(services, "locate_point_in_features", fake_locate)

    result = services.locate_point(0.5, 0.5)

    assert result["province"] == "Distrito Nacional"
    assert result["precision"] == "province"
    assert result["status"] == "matched"


def test_locate_point_municipality_overrides(monkeypatch):
    monkeypatch.setattr(
        services, "load_provinces", lambda: {"features": [_fake_province_feature()]}
    )
    monkeypatch.setattr(
        services, "load_municipalities", lambda: {"features": [_fake_municipality_feature()]}
    )

    def fake_locate(lat, lon, features):
        return features[0] if features else None

    monkeypatch.setattr(services, "locate_point_in_features", fake_locate)

    result = services.locate_point(0.5, 0.5)

    assert result["municipality"] == "Santo Domingo de Guzmán"
    assert result["province"] == "Distrito Nacional"
    assert result["precision"] == "municipality"
    assert result["status"] == "matched"
