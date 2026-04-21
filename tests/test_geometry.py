from rd_territorial_system.geometry import locate_point_in_features, point_in_feature


def _square_feature():
    # cuadrado simple (0,0) → (1,1)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    (0.0, 0.0),
                    (1.0, 0.0),
                    (1.0, 1.0),
                    (0.0, 1.0),
                    (0.0, 0.0),
                ]
            ],
        },
        "properties": {"name": "square"},
    }


# 🔴 point_in_feature


def test_point_inside_polygon():
    feature = _square_feature()

    # punto dentro
    assert point_in_feature(0.5, 0.5, feature) is True


def test_point_on_edge_polygon():
    feature = _square_feature()

    # punto en el borde (touches)
    assert point_in_feature(0.0, 0.5, feature) is True


def test_point_outside_polygon():
    feature = _square_feature()

    # punto fuera
    assert point_in_feature(2.0, 2.0, feature) is False


def test_point_feature_without_geometry():
    feature = {"type": "Feature", "properties": {}}

    assert point_in_feature(0.5, 0.5, feature) is False


# 🔴 locate_point_in_features


def test_locate_point_returns_matching_feature():
    feature1 = _square_feature()
    feature2 = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    (2.0, 2.0),
                    (3.0, 2.0),
                    (3.0, 3.0),
                    (2.0, 3.0),
                    (2.0, 2.0),
                ]
            ],
        },
        "properties": {"name": "other"},
    }

    result = locate_point_in_features(0.5, 0.5, [feature2, feature1])

    assert result is feature1


def test_locate_point_returns_none_when_not_found():
    feature = _square_feature()

    result = locate_point_in_features(5.0, 5.0, [feature])

    assert result is None


def test_locate_point_empty_features():
    result = locate_point_in_features(0.5, 0.5, [])

    assert result is None
