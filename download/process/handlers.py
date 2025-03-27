# ruff: noqa: D205, D415, S501

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import dask.array as da
import geopandas as gpd
import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
import stackstac
import xarray as xr
from dask.distributed import Lock
from pydantic import BaseModel, field_validator

from download.configure.file import EODatasetConfig, File
from download.configure.validate import validators as valid
from download.process import util as u
from download.setup.constants import GEOMETRY_SERVERS, Paths


class DownloadHandler(ABC):  # fmt: off
    """Base class for Download handlers."""

    file: File

    @property
    def filenames(self) -> list[str]:
        """Property listing all filenames processed by the handler.

        Drives the logic for the 'find_file_config' method in the
        Config class, which queries these lists
        """
        filenames: str = getattr(self, "output_filename", None)  # type: ignore
        return [filenames]

    @abstractmethod
    def execute(
        self, path: Path
    ) -> Tuple[
        bool, dict[str, bytes | pd.DataFrame | None]
    ]:  # fmt: off pragma: no cover
        """Abstract execute method for DownloadHandler class."""


class ArcgisGeomHandler(BaseModel, DownloadHandler):
    """Interface with ARCGIS servers to download a single file containing geometry data.

    Uses the base File class configuration object to provide the
    folder, title, url and file extension. Takes a filename to define the
    specific file to retrieve from the service. Format and out_fields
    define the specific data to return and offset controls the ability to
    batch the retrieval of records.

    Attributes:
    -----------
    file (File):
        Instance of the File class, contains the core configuration to download
        any file

    filename (str):
        The specific file within the API to retrieve

    server (str):
        The specific arcgis server to connect to, determining the url suffix.
        Must be a specified server within GEOMETRY_SERVERS.

    out_fields: (Optional[str]) - Default: "":
        Fields to return from the API, provided as a single string with commas
        separating each field, e.g., 'field_1, field_2, field_3'

    format: (str):
        File format to return from the API - Check API for options

    offset (int) - Default: 0:
        Used when either you require more than 2,000 records from a dataset (ARCGIS
        only returns 2,000 in a batch) or the size of the batch is too large and the
        API times out (hard limit of 60 seconds). This defines how many records to
        retrieve in each batch. Set to 0 for no offset and to get all records in one
        batch.

    output_filename (str):
        Unique name for the dataset. Must be formatted as follows
        'file-description_[year / year_range]'.
        Example: crime-data_2019 or crime-data_2019-2024
    """

    file: File
    filename: str
    server: str
    outfields: Optional[str] = ""
    format: str
    offset: int = 0
    output_filename: str

    @field_validator("filename")
    @classmethod
    def filename_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, filename: str
    ) -> str:
        """Validate the format of the filename."""
        return valid.validate_filename(filename)

    @field_validator("server")
    @classmethod
    def server_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, server: str
    ) -> str:
        """Validate the server value."""
        return valid.validate_server(server)

    @field_validator("offset")
    @classmethod
    def offset_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, offset: int
    ) -> int:
        """Validate the format of the offset."""
        return valid.validate_offset(offset, 2000)

    @field_validator("output_filename")
    @classmethod
    def output_filename_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, output_filename: str
    ) -> str:
        """Validate the format of the filename."""
        return valid.validate_output_filename(output_filename)

    def execute(
        self, path: Path
    ) -> Tuple[bool, dict[str, bytes | pd.DataFrame | None]]:
        """Interface with the ONS ARCGIS server to download a single file containing geometry data.

        Returns:
        --------
        bool: Status flag indicating if any errors were raised
        dict[str, bytes | DataFrame]: Dictionary containing the filename
        and the corresponding bytes or DataFrame object returned from the url
        """
        url = f"{self.file.url}{self.filename}{GEOMETRY_SERVERS[self.server]}"

        params: dict[str, Union[str, int, None]] = {
            "where": "1=1",
            "timeRelation": "esriTimeRelationOverlaps",
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "resultType": "none",
            "distance": "0.0",
            "units": "esriSRUnit_Meter",
            "outFields": self.outfields,
            "featureEncoding": "esriCompressedShapeBuffer",
            "outputSpatialReference": 4326,
            "returnTrueCurves": "false",
            "multipatchOption": "xyFootprint",
            "sqlFormat": "none",
            "f": self.format,
            "resultRecordCount": ("" if self.offset == 0 else self.offset),
        }

        gdf, status = u.iterative_geo_api_retrieve(params, self.offset, url, 3)

        if not status:
            return (False, {self.output_filename: None})

        if self.file.write_to_disk:
            filepath = u.generate_data_path(
                path, self.file.folder, self.output_filename, self.file.file_ext
            )
            gdf.to_parquet(filepath)  # type: ignore

        return (True, {self.output_filename: gdf})


# TO DO: refactor into wider pydantic model
def process_eo_data(dataset: EODatasetConfig) -> Dict[str, Any]:
    """Function for downloading and processing EO data using STAC API."""
    year = dataset.stac_config.datetime.split("/")[0][:4]

    raw_output_path = u.generate_data_path(
        Paths.RAW_DATA_DIR,
        dataset.file_config.folder,
        f"{dataset.file_config.title}_composite__{year}",
        "tif",
    )

    raw_output_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_parquet(
        Paths.RAW_DATA_DIR / "boundaries" / "geom-mca-codes_2024.parquet",
        filters=[("CAUTH24CD", "=", "E47000001")],
    ).to_crs(dataset.handler_config.epsg)

    stac_client = pystac_client.Client.open(
        url=str(dataset.stac_config.url), modifier=planetary_computer.sign_inplace
    )

    search = stac_client.search(
        collections=dataset.stac_config.collections,
        bbox=dataset.stac_config.bbox,
        datetime=dataset.stac_config.datetime,
        query=dataset.stac_config.query,
    )

    items = search.item_collection()

    print(f"Number of items found for {year}: {len(items)}")

    data = (
        stackstac.stack(
            items,
            assets=dataset.handler_config.assets,
            chunksize=dataset.handler_config.chunksize,
            resolution=dataset.handler_config.resolution,
            epsg=dataset.handler_config.epsg,
        )
        .where(lambda x: x > 0, other=np.nan) # sentinel-2 uses 0 as nodata
        .assign_coords(band=lambda x: x.common_name.rename("band"))
    )

    composite = data.median(dim="time", keep_attrs=True)

    delayed_mask = u.make_mask(gdf, data.isel(time=0, band=0))

    mask_array = da.from_delayed(
        delayed_mask,
        shape=(data.sizes["y"], data.sizes["x"]),
        dtype=np.uint8,
    )

    mask_da = xr.DataArray(
        mask_array, coords={"y": data.y, "x": data.x}, dims=("y", "x"), name="mask"
    )

    composite = composite.where(mask_da == 1)

    composite = composite.compute()

    composite = composite.rio.write_crs(dataset.handler_config.epsg)

    composite.rio.to_raster(
        raw_output_path,
        tiled=True,
        lock=Lock("rio"),
    )

    return {
        "Created raw composite": raw_output_path,
    }


DOWNLOAD_HANDLERS: dict[str, DownloadHandler] = {
    "arcgis_geom_api": ArcgisGeomHandler,  # type: ignore
}
