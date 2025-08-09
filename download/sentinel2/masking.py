from __future__ import annotations

import dask.array as da
import geopandas as gpd
import numpy as np
import rasterio.features
import rioxarray as rio  # noqa: F401
import xarray as xr
from dask import delayed


def _rasterize_geometry(gdf: gpd.GeoDataFrame, template_da: xr.DataArray) -> np.ndarray:
    """Rasterizes a GeoDataFrame geometry to match a DataArray's shape and transform."""
    shapes = [(geom, 1) for geom in gdf.geometry]
    transform = template_da.rio.transform()
    out_shape = template_da.rio.shape

    mask: np.ndarray = rasterio.features.rasterize(
        shapes, out_shape=out_shape, transform=transform, fill=0, dtype=np.uint8
    )
    return mask


class MaskGenerator:
    """Generates raster masks from vector geometries."""

    @staticmethod
    @delayed
    def _delayed_rasterize(gdf: gpd.GeoDataFrame, template_da: xr.DataArray) -> np.ndarray:
        """Delayed wrapper around rasterize_geometry."""
        return _rasterize_geometry(gdf, template_da)

    def create_dask_mask(self, gdf: gpd.GeoDataFrame, template_da: xr.DataArray) -> xr.DataArray:
        """
        Creates a Dask-backed raster mask from a GeoDataFrame.
        """
        delayed_mask = self._delayed_rasterize(gdf, template_da.isel(time=0, band=0))

        mask_array = da.from_delayed(
            delayed_mask,
            shape=(template_da.sizes["y"], template_da.sizes["x"]),
            dtype=np.uint8,
        )

        return xr.DataArray(
            mask_array,
            coords={"y": template_da.y, "x": template_da.x},
            dims=("y", "x"),
            name="mask",
        )
