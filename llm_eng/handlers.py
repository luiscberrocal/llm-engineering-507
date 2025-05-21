from datetime import datetime
from pathlib import Path


def get_file_age(path: Path) -> float:
    """
    Get the age of a file in hours.

    Args:
        path (Path): The path to the file.

    Returns:
        float: The age of the file in hours.
    """
    if path.exists():
        now = datetime.now().timestamp()
        return (now - path.stat().st_mtime) // 3600
    else:
        return 0.0
