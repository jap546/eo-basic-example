import warnings
from dataclasses import dataclass, field

from download.configure.file import File
from download.process.handlers import DOWNLOAD_HANDLERS, DownloadHandler


@dataclass
class Config:
    """Converts a valid configuration file into the download model.

    Accepts a dict object as a configuration file and parses it into instances of
    the corresponding download handlers, as specified in each config entry.
    Creates the 'entries' attributes, which is a dictionary of DownloadHandler
    objects which can be iterated over and processed.

    Attributes:
    -----------
    config_file (list[dict[str, str | list[dict[str, str | dict[str, str | int | bool | dict[str, str | int]]]]]]):
        Dictionary object containing a 'plain text' download configuration
    """

    config_file: list[
        dict[
            str,
            str
            | list[dict[str, str | dict[str, str | int | bool | dict[str, str | int]]]],
        ]
    ]

    entries: list[DownloadHandler] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        """Convert every entry in the config file to the appropriate DownloadHandler.

        The 'file_config' is converted to an instance of the File class and is passed,
        along with the attributes in the 'handler_config' to the DownloadHandler
        specified by the download method.

        Each entry is added to the 'entries' attribute.

        Returns:
        --------
            None
        """
        for folder_config in self.config_file:
            for dataset in folder_config["datasets"]:
                file = File(
                    folder=folder_config["folder"],  # type: ignore
                    **dataset["file_config"],  # type: ignore
                )

                self.entries.append(
                    DOWNLOAD_HANDLERS[dataset["download_method"]](  # type: ignore
                        file=file,
                        **dataset["handler_config"],  # type: ignore
                    )
                )

        self._find_duplicate_url()
        self._find_duplicate_filename()

    def _find_duplicate_url(self) -> None:
        """Find all URLs which are contained in more than one config entry.

        Raises a warning if any URLs are contained in more than one config entry.
        If the URLs are for zip files, then prompts the user to edit the config to
        use the capability to extract multiple files. Ignores cases where the URL is
        defined for the EESHandler or GeomZipHander which download zip files but only
        handle one file at a time.

        Arguments:
        ----------
        None

        Returns:
        --------
        None
        """
        urls: list[str] = []
        zip_urls: list[str] = []

        for entry in self.entries:
            url = entry.file.url
            if type(entry).__name__ == "ZipHandler":
                if url in zip_urls:
                    msg = f"You are downloading a zip file from url: '{url}' more than once. You can extract multiple files from the same zip file within a single config entry. Consult the documentation for more information."
                    warnings.warn(msg, stacklevel=1)
                else:
                    zip_urls.append(url)
            elif type(entry).__name__ not in [
                "ArcgisGeomHandler",
            ]:
                if url in urls:
                    msg = f"You have more than one config entry pointing to the file located at: '{url}'. This will download multiple duplicate files."
                    warnings.warn(msg, stacklevel=1)
                else:
                    urls.append(url)

    def _find_duplicate_filename(self) -> None:
        """Find if a config entry with this filename already exists.

        Arguments:
        ----------
        None

        Returns:
        --------
        None
        """
        filenames: list[str] = []

        for entry in self.entries:
            for filename in entry.filenames:
                if filename in filenames:
                    msg = f"You have more than one config entry generating a filename of: '{filename}'."
                    warnings.warn(msg, stacklevel=1)
                else:
                    filenames.append(filename)

    def find_file_config(self, filename: str) -> DownloadHandler:
        """Find config entry for the searched for filename.

        Arguments:
        ----------
        filename (str):
            The name of the file to find the config entry for

        Returns:
        --------
        DownloadHandler: The instance of DownloadHander containing the
        searched for filename
        """
        for entry in self.entries:
            if filename in entry.filenames:
                return entry
        err = f"Filename: {filename} does not exist in the config object"
        raise ValueError(err)

