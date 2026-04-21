from __future__ import annotations

from typing import Any, Optional

from shapely.geometry import Point, shape


def point_in_feature(lat: float, lon: float, feature: dict[str, Any]) -> bool:
    geometry = feature.get("geometry")
    if not geometry:
        return False
    point = Point(lon, lat)
    polygon = shape(geometry)
    return polygon.contains(point) or polygon.touches(point)


def locate_point_in_features(
    lat: float, lon: float, features: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    for feature in features:
        if point_in_feature(lat, lon, feature):
            return feature
    return None
