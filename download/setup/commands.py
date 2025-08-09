from download.setup.constants import Paths


def create_project_directories() -> None:
    """Create all necessary project directories."""
    Paths.ensure_directories_exist()
