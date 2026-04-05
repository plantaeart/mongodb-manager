"""Unit tests for ConnectionManager.import_connections backup_paths behaviour.

Covers:
  - _ensure_backup_paths: folder created when missing
  - _ensure_backup_paths: folder kept as-is when already exists
  - _ensure_backup_paths: invalid/unwritable path is silently skipped
  - import_connections: backup_paths stripped when import_backup_paths=False (default)
  - import_connections: missing folder created when import_backup_paths=True
  - import_connections: existing folder kept (not recreated) when import_backup_paths=True
  - import_connections: invalid path skipped (not stored) when import_backup_paths=True
  - import_connections: overwrite replaces backup_paths and creates missing folders
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from app.core.connection_ops import ConnectionManager


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_manager() -> tuple[ConnectionManager, MagicMock]:
    """Return a ConnectionManager wired to a MagicMock repository."""
    repo = MagicMock()
    repo.add_connection.return_value = True
    repo.update_connection.return_value = True
    manager = ConnectionManager(repository=repo)
    return manager, repo


SAMPLE_CONN = {
    "name": "my-conn",
    "host": "localhost",
    "port": 27017,
    "username": None,
    "password": None,
    "database": None,
    "auth_source": None,
    "description": "",
    "backup_paths": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# _ensure_backup_paths
# ─────────────────────────────────────────────────────────────────────────────

class TestEnsureBackupPaths:

    def test_creates_missing_folder(self, tmp_path):
        """A path that does not exist should be created."""
        target = tmp_path / "new-folder"
        assert not target.exists()

        result = ConnectionManager._ensure_backup_paths([str(target)])

        assert target.exists()
        assert target.is_dir()
        assert result == [str(target)]

    def test_keeps_existing_folder(self, tmp_path):
        """A path that already exists should be kept as-is."""
        target = tmp_path / "existing"
        target.mkdir()
        # Put a marker file inside to confirm it's untouched
        marker = target / "marker.txt"
        marker.write_text("keep me")

        result = ConnectionManager._ensure_backup_paths([str(target)])

        assert result == [str(target)]
        assert marker.exists(), "Existing folder content should be untouched"

    def test_creates_nested_folders(self, tmp_path):
        """mkdir(parents=True) should create the full path tree."""
        target = tmp_path / "a" / "b" / "c"
        assert not target.exists()

        result = ConnectionManager._ensure_backup_paths([str(target)])

        assert target.exists()
        assert result == [str(target)]

    def test_invalid_path_is_skipped(self):
        """A path that cannot be created (e.g. empty string) is silently skipped."""
        result = ConnectionManager._ensure_backup_paths([""])
        assert result == []

    def test_mixed_valid_and_invalid(self, tmp_path):
        """Valid paths are returned; invalid ones are dropped."""
        valid = tmp_path / "good"
        result = ConnectionManager._ensure_backup_paths([str(valid), ""])
        assert str(valid) in result
        assert "" not in result

    def test_empty_list_returns_empty(self):
        result = ConnectionManager._ensure_backup_paths([])
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# import_connections — backup_paths handling
# ─────────────────────────────────────────────────────────────────────────────

class TestImportConnectionsBackupPaths:

    def test_backup_paths_stripped_by_default(self, tmp_path):
        """import_backup_paths=False (default) → no backup_paths stored."""
        manager, repo = _make_manager()
        repo.get_connection.return_value = None  # new connection

        conn = {**SAMPLE_CONN, "backup_paths": [str(tmp_path / "folder")]}
        manager.import_connections([conn])  # import_backup_paths defaults to False

        # add_backup_path should never have been called
        repo.add_backup_path.assert_not_called()

    def test_missing_folder_created_on_import(self, tmp_path):
        """When import_backup_paths=True and folder missing → folder is created."""
        manager, repo = _make_manager()
        repo.get_connection.return_value = None  # new connection

        target = tmp_path / "missing-folder"
        assert not target.exists()

        conn = {**SAMPLE_CONN, "backup_paths": [str(target)]}
        result = manager.import_connections([conn], import_backup_paths=True)

        assert target.exists(), "Folder should have been created during import"
        repo.add_backup_path.assert_called_once_with("my-conn", str(target))
        assert result["imported"] == 1
        assert result["errors"] == []

    def test_existing_folder_kept_on_import(self, tmp_path):
        """When import_backup_paths=True and folder exists → linked without modification."""
        manager, repo = _make_manager()
        repo.get_connection.return_value = None  # new connection

        target = tmp_path / "existing-folder"
        target.mkdir()
        marker = target / "data.txt"
        marker.write_text("existing data")

        conn = {**SAMPLE_CONN, "backup_paths": [str(target)]}
        result = manager.import_connections([conn], import_backup_paths=True)

        assert marker.exists(), "Existing folder content should be untouched"
        repo.add_backup_path.assert_called_once_with("my-conn", str(target))
        assert result["imported"] == 1

    def test_invalid_path_not_stored(self):
        """When import_backup_paths=True and path is invalid → not stored in DB."""
        manager, repo = _make_manager()
        repo.get_connection.return_value = None

        conn = {**SAMPLE_CONN, "backup_paths": [""]}
        result = manager.import_connections([conn], import_backup_paths=True)

        repo.add_backup_path.assert_not_called()
        assert result["imported"] == 1  # connection itself still imported

    def test_overwrite_creates_missing_folder(self, tmp_path):
        """Overwrite=True + import_backup_paths=True → missing folder created."""
        manager, repo = _make_manager()

        target = tmp_path / "new-folder"
        assert not target.exists()

        # Simulate existing connection with a different path
        existing_conn = {**SAMPLE_CONN, "backup_paths": [str(tmp_path / "old-folder")]}
        repo.get_connection.return_value = existing_conn

        conn = {**SAMPLE_CONN, "backup_paths": [str(target)]}
        result = manager.import_connections([conn], overwrite=True, import_backup_paths=True)

        assert target.exists(), "New folder should have been created"
        # Old path removed, new path added
        repo.remove_backup_path.assert_called_once_with("my-conn", str(tmp_path / "old-folder"))
        repo.add_backup_path.assert_called_once_with("my-conn", str(target))
        assert result["overwritten"] == 1

    def test_overwrite_existing_folder_not_recreated(self, tmp_path):
        """Overwrite=True + folder already exists → folder untouched."""
        manager, repo = _make_manager()

        target = tmp_path / "existing"
        target.mkdir()
        marker = target / "keep.txt"
        marker.write_text("keep")

        repo.get_connection.return_value = {**SAMPLE_CONN, "backup_paths": []}

        conn = {**SAMPLE_CONN, "backup_paths": [str(target)]}
        manager.import_connections([conn], overwrite=True, import_backup_paths=True)

        assert marker.exists(), "Folder content should be untouched"
        repo.add_backup_path.assert_called_once_with("my-conn", str(target))
