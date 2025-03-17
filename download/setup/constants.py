from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path("data")
DATA_DIR = Path(os.environ.get("DOWNLOAD_DATA_DIR") or DEFAULT_DATA_DIR)


class Paths:
    LOGS_DIR = Path(DATA_DIR / "logs")
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    ARCHIVE_DATA_DIR: Path = DATA_DIR / "archive"
    TEST_PATH = Path("tests/download/test_data")


GEOMETRY_SERVERS = {"ons": "/FeatureServer/0/query?", "scot": "/query?"}
