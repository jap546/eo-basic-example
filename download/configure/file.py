from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl, field_validator

from download.configure.validate import validators as valid


class File(BaseModel):
    """Pydantic model representation of the core definition of a download config entry.

    Utilises Pydantic validators to enforce content and format restrictions on each
    attribute of each config entry. Will throw and exception if any of these rules
    are violated.

    Attributes:
    -----------
    folder (str):
        Name of the subfolder to store the data within the raw folder.
        The folder is created if it does not already exist.

    url (str):
        URL for where the data is stored.

    file_ext (str):
        File extension of the file when downloaded.

    write_to_disk (bool):
        Whether the downloaded data should be written to disk.
    """

    folder: str
    url: str
    file_ext: str
    write_to_disk: Optional[bool] = False

    @field_validator("folder")
    @classmethod
    def folder_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, folder: str
    ) -> str:
        """Validate the format of the folder."""
        return valid.validate_folder(folder)

    @field_validator("url")
    @classmethod
    def url_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, url: str
    ) -> str:
        """Validate the format of the url."""
        return valid.validate_url(url)

    @field_validator("file_ext")
    @classmethod
    def file_ext_valid(  # pylint: disable=no-self-argument, no-self-use
        cls, ext: str
    ) -> str:  # pylint: disable=no-self-argument, no-self-use
        """Validate the file extension."""
        return valid.validate_file_ext(ext)

# Pydantic Models for EO Configuration
class EOFileConfig(BaseModel):
    """Base model for file config."""

    folder: str
    title: str


class EOStacConfig(BaseModel):
    """Base model for stac config."""

    url: HttpUrl
    collections: List[str]
    bbox: List[float]
    datetime: str
    query: Dict[str, Any]


class EOHandlerConfig(BaseModel):
    """Base model for handler config."""

    assets: List[str]
    chunksize: Any
    resolution: int
    epsg: int


class EODatasetConfig(BaseModel):
    """Base model for EO dataset."""

    download_method: str
    file_config: EOFileConfig
    stac_config: EOStacConfig
    handler_config: EOHandlerConfig
