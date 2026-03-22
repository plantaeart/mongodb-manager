"""Path utilities for MongoDB Manager backup folder management"""

from app.core.utils.config import BACKUP_BASE_DIR, BACKUP_FOLDER_SUFFIX


def normalize_backup_folder_path(folder_path_input: str) -> str:
    """Normalize a backup folder path by enforcing base dir prefix and suffix.

    Applies two rules:
    1. Ensures the path starts with ``BACKUP_BASE_DIR``.
    2. Ensures the path ends with ``BACKUP_FOLDER_SUFFIX``.

    Both rules are idempotent — calling the function on an already-normalized
    path returns the same value.

    Args:
        folder_path_input: Raw folder path as supplied by the user (may be
            relative, absolute, with or without the suffix).

    Returns:
        Fully normalized absolute-style backup folder path.

    Examples:
        >>> normalize_backup_folder_path("my-project")
        '/backups_mongodb_manager/my-project_mongodb_manager'
        >>> normalize_backup_folder_path("/backups_mongodb_manager/my-project")
        '/backups_mongodb_manager/my-project_mongodb_manager'
    """
    clean_path = folder_path_input.strip().strip("/")

    # Remove the base dir prefix so we work only with the user-supplied segment
    if clean_path.startswith(BACKUP_BASE_DIR.lstrip("/")):
        clean_path = clean_path[len(BACKUP_BASE_DIR.lstrip("/")):].strip("/")

    folder_path_base = f"{BACKUP_BASE_DIR}/{clean_path}"

    if not folder_path_base.endswith(BACKUP_FOLDER_SUFFIX):
        return f"{folder_path_base}{BACKUP_FOLDER_SUFFIX}"

    return folder_path_base
