import logging
from typing import Any, Tuple

from download.setup.constants import Paths

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")


def setup_logger(name: str, log_file: str, level: Any = logging.INFO) -> logging.Logger:
    """Logger Template."""
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(streamhandler)

    return logger


def loggers() -> Tuple[logging.Logger, ...]:
    Paths.LOGS_DIR.mkdir(exist_ok=True, parents=True)
    logger_names = [
        "download_logger",
    ]

    return tuple(
        setup_logger(name, str(Paths.LOGS_DIR / f"{name.split('_')[0]}.log"))
        for name in logger_names
    )


(download_logger,) = loggers()
