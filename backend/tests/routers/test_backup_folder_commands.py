"""Integration tests for Backup Folder Management commands

Commands covered:
  - backup folder list   (Path B — generic CLI fallback)
  - backup folder add    (Path A — special, direct ConnectionManager + filesystem)
  - backup folder delete (Path A — special, direct ConnectionManager + shutil)

Already covered in test_commands.py (NOT duplicated here):
  - backup folder delete — confirmation: False
  - backup folder delete — missing connection_name
  - backup folder delete — missing folder_path

Fixtures used from tests/routers/conftest.py (auto-discovered by pytest):
  - mock_cli_app            : patches app.routers.commands.cli_app
  - mock_connection_manager : patches app.core.connection_ops.ConnectionManager
  - mock_path_exists        : patches pathlib.Path.exists()
  - mock_path_mkdir         : patches pathlib.Path.mkdir()
  - mock_os_access          : patches os.access() inside app.routers.commands
  - mock_shutil_rmtree      : patches shutil.rmtree() inside app.routers.commands

Fixtures used from tests/conftest.py:
  - client       : FastAPI TestClient
  - auth_headers : Authorization header with valid JWT

Path normalization (backup folder add):
  BACKUP_BASE_DIR   = /backups_mongodb_manager  (default env value)
  BACKUP_FOLDER_SUFFIX = _mongodb_manager
  Input "myconn" → normalized to "/backups_mongodb_manager/myconn_mongodb_manager"
"""

import sys


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post(client, auth_headers, command, params):
    """Shorthand for posting to /api/commands/execute"""
    return client.post(
        "/api/commands/execute",
        json={"command": command, "params": params},
        headers=auth_headers,
    )


def _make_stdout_writer(text):
    """Return a cli_app side_effect that writes *text* to the redirected stdout"""
    def _side_effect(args, standalone_mode=False):
        sys.stdout.write(text)
    return _side_effect


# ── backup folder list ────────────────────────────────────────────────────────

class TestBackupFolderList:
    """backup folder list goes through Path B (generic CLI fallback)."""

    def test_success(self, client, auth_headers, mock_cli_app):
        """cli_app writes output → success: True, output forwarded as-is"""
        mock_cli_app.side_effect = _make_stdout_writer(
            "Backup folders for test-conn:\n  /backups_mongodb_manager/test-conn_mongodb_manager\n"
        )

        response = _post(client, auth_headers, "backup folder list", {
            "connection_name": "test-conn"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0


# ── backup folder add ─────────────────────────────────────────────────────────

class TestBackupFolderAdd:
    """backup folder add goes through Path A (special).

    Uses ConnectionManager directly for connection lookup and path registration,
    plus real filesystem calls (Path.exists, Path.mkdir, os.access) which are
    patched per test.
    """

    # ── guard clauses (no filesystem involvement) ─────────────────────────────

    def test_missing_connection_name(self, client, auth_headers, mock_connection_manager):
        """No connection_name → success: False, error mentions 'connection'"""
        response = _post(client, auth_headers, "backup folder add", {
            "folder_path": "/backups_mongodb_manager/test_mongodb_manager"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "connection" in data["error"].lower()

    def test_connection_name_as_list_uses_first_element(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_os_access
    ):
        """connection_name given as list → first element used, proceeds normally"""
        mock_connection_manager.add_backup_path.return_value = True

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": ["test-conn", "other-conn"],
            "folder_path": "myconn",
        })

        assert response.status_code == 200
        # Verify add_backup_path was called with the first connection name
        call_args = mock_connection_manager.add_backup_path.call_args
        assert call_args.args[0] == "test-conn"

    def test_missing_folder_path(self, client, auth_headers, mock_connection_manager):
        """No folder_path → success: False, error mentions 'folder' or 'path'"""
        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "folder" in data["error"].lower() or "path" in data["error"].lower()

    def test_connection_not_found(self, client, auth_headers, mock_connection_manager):
        """get_connection returns None → success: False, error mentions 'not found'"""
        mock_connection_manager.get_connection.return_value = None

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "ghost-conn",
            "folder_path": "myconn",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    # ── path normalization ────────────────────────────────────────────────────

    def test_path_normalization_adds_base_dir_and_suffix(
        self, client, auth_headers, mock_connection_manager
    ):
        """Raw folder name is normalized: BACKUP_BASE_DIR prefix + BACKUP_FOLDER_SUFFIX.

        With create_if_missing=False and the path not existing, the error message
        contains the fully-normalized path — confirming the transformation happened.
        """
        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn",
            "folder_path": "myconn",
            "create_if_missing": False,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        # Normalized path must appear in the error
        assert "/backups_mongodb_manager/myconn_mongodb_manager" in data["error"]

    # ── filesystem branch tests ───────────────────────────────────────────────

    def test_path_not_exist_create_if_missing_false(
        self, client, auth_headers, mock_connection_manager, mock_path_exists
    ):
        """Path doesn't exist + create_if_missing=False → 'does not exist' error"""
        mock_path_exists.return_value = False

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn",
            "folder_path": "myconn",
            "create_if_missing": False,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "does not exist" in data["error"].lower()

    def test_path_not_exist_mkdir_fails(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_path_mkdir
    ):
        """Path doesn't exist + create_if_missing=True + mkdir raises → 'Failed to create directory'"""
        mock_path_exists.return_value = False
        mock_path_mkdir.side_effect = PermissionError("Permission denied")

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn",
            "folder_path": "myconn",
            "create_if_missing": True,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed to create directory" in data["error"].lower()

    def test_path_not_writable(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_os_access
    ):
        """Path exists but is not writable → 'not writable' error"""
        mock_path_exists.return_value = True
        mock_os_access.return_value = False

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn",
            "folder_path": "myconn",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not writable" in data["error"].lower()

    def test_add_backup_path_returns_false(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_os_access
    ):
        """Path exists + writable + add_backup_path returns False → 'already exists' error"""
        mock_path_exists.return_value = True
        mock_os_access.return_value = True
        mock_connection_manager.add_backup_path.return_value = False

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn",
            "folder_path": "myconn",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_success(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_os_access
    ):
        """All checks pass → success: True, output contains '✓ Added backup folder'"""
        mock_path_exists.return_value = True
        mock_os_access.return_value = True
        mock_connection_manager.add_backup_path.return_value = True

        response = _post(client, auth_headers, "backup folder add", {
            "connection_name": "test-conn",
            "folder_path": "myconn",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "✓ added backup folder" in data["output"].lower()


# ── backup folder delete ──────────────────────────────────────────────────────

class TestBackupFolderDelete:
    """backup folder delete goes through Path A (special).

    Guard clause tests (confirmation=False, missing connection_name, missing
    folder_path) are already in test_commands.py — NOT duplicated here.
    """

    BASE_PARAMS = {
        "connection_name": "test-conn",
        "folder_path": "/backups_mongodb_manager/test-conn_mongodb_manager",
        "confirmation": True,
    }

    # ── guard clauses after confirmation ─────────────────────────────────────

    def test_connection_not_found(self, client, auth_headers, mock_connection_manager):
        """get_connection returns None → success: False, error mentions 'not found'"""
        mock_connection_manager.get_connection.return_value = None

        response = _post(client, auth_headers, "backup folder delete", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_folder_not_registered_in_connection(
        self, client, auth_headers, mock_connection_manager
    ):
        """folder_path not in connection's backup_paths → 'not registered' error"""
        mock_connection_manager.get_connection.return_value = {
            "name": "test-conn",
            "backup_paths": ["/backups_mongodb_manager/other_mongodb_manager"],
        }

        response = _post(client, auth_headers, "backup folder delete", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not registered" in data["error"].lower()

    def test_remove_backup_path_returns_false(
        self, client, auth_headers, mock_connection_manager
    ):
        """folder registered but remove_backup_path returns False → 'Failed to remove' error"""
        mock_connection_manager.get_connection.return_value = {
            "name": "test-conn",
            "backup_paths": [self.BASE_PARAMS["folder_path"]],
        }
        mock_connection_manager.remove_backup_path.return_value = False

        response = _post(client, auth_headers, "backup folder delete", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed to remove" in data["error"].lower()

    # ── disk deletion branch ──────────────────────────────────────────────────

    def test_rmtree_raises_returns_partial_error(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_shutil_rmtree
    ):
        """Removed from DB but shutil.rmtree raises → partial failure error"""
        mock_connection_manager.get_connection.return_value = {
            "name": "test-conn",
            "backup_paths": [self.BASE_PARAMS["folder_path"]],
        }
        mock_connection_manager.remove_backup_path.return_value = True
        mock_path_exists.return_value = True
        mock_shutil_rmtree.side_effect = OSError("permission denied")

        response = _post(client, auth_headers, "backup folder delete", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed to delete from disk" in data["error"].lower()

    def test_success_path_does_not_exist_on_disk(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_shutil_rmtree
    ):
        """Removed from DB, path doesn't exist on disk → no rmtree, success: True"""
        mock_connection_manager.get_connection.return_value = {
            "name": "test-conn",
            "backup_paths": [self.BASE_PARAMS["folder_path"]],
        }
        mock_connection_manager.remove_backup_path.return_value = True
        mock_path_exists.return_value = False

        response = _post(client, auth_headers, "backup folder delete", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["output"].lower()
        mock_shutil_rmtree.assert_not_called()

    def test_success_path_exists_rmtree_succeeds(
        self, client, auth_headers,
        mock_connection_manager, mock_path_exists, mock_shutil_rmtree
    ):
        """Removed from DB, path exists on disk, rmtree succeeds → success: True"""
        mock_connection_manager.get_connection.return_value = {
            "name": "test-conn",
            "backup_paths": [self.BASE_PARAMS["folder_path"]],
        }
        mock_connection_manager.remove_backup_path.return_value = True
        mock_path_exists.return_value = True
        mock_shutil_rmtree.return_value = None  # no-op success

        response = _post(client, auth_headers, "backup folder delete", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["output"].lower()
        mock_shutil_rmtree.assert_called_once()
