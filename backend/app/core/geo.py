"""Conversions between API-facing (lat, lon) floats and the PostGIS
geography(Point, 4326) columns on Douar/Report. Centralized here so every
route constructs/reads points the same way."""

from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape


def point_from_latlon(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def latlon_from_point(point) -> tuple[float, float] | None:
    if point is None:
        return None
    shape = to_shape(point)
    return shape.y, shape.x  # (lat, lon)
