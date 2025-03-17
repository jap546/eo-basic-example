import json
import time
from dataclasses import dataclass
from pathlib import Path

from download import Config, Downloader
from download.downloader import eo_downloader
from download.setup.logger import download_logger as logger


@dataclass
class DownloadError(Exception):
    def __init__(self) -> None:
        super().__init__("One or more files failed to download.")


def download_missing_files(attempts: int = 3) -> None:
    status = True

    with Path("download_config.json").open(encoding="utf-8") as f:
        config_file = json.load(f)

    config = Config(config_file)
    db = Downloader(config=config)

    for try_attempt in range(1, attempts + 1):
        status = db.update()

        if status:
            logger.info("All missing data successfully downloaded.")
            break

        logger.info(
            f"Retrying failed downloads after 30 seconds (attempt number: {try_attempt + 1})."
        )
        time.sleep(30)

    if not status:
        logger.critical("One or more files failed to download.")
        raise DownloadError

    logger.info("Successfully downloaded vector data.")

    # placeholder for EO download
    logger.info("Downloading raster data.")
    eo_downloader()
    logger.info("Successfully downloaded raster data.")
