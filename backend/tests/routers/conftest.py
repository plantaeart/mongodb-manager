"""Shared fixtures for router integration tests

Fixtures here are auto-discovered by pytest for all files under tests/routers/.
No imports needed in individual test files.

Fixtures provided:
  - mock_cli_app             : patches the CLI dispatcher used by Path B commands
                               (connect list, connect add) and Path A multi-connection
                               commands (connect remove, connect test)
  - mock_connection_manager  : patches ConnectionManager used by Path A direct-dispatch
                               commands (connect update, backup folder add/delete, etc.)
                               Pre-wired with sensible defaults; override per test as needed.
  - mock_backup_manager      : patches BackupManager used by backup create/restore commands.
                               Pre-wired with sensible defaults; override per test as needed.
  - mock_path_exists         : patches pathlib.Path.exists() inside app.routers.commands
                               (backup folder add/delete filesystem checks)
  - mock_os_access           : patches os.access() inside app.routers.commands
                               (backup folder add writability check)
  - mock_shutil_rmtree       : patches shutil.rmtree() inside app.routers.commands
                               (backup folder delete disk deletion)
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_cli_app():
    """Patch app.routers.commands.cli_app for the duration of one test.

    Yields the MagicMock so individual tests can configure side_effect / return_value:

        def test_something(client, auth_headers, mock_cli_app):
            mock_cli_app.return_value = None          # silent success
            mock_cli_app.side_effect = my_side_effect # write to stdout, raise SystemExit, etc.
            response = client.post(...)
    """
    with patch("app.routers.commands.cli_app") as mock:
        yield mock


@pytest.fixture
def mock_connection_manager():
    """Patch ConnectionManager at every router module that imports it at module level.

    Since Phase 5.2 moved imports from deferred (inside functions) to module-level,
    we must patch the name at each binding site so tests intercept the right class.

    Yields the *instance* mock (MockCM.return_value) pre-wired with safe defaults:
      - get_connection()                        → sample connection dict
      - update_connection()                     → True
      - add_backup_path()                       → True
      - remove_backup_path()                    → True
      - repository.build_uri_from_connection()  → "mongodb://localhost:27017"

    Override any attribute before calling the endpoint:

        def test_something(client, auth_headers, mock_connection_manager):
            mock_connection_manager.update_connection.return_value = False
            mock_connection_manager.get_connection.return_value = None
            response = client.post(...)
    """
    # Patch all three module-level binding sites (one shared instance mock)
    with patch("app.routers.commands.connect.ConnectionManager") as MockCM, \
         patch("app.routers.commands.backup_folder.ConnectionManager", MockCM), \
         patch("app.routers.commands.backup_ops.ConnectionManager", MockCM):

        instance = MockCM.return_value

        # Default connection returned by get_connection()
        instance.get_connection.return_value = {
            "name": "test-conn",
            "host": "localhost",
            "port": 27017,
            "username": None,
            "password": None,
            "database": None,
            "auth_source": "admin",
            "description": "Test connection",
            "backup_paths": ["/backups/test-conn-backups"],
        }

        instance.update_connection.return_value = True
        instance.add_backup_path.return_value = True
        instance.remove_backup_path.return_value = True
        instance.repository = MagicMock()
        instance.repository.build_uri_from_connection.return_value = "mongodb://localhost:27017"

        yield instance


@pytest.fixture
def mock_path_exists():
    """Patch pathlib.Path.exists() inside app.routers.commands.

    Defaults to True (path exists). Override per test:

        def test_something(mock_path_exists):
            mock_path_exists.return_value = False
    """
    with patch("pathlib.Path.exists", return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_path_mkdir():
    """Patch pathlib.Path.mkdir() inside app.routers.commands.

    Defaults to a no-op (directory created successfully). Override to raise:

        def test_something(mock_path_mkdir):
            mock_path_mkdir.side_effect = PermissionError("denied")
    """
    with patch("pathlib.Path.mkdir") as mock:
        yield mock


@pytest.fixture
def mock_os_access():
    """Patch os.access() inside app.routers.commands.

    Defaults to True (path is writable). Override per test:

        def test_something(mock_os_access):
            mock_os_access.return_value = False
    """
    with patch("os.access", return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_shutil_rmtree():
    """Patch shutil.rmtree() inside app.routers.commands.

    Defaults to a no-op (deletion succeeded). Override to raise:

        def test_something(mock_shutil_rmtree):
            mock_shutil_rmtree.side_effect = OSError("permission denied")
    """
    with patch("shutil.rmtree") as mock:
        yield mock


@pytest.fixture
def mock_backup_manager():
    """Patch BackupManager at the router module that imports it at module level.

    Since Phase 5.2 moved the import to module-level in backup_ops.py,
    we patch the binding site there so tests intercept the right class.

    Yields the *instance* mock (MockBM.return_value) pre-wired with safe defaults:
      - list_backups()    → one sample backup dict with name, backup_name, and path
      - create_backup()   → Path("/backups/test-conn-backups/my-backup")
      - restore_backup()  → None (success)

    Override any attribute before calling the endpoint:

        def test_something(client, auth_headers, mock_backup_manager):
            mock_backup_manager.create_backup.side_effect = ValueError("already exists")
            mock_backup_manager.list_backups.return_value = []
    """
    with patch("app.routers.commands.backup_ops.BackupManager") as MockBM:
        instance = MockBM.return_value

        instance.list_backups.return_value = [
            {
                "name": "my-backup",
                "backup_name": "my-backup",
                "path": Path("/backups/test-conn-backups/my-backup"),
                "connection_name": "test-conn",
                "timestamp": "20260322_120000",
                "created_at": "2026-03-22T12:00:00",
                "databases": ["testdb"],
                "size": 1024,
            }
        ]
        instance.create_backup.return_value = Path("/backups/test-conn-backups/my-backup")
        instance.restore_backup.return_value = None

        yield instance
