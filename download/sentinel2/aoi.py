from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import geopandas as gpd
from pydantic import BaseModel

from download.sentinel2.constants import S2_BANDS
from download.sentinel2.model import BoundingBox

if TYPE_CHECKING:
    from download.sentinel2.config import Sentinel2Config


class EmptyGeoDataFrameError(Exception):
    """Raised when a GeoDataFrame is unexpectedly empty after filtering."""

    def __init__(self) -> None:
        super().__init__(
            "GeoDataFrame is empty after filtering. Check boundary path and filter criteria."
        )


class ProcessingArea(BaseModel):
    """A data class representing a single area to be processed."""

    name: str
    search_bbox: BoundingBox
    output_path: Path
    clip_gdf: gpd.GeoDataFrame | None = None

    class Config:
        arbitrary_types_allowed = True


class AoiManager:
    """Manages the creation of processing areas from configuration."""

    def __init__(self, config: Sentinel2Config, base_output_dir: Path):
        self.config = config
        self.base_output_dir = base_output_dir

    def _get_base_filename_stem(self) -> str:
        """Generates a filename stem if not provided in the config."""
        return self.config.output_filename or "_".join(S2_BANDS.keys())

    def _get_boundary_gdf(self) -> gpd.GeoDataFrame:
        """Reads and filters the boundary file."""
        assert self.config.boundary_path is not None  # noqa: S101
        assert self.config.boundary_filter_column is not None  # noqa: S101
        assert self.config.boundary_filter_values is not None  # noqa: S101

        path = self.config.boundary_path
        col = self.config.boundary_filter_column
        vals = self.config.boundary_filter_values

        read_kwargs: dict[str, Any] = {}
        if path.suffix in [".parquet", ".geoparquet"]:
            read_kwargs["filters"] = [(col, "in", vals)]
        else:
            quoted_vals = [f"'{val}'" for val in vals]
            read_kwargs["where"] = f'"{col}" IN ({",".join(quoted_vals)})'
            read_kwargs["use_arrow"] = True

        gdf = (
            gpd.read_file(path, **read_kwargs)
            if path.suffix not in [".parquet"]
            else gpd.read_parquet(path, **read_kwargs)
        )

        if gdf.empty:
            raise EmptyGeoDataFrameError()
        return gdf

    def get_areas(self) -> Iterator[ProcessingArea]:
        """Yields ProcessingArea objects based on the configuration."""
        base_stem = self._get_base_filename_stem()

        if self.config.bbox:
            name = self.config.output_filename or "bbox_area"
            output_path = self.base_output_dir / f"{base_stem}.tif"
            yield ProcessingArea(name=name, search_bbox=self.config.bbox, output_path=output_path)

        elif self.config.boundary_path:
            assert self.config.boundary_filter_values is not None  # noqa: S101
            gdf = self._get_boundary_gdf().to_crs(self.config.source_crs)
            for value in self.config.boundary_filter_values:
                gdf_subset = gdf[gdf[self.config.boundary_filter_column] == value]
                if gdf_subset.empty:
                    continue

                minx, miny, maxx, maxy = gdf_subset.total_bounds
                search_bbox = BoundingBox(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
                output_path = self.base_output_dir / str(value) / f"{base_stem}.tif"
                clip_gdf = gdf_subset.to_crs(self.config.target_crs)

                yield ProcessingArea(
                    name=str(value),
                    search_bbox=search_bbox,
                    output_path=output_path,
                    clip_gdf=clip_gdf,
                )
