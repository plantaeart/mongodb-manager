"""Shared fixtures for router integration tests

Fixtures here are auto-discovered by pytest for all files under tests/routers/.
No imports needed in individual test files.

Two fixtures are provided:
  - mock_cli_app             : patches the CLI dispatcher used by Path B commands
                               (connect list, connect add) and Path A multi-connection
                               commands (connect remove, connect test)
  - mock_connection_manager  : patches ConnectionManager used by Path A direct-dispatch
                               commands (connect update, backup folder add/delete, etc.)
                               Pre-wired with sensible defaults; override per test as needed.
"""

import pytest
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
    """Patch app.routers.commands.ConnectionManager for the duration of one test.

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
    with patch("app.core.connection_ops.ConnectionManager") as MockCM:
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
