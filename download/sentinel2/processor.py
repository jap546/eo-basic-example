from __future__ import annotations

from typing import TYPE_CHECKING

import dask.diagnostics
import geopandas as gpd
import stackstac
import xarray as xr
from pystac import ItemCollection

from download.sentinel2.constants import GDAL_ENV, S2_BANDS, SCL_GOOD_PIXELS
from download.sentinel2.masking import MaskGenerator

if TYPE_CHECKING:
    from download.sentinel2.config import Sentinel2Config
    from download.sentinel2.model import BoundingBox


class DataProcessor:
    """Handles the processing of STAC items into a final raster composite."""

    def __init__(self, config: Sentinel2Config):
        self.config = config
        self.mask_generator = MaskGenerator()

    def process_to_composite(
        self, items: ItemCollection, search_bbox: BoundingBox, clip_gdf: gpd.GeoDataFrame | None
    ) -> xr.DataArray | None:
        """
        Takes STAC items and produces a computed, cloud-masked, median composite.
        """
        target_bounds = search_bbox.reproject(
            from_crs=self.config.source_crs,
            to_crs=self.config.target_crs,
        )

        band_codes = list(S2_BANDS.values())

        data = stackstac.stack(
            items,
            assets=[*band_codes, "SCL"],
            resolution=self.config.resolution,
            epsg=self.config.target_crs,
            bounds=target_bounds.as_tuple(),
            gdal_env=GDAL_ENV,
            chunksize=(-1, 1, 2048, 2048),
        )

        if clip_gdf is not None:
            print("Creating pre-computation mask from boundary...")
            boundary_mask = self.mask_generator.create_dask_mask(clip_gdf, data)
            data = data.where(boundary_mask == 1)

        scl_mask = data.sel(band="SCL").isin(SCL_GOOD_PIXELS)
        masked_data = data.where(scl_mask).sel(band=band_codes)

        print("Computing composite...")
        composite = masked_data.median(dim="time", keep_attrs=True, skipna=True)
        with dask.diagnostics.ProgressBar():
            computed: xr.DataArray = composite.compute()

        if not computed.notnull().any():
            return None

        return computed
