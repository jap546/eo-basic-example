import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pydantic import BaseModel, field_validator

import download.configure.validate.exceptions as e
from download.configure.file import File
from download.configure.validate import validators as valid
from download.process import util as u
from download.sentinel2.config import CoordinateReferenceSystems, Sentinel2Config
from download.sentinel2.extractor import Sentinel2Extractor
from download.sentinel2.model import BoundingBox
from download.setup.constants import GEOMETRY_SERVERS


class DownloadHandler(ABC):  # fmt: off
    """Base class for Download handlers."""

    file: File

    @property
    def filenames(self) -> list[str]:
        """Property listing all filenames processed by the handler.

        Drives the logic for the 'find_file_config' method in the
        Config class, which queries these lists
        """
        filenames: str = getattr(self, "output_filename", None)  # type: ignore  # noqa: PGH003
        return [filenames]

    @abstractmethod
    def execute(
        self, path: Path
    ) -> tuple[bool, dict[str, bytes | pd.DataFrame | None]]:  # fmt: off pragma: no cover
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
    outfields: str | None = ""
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

    @field_validator("format")
    @classmethod
    def validate_format(cls, file_format: str) -> str:
        return valid.validate_format(file_format)

    def execute(self, path: Path) -> tuple[bool, dict[str, bytes | pd.DataFrame | None]]:
        """Interface with the ONS ARCGIS server to download a single file containing geometry data.

        Returns:
        --------
        bool: Status flag indicating if any errors were raised
        dict[str, bytes | DataFrame]: Dictionary containing the filename
        and the corresponding bytes or DataFrame object returned from the url
        """
        url = f"{self.file.url}{self.filename}{GEOMETRY_SERVERS[self.server]}"

        params: dict[str, str | int | None] = {
            "where": "1=1",
            "distance": "0.0",
            "units": "esriSRUnit_Meter",
            "outFields": self.outfields,
            "featureEncoding": "esriCompressedShapeBuffer",
            "outSR": CoordinateReferenceSystems.BNG.to_epsg_code(),
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
            gdf.to_parquet(filepath)

        return (True, {self.output_filename: gdf})


class GeomShpZipHandler(BaseModel, DownloadHandler):
    """Download a zip file containing shapefiles and save to GeoJSON.

    Uses the base File class configuration object to provide the
    folder, title, url and file extension. Takes in an value for
    filename, which is the name of the file to be extracted from
    the zip file.

    As a minimum, a shapefile requires:
      - .dbf: attribute information
      - .shp: feature geometry
      - .shx: index of feature geometry

    Ideally, it'd also have:
      - .prj: coordinate reference and projection information in WKT format
      - .sbn & .sbx: spatial index
      - .shp.xml: geospatial metadata in XML format

    If any of the file extensions are present we will extract them from the zip file.

    Attributes:
    -----------
    file (File):
        Instance of the File class, contains the core configuration to download
        any file

    filename (str):
        Name of the file to be extracted from the zip file

    output_filename (str):
        Unique name for the dataset. Must be formatted as follows
        'file-description_[year / year_range]'.
        Example: crime-data_2019 or crime-data_2019-2024
    """

    file: File
    filename: str
    output_filename: str

    @field_validator("filename")
    @classmethod
    def filename_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, filename: str
    ) -> str:
        """Validate the format of the filename."""
        return valid.validate_filename(filename)

    @field_validator("output_filename")
    @classmethod
    def output_filename_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, output_filename: str
    ) -> str:
        """Validate the format of the filename."""
        return valid.validate_output_filename(output_filename)

    def execute(self, path: Path) -> tuple[bool, dict[str, bytes | pd.DataFrame | None]]:
        """Download a zip file containing shapefiles and save to disk.

        Returns:
        --------
        bool: Status flag indicating if any errors were raised
        dict[str, bytes | DataFrame]: Dictionary containing the filename
        and the corresponding bytes or DataFrame object returned from the url
        """
        resp, status = u.retrieve_file(self.file.url, "zip")

        if not status or not resp:
            return (False, {self.output_filename: None})

        zip_file_bytes = io.BytesIO(resp.content)

        if self.file.write_to_disk:
            filepath = u.generate_data_path(
                path, self.file.folder, self.output_filename, self.file.file_ext
            )

            gdf = gpd.read_file(zip_file_bytes, use_arrow=True).to_crs(
                CoordinateReferenceSystems.BNG.to_epsg_code()
            )
            gdf.to_parquet(filepath)

            return (True, {self.output_filename: gdf})

        return (True, {self.output_filename: None})


class Sentinel2Handler(BaseModel, DownloadHandler):
    """
    Handler for discovering, processing, and downloading Sentinel-2 imagery.
    """

    file: File
    output_filename: str

    bbox: BoundingBox | None = None
    boundary_path: Path | None = None
    boundary_filter_column: str | None = None
    boundary_filter_values: list[str] | None = None
    resolution: int
    start_date: Any
    end_date: Any
    max_cloud_cover: int = 25
    collection: str = "sentinel-2-l2a"
    resample_period: str | None = None
    composite_method: str = "median"

    @field_validator("output_filename")
    @classmethod
    def output_filename_valid(cls, output_filename: str) -> str:
        if " " in output_filename:
            msg = "output_filename must not contain spaces."
            raise e.SpacesInFileNameError(msg)
        return output_filename

    @property
    def filenames(self) -> list[str]:
        return [self.output_filename]

    def execute(self, path: Path) -> tuple[bool, dict[str, bytes | pd.DataFrame | None]]:
        try:
            s2_config_data = self.model_dump(exclude={"file"})
            s2_config = Sentinel2Config(**s2_config_data)

            base_output_dir = path / self.file.folder
            base_output_dir.mkdir(parents=True, exist_ok=True)

            extractor = Sentinel2Extractor(config=s2_config, base_output_dir=base_output_dir)
            created_files = extractor.run()

            status = len(created_files) > 0
            return (status, {})  # noqa: TRY300

        except Exception as error:
            msg = f"ERROR: An exception occurred during Sentinel-2 processing: {error}"
            print(msg)
            return (False, {})


DOWNLOAD_HANDLERS: dict[str, DownloadHandler] = {
    "arcgis_geom_api": ArcgisGeomHandler,  # type: ignore  # noqa: PGH003
    "geom_shp_zip": GeomShpZipHandler,  # type: ignore  # noqa: PGH003
    "sentinel2": Sentinel2Handler,  # type: ignore  # noqa: PGH003
}
