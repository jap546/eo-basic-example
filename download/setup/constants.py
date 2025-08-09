from __future__ import annotations

from pathlib import Path

TOP_FOLDER = Path(__file__).resolve().parent.parent.parent


class Paths:
    TOP_FOLDER: Path = TOP_FOLDER
    DATA_DIR: Path = TOP_FOLDER / "data"
    LOGS_DIR: Path = DATA_DIR / "logs"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    ARCHIVE_DATA_DIR: Path = DATA_DIR / "archive"
    TEST_PATH: Path = Path("tests/download/test_data")

    @classmethod
    def ensure_directories_exist(cls) -> None:
        """Create directories if they don't exist."""
        directories = [
            getattr(cls, attr) for attr in dir(cls) if isinstance(getattr(cls, attr), Path)
        ]

        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)


GEOMETRY_SERVERS = {"ons": "/FeatureServer/0/query?", "scot": "/query?"}
