from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from download import Config
from download.process import util as u
from download.process.handlers import process_eo_data
from download.process.util import archive_data, delete_data
from download.setup.constants import Paths
from download.setup.logger import download_logger as logger


@dataclass
class Downloader:
    """Controller for the download process.

    Identifies all entries in the Config which are not currently present in the
    file store. Then executes the download method for each.

    Attributes:
    -----------
    config (Config):
        The Config object containing all files that need to be downloaded.

    raw_directory (Path):
        Path to write downloaded files to. Defaults to "data/raw".

    archive (bool):
        Whether redundant files are archived or deleted.

    data (dict[str, Any]):
        Dictionary to store all downloaded files. Will be stored in original
        downloaded format (e.g., bytes) unless otherwise transformed by the
        individual handler.
    """

    config: Config
    raw_directory: Path = Paths.RAW_DATA_DIR
    archive: bool = False
    data: dict[str, Any] = field(init=False, default_factory=dict)

    @property
    def existing_files(self) -> list[str]:
        """Property containing a list of all filenames of files already downloaded."""
        existing_files = list(self.raw_directory.glob("**/*.*"))
        return sorted(
            [
                str(title.stem)
                for title in existing_files
                if "DS_Store" not in str(title)
            ]
        )

    @property
    def required_files(self) -> list[str]:
        """Property containing filenames of all files required to be downloaded."""
        return sorted(
            [filename for entry in self.config.entries for filename in entry.filenames]
        )

    @property
    def old_data(self) -> list[Path]:
        """Property containing filnames of existing files that are no longer in the config."""
        existing_files = list(self.raw_directory.glob("**/*.*"))
        existing_files_paths = [
            file for file in existing_files if "DS_Store" not in str(file)
        ]
        return [
            file
            for file in existing_files_paths
            if file.stem not in self.required_files
        ]

    def missing(self) -> list[str]:
        """Return all required files that have not been downloaded yet.

        Returns:
        --------
            list[str]: All file titles which have not been downloaded
        """
        return list(set(self.required_files) - set(self.existing_files))

    def check(self) -> bool:
        """Check whether any files need deleting or downloading.

        Returns:
        --------
        bool: Whether any files need deleting or downloading
        """
        return self.required_files == self.existing_files

    def update(self) -> bool:
        """Iterate over the missing files and download them.

        If there is at least one missing file, or file to be deleted. Then all 'old'
        files are deleted. Then for each missing file, the corresponding download
        handler is identified and its execute method called.

        An exception is raised if any of the files fails to download.
        """
        download_status = True

        if self.check():
            logger.info("Data is up to date")
            return download_status

        if self.archive:
            archive_data(self.old_data)
        else:
            delete_data(self.old_data)

        for missing_file in self.missing():
            file = self.config.find_file_config(missing_file)

            logger.info(f"Downloading file: {missing_file}")

            status, data = file.execute(self.raw_directory)

            if status:
                for filename, data_item in data.items():
                    self.data[filename] = data_item

            if not status:
                download_status = False

        return download_status

# TO DO: refactor into pydantic approach
def eo_downloader():
    """Temporary wrapper to handle EO download config."""
    client = u.start_local_dask(n_workers=4, mem_safety_margin="1GB")

    config_path = Path("download_config_raster.json")

    folder_datasets = u.load_eo_config(config_path)

    for folder_data in folder_datasets:
        folder_name = folder_data["folder"]

        raw_data_dir = (
            Paths.RAW_DATA_DIR / folder_name
        )

        raw_data_dir.mkdir(parents=True, exist_ok=True)

        for dataset in folder_data["datasets"]:
            result = process_eo_data(dataset)

            for k, v in result.items():
                print(f"{k}: {v}")
    
    client.shutdown()