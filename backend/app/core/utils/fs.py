"""Filesystem utilities for MongoDB Manager"""

import shutil
from pathlib import Path


def delete_directory_if_exists(path: str | Path) -> bool:
    """Resolve *path* to an absolute path and delete it with all its contents.

    If the path does not exist the function returns ``False`` without raising.
    If deletion fails an exception is propagated to the caller.

    Args:
        path: Directory path to delete (relative or absolute).

    Returns:
        ``True`` if the directory existed and was deleted, ``False`` if it did
        not exist.

    Raises:
        Exception: If ``shutil.rmtree`` fails (e.g., permission error).

    Examples:
        >>> delete_directory_if_exists("/tmp/my-backup")
        True
    """
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = Path.cwd() / path_obj
    path_obj = path_obj.resolve()

    if not path_obj.exists():
        return False

    shutil.rmtree(path_obj)
    return True
