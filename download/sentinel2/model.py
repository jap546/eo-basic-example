from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

import geopandas as gpd
from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry


class CoordinateReferenceSystems(Enum):
    """Common CRS used, with a method to get the integer code."""

    WGS84 = "EPSG:4326"
    BNG = "EPSG:27700"

    def to_epsg_code(self) -> int:
        """Converts the CRS string to its integer EPSG code."""
        return int(self.value.split(":")[1])

    def to_string(self) -> str:
        """Returns CRS as a string."""
        return self.value


@dataclass
class BoundingBox:
    """A data class representing a bounding box."""

    minx: float
    miny: float
    maxx: float
    maxy: float

    def as_dict(self) -> dict[str, float]:
        """Returns the bounding box coordinates as a dictionary."""
        return asdict(self)

    def as_tuple(self) -> tuple[float, float, float, float]:
        """Returns the bounding box coordinates as a tuple."""
        return (self.minx, self.miny, self.maxx, self.maxy)

    def reproject(self, from_crs: str | int, to_crs: str | int) -> BoundingBox:
        """
        Reprojects the bounding box coordinates to a new CRS.
        """
        transformer = Transformer.from_crs(
            crs_from=CRS.from_user_input(from_crs),
            crs_to=CRS.from_user_input(to_crs),
            always_xy=True,
        )

        new_xs, new_ys = transformer.transform(xx=[self.minx, self.maxx], yy=[self.miny, self.maxy])

        return BoundingBox(
            minx=min(new_xs),
            miny=min(new_ys),
            maxx=max(new_xs),
            maxy=max(new_ys),
        )


type GeometryInputType = BoundingBox | str | bytes | tuple | list | gpd.GeoSeries | BaseGeometry
