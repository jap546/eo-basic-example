import json
import mimetypes
import os
import re
from datetime import datetime, timezone
from email.message import (
    Message,  # per https://peps.python.org/pep-0594/#cgi:~:text=Replacements%20for%20the,message.Message%20are%3A
)
from pathlib import Path
from typing import Any, Optional, Tuple, Union
from urllib.parse import urlencode

import dask
import pandas as pd
import requests
from dask.distributed import Client
from geopandas import GeoDataFrame
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from download.configure.file import EODatasetConfig
from download.setup.constants import Paths
from download.setup.logger import download_logger as logger


def delete_data(to_delete: list[Path]) -> None:
    """Delete all specified files.

    Arguments:
    ----------
    to_delete (list[Path]):
        List of files to delete

    Returns:
    --------
    None
    """
    for file in to_delete:
        logger.info(f"Deleting file: {file}")
        file.unlink()


def archive_data(to_archive: list[Path]) -> None:
    """Archive all specified files into a timestamped archive directory.

    Arguments:
    ----------
    to_archive (list[Path]):
        List of files to archive

    Returns:
    --------
    None
    """
    time = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H:%M:%S")
    archive_path = Paths.ARCHIVE_DATA_DIR / time
    archive_path.mkdir(parents=True)

    for file in to_archive:
        logger.info(f"Archiving file in folder: {time}")
        file.rename(archive_path / file.name)


def get_response_from_url(
    url: str, timeout: int = 10
) -> tuple[requests.Response | None, bool]:
    """Use requests.get to access the content of a specified URL.

    Uses the Retry class to handle intermittent failures and returns
    any errors encountered after 5 attempts.

    Arguments:
    ----------
    url (str):
        URL to be accessed

    timeout: (int):
        length of time to wait for response from server in seconds

    Returns:
    --------
    Optional[requests.Response]: The data payload

    str: Status flag for whether any errors were encountered
    """
    retries = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=list(range(400, 600)),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retries)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        # Ensure the URL is a proper string and pass it directly into requests.get
        if isinstance(url, str):
            resp: Optional[requests.Response] = session.get(url, timeout=timeout)
        else:
            logger.error(f"Invalid URL type: {type(url)}. Expected a string.")
            return None, False

        if resp is not None and resp.status_code >= 400:
            error = (
                f"Error: Received status code: {resp.status_code}, "
                f"{resp.reason} for URL: {url}"
            )
            logger.error(error)
            return None, False
    except requests.exceptions.RequestException as e:
        error = f"Error: An error occurred while making request: {e}"
        logger.error(error)
        return None, False

    return resp, True


FILE_TYPE_HANDLER = {
    "json": "json",
    "geojson": "json",
    "csv": "csv",
    "xlsx": "xlsx",
    "ods": "ods",
    "xls": "xls",
    "html": "html",
    "zip": "zip",
    "bin": "zip",
}


def validate_file(ext: str, resp: requests.Response) -> bool:
    """Validate that the content return from a URL conforms to expectations.

    Arguments:
    ----------
    ext (str):
        File extension expected from config
    resp (requests.Response):
        Content retrieved from URL

    Retruns:
    --------
    bool: Whether the file was valid or not
    """
    expected_ext = ext.lower()
    content_type = resp.headers.get("Content-Type", "")
    if not content_type:
        logger.warning("Cannot validate file type/content")
        return True
    m = Message()
    m["content-type"] = content_type
    mimetype, _ = m.get_params()[0]  # type: ignore
    extension = mimetypes.guess_extension(mimetype)

    if extension:
        extension = extension.lstrip(".")
        if extension not in FILE_TYPE_HANDLER:
            logger.error(f"Error: Unsupported file extension: {extension}")
            return False

        file_type = FILE_TYPE_HANDLER[extension]
        if file_type != expected_ext:
            logger.error(f"Error: Expected '{expected_ext}', but found '{file_type}'")
            return False

        return True

    logger.warning("Warning: Unable to determine file extension")
    return True


def retrieve_file(url: str, file_ext: str) -> Tuple[requests.Response | None, bool]:
    """Retrieve file from URL and undertake validation of the returned content.

    Arguments:
    ----------
    url (str):
        URL to download the data from
    file_ext (str):
        Expected file extension, used for validation

    Returns:
    --------
    Optional[requests.Response]: The data payload

    bool: Status flag for whether any errors were encountered
    """
    resp, status = get_response_from_url(url)

    if resp is None or not status:
        return None, status

    valid = validate_file(file_ext, resp)

    if not valid:
        return None, valid

    return resp, True


def encode_params(api_params: dict[Any, Any]) -> str:
    """Encodes all populated parameter values from the ApiParams class.

    Arguments:
    ----------
    api_params (ApiParams):
        The API params pulled from the download config

    Returns:
    --------
    str: The encoded parameter values to append to the URL
    """
    populated_params = {
        key: value for key, value in api_params.items() if value is not None
    }
    return urlencode(populated_params)


def iterative_geo_api_retrieve(
    params: dict[str, Union[str, int, None]], offset: int, url: str, max_retries: int
) -> Tuple[GeoDataFrame | None, bool]:
    """Iteratively call a given api URL (specifically for geometry data).

    Uses the offset parameter to iteratively call subsequent batches of data
    from the API. Then stitches each batch together into a single GeoDataFrame.

    Arguments:
    ----------
    params (dict[str, Union[str, int, None]]):
        Parameter values for accessing the API
    offset (int):
        Batch size of records to retrieve in each iteration
    url (str):
        URL of the API endpoint
    max_retries (int):
        number of times to attempt to download the file

    Returns:
    --------
    GeoDataFrame | None: The data paylod (or None, if an error is encountered)

    bool: Status flag for whetherany errors were encountered
    """
    iteration = 1
    raw_data: list[dict[Any, Any]] = []

    while True:
        params["resultOffset"] = offset * (iteration - 1)

        for retry in range(1, max_retries + 1):
            url_params = url + encode_params(params)
            resp, status = get_response_from_url(url_params, timeout=70)

            if not status:
                return None, False

            ret_json = resp.json()  # type: ignore

            if "features" in ret_json:
                break

            if retry == max_retries:
                logger.error(
                    f"Failed to download data at position: {params['resultOffset']}-"
                    f"{int(params['resultOffset']) + offset}"  # type: ignore
                )

                return None, False

        if not ret_json["features"]:
            break

        raw_data.append(ret_json)

        if offset == 0:
            break  # If no offset, then only iterate once, as all data downloaded in one go

        iteration += 1

    gdf = GeoDataFrame()

    for ret in raw_data:
        tmp_gdf = GeoDataFrame.from_features(ret, crs=4326)
        gdf = GeoDataFrame(
            pd.concat([gdf, tmp_gdf], axis=0, ignore_index=True), crs=4326
        )

    return gdf, True


def generate_slug(name: str, delimiter: str = "-") -> str:
    """Replace spaces with specified delimiter.

    Arguments:
    ----------
    name (str):
        String to be altered
    delimiter (str):
        String to be inserted into spaces

    Returns:
    --------
    str: Standardised slug to use in the filepath
    """
    name = re.sub(" +", " ", name)
    return name.lower().replace(" ", delimiter)


def generate_data_path(path: Path, folder: str, title: str, ext: str) -> Path:
    """Create standardised filepath for downloaded files.

    Arguments:
    ----------
    path: (Path):
        The base folder path to use
    folder (str):
        The folder name to download the data into
    title (str):
        The name of the files
    ext (str):
        The file extension to use

    Returns:
    --------
    Path: Standardised file path to save the file to
    """
    filepath: Path = path / generate_slug(folder, delimiter="-") / f"{title}.{ext}"

    filepath.parent.mkdir(exist_ok=True, parents=True)

    return filepath


def calc_years_in_range(year: str) -> list[int]:
    """Generate all the years between two given years.

    Arguments:
    ----------
    year (str):
        A hyphen delimited range of years (e.g., 2019-2024)

    Returns:
    --------
    list[int]: All years between the two given years (inclusive)
    """
    split_year = year.split("-")
    return (
        [int(split_year[0])]
        if len(split_year) == 1
        else list(range(int(split_year[0]), int(split_year[1]) + 1))
    )


def get_total_available_memory(check_jupyter_hub: bool = True) -> int:  # noqa: FBT001, FBT002
    """Calculate how much memory is available.

    1. Check MEM_LIMIT environment variable, set by jupyterhub
    2. Use hardware information if that not set
    """
    if check_jupyter_hub:
        mem_limit = os.environ.get("MEM_LIMIT", None)
        if mem_limit is not None:
            return int(mem_limit)

    from psutil import virtual_memory

    return virtual_memory().total


def compute_memory_per_worker(
    n_workers: int = 1,
    mem_safety_margin: Optional[Union[str, int]] = None,
    memory_limit: Optional[Union[str, int]] = None,
) -> int:
    """Calculate how much memory to assign per worker.

    result can be passed into ``memory_limit=`` parameter of dask worker/cluster/client
    """
    from dask.utils import parse_bytes

    if isinstance(memory_limit, str):
        memory_limit = parse_bytes(memory_limit)

    if isinstance(mem_safety_margin, str):
        mem_safety_margin = parse_bytes(mem_safety_margin)

    if memory_limit is None and mem_safety_margin is None:
        total_bytes = get_total_available_memory()
        # leave 500Mb or half of all memory if RAM is less than 1 Gb
        mem_safety_margin = min(500 * (1024 * 1024), total_bytes // 2)
    elif memory_limit is None:
        total_bytes = get_total_available_memory()
    elif mem_safety_margin is None:
        total_bytes = memory_limit
        mem_safety_margin = 0
    else:
        total_bytes = memory_limit

    return (total_bytes - mem_safety_margin) // n_workers


def start_local_dask(
    n_workers: int = 1,
    threads_per_worker: Optional[int] = None,
    mem_safety_margin: Optional[Union[str, int]] = None,
    memory_limit: Optional[Union[str, int]] = None,
    **kw: dict,
) -> Client:
    """Wrapper around ``distributed.Client(..)`` constructor that deals with memory better.

    It also configures ``distributed.dashboard.link`` to go over proxy when operating
    from behind jupyterhub.

    :param n_workers: number of worker processes to launch
    :param threads_per_worker: number of threads per worker, default is as many as there are CPUs
    :param memory_limit: maximum memory to use across all workers
    :param mem_safety_margin: bytes to reserve for the rest of the system, only applicable
                              if ``memory_limit=`` is not supplied.

    .. note::

        if ``memory_limit=`` is supplied, it will be parsed and divided equally between workers.
    """
    # if dashboard.link set to default value and running behind hub, make dashboard link go via proxy
    if (
        dask.config.get("distributed.dashboard.link")
        == "{scheme}://{host}:{port}/status"
    ):
        jup_prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX")
        if jup_prefix is not None:
            jup_prefix = jup_prefix.rstrip("/")
            dask.config.set(
                {"distributed.dashboard.link": f"{jup_prefix}/proxy/{{port}}/status"}
            )

    memory_limit = compute_memory_per_worker(
        n_workers=n_workers,
        memory_limit=memory_limit,
        mem_safety_margin=mem_safety_margin,
    )

    return Client(
        n_workers=n_workers,
        threads_per_worker=threads_per_worker,
        memory_limit=memory_limit,
        **kw,
    )


def load_eo_config(config_path: Path) -> list[dict]:
    """Wrapper to open and load EO config."""
    with open(config_path) as f:  # noqa: PTH123
        config_data = json.load(f)

    return [
        {
            "folder": folder["folder"],
            "datasets": [
                # Ensure the 'folder' is correctly passed in the 'file_config' and the 'title' is passed
                EODatasetConfig(
                    title=dataset["file_config"]["title"],  # Explicitly set title
                    file_config={
                        **dataset["file_config"],
                        "folder": folder["folder"],
                    },  # Set the folder
                    stac_config=dataset["stac_config"],  # Pass stac_config as is
                    handler_config=dataset[
                        "handler_config"
                    ],  # Pass handler_config as is
                    download_method=dataset[
                        "download_method"
                    ],  # Pass download_method as is
                )
                for dataset in folder["datasets"]
            ],
        }
        for folder in config_data
    ]
