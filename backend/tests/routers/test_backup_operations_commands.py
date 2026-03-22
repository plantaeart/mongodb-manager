"""Integration tests for Backup Create & Restore commands

Commands covered:
  - backup create  (Path A — special, direct ConnectionManager + BackupManager)
  - backup restore (Path A — special, direct BackupManager + ConnectionManager)

Already covered in test_commands.py (NOT duplicated here):
  - backup restore — confirmation: False
  - backup create  — missing connection_name (guard clause)

Fixtures used from tests/routers/conftest.py (auto-discovered by pytest):
  - mock_connection_manager : patches app.core.connection_ops.ConnectionManager
  - mock_backup_manager     : patches app.core.backup_ops.BackupManager

Fixtures used from tests/conftest.py:
  - client       : FastAPI TestClient
  - auth_headers : Authorization header with valid JWT

Key patch targets (local-import pattern — both are imported inside the handler branch):
  - ConnectionManager → app.core.connection_ops.ConnectionManager
  - BackupManager     → app.core.backup_ops.BackupManager

Response shape (always HTTP 200):
  {"success": bool, "output": str, "error": str | None, "exit_code": int}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post(client, auth_headers, command, params):
    """Shorthand for posting to /api/commands/execute"""
    return client.post(
        "/api/commands/execute",
        json={"command": command, "params": params},
        headers=auth_headers,
    )


# ── backup create ─────────────────────────────────────────────────────────────

class TestBackupCreate:
    """backup create goes through Path A (special).

    Uses ConnectionManager to look up the connection and validate backup_location,
    then delegates to BackupManager.create_backup().

    Guard clauses already tested in test_commands.py:
      - missing connection_name
    """

    BASE_PARAMS = {
        "connection_name": "test-conn",
        "backup_name": "my-backup",
        "backup_location": "/backups/test-conn-backups",
    }

    # ── guard clauses ─────────────────────────────────────────────────────────

    def test_missing_backup_name(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """No backup_name → success: False, error mentions 'backup name'"""
        response = _post(client, auth_headers, "backup create", {
            "connection_name": "test-conn",
            "backup_location": "/backups/test-conn-backups",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "backup name" in data["error"].lower()

    def test_missing_backup_location(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """No backup_location → success: False, error mentions 'backup location'"""
        response = _post(client, auth_headers, "backup create", {
            "connection_name": "test-conn",
            "backup_name": "my-backup",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "backup location" in data["error"].lower()

    def test_connection_not_found(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """get_connection returns None → success: False, error mentions 'not found'"""
        mock_connection_manager.get_connection.return_value = None

        response = _post(client, auth_headers, "backup create", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_backup_location_not_in_connection_paths(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """backup_location not in connection.backup_paths → 'Invalid backup location' error"""
        # The mock connection has backup_paths=["/backups/test-conn-backups"]
        # Use a location that is NOT in that list
        response = _post(client, auth_headers, "backup create", {
            "connection_name": "test-conn",
            "backup_name": "my-backup",
            "backup_location": "/backups/some-other-location",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "invalid backup location" in data["error"].lower()

    # ── BackupManager exception branches ──────────────────────────────────────

    def test_create_backup_raises_value_error_duplicate_name(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """BackupManager.create_backup raises ValueError → error = str(e), no 'Backup failed:' prefix"""
        mock_backup_manager.create_backup.side_effect = ValueError(
            "Backup 'my-backup' already exists in /backups/test-conn-backups"
        )

        response = _post(client, auth_headers, "backup create", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        # ValueError is returned as-is (no "Backup failed:" prefix)
        assert "already exists" in data["error"].lower()
        assert not data["error"].startswith("Backup failed:")

    def test_create_backup_raises_generic_exception(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """BackupManager.create_backup raises Exception → error prefixed with 'Backup failed:'"""
        mock_backup_manager.create_backup.side_effect = Exception("mongodump exited with code 1")

        response = _post(client, auth_headers, "backup create", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"].startswith("Backup failed:")
        assert "mongodump" in data["error"]

    # ── success path ──────────────────────────────────────────────────────────

    def test_success(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """All checks pass + create_backup succeeds → success: True, output contains backup name"""
        response = _post(client, auth_headers, "backup create", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "my-backup" in data["output"]
        assert "✓" in data["output"]
        # Verify BackupManager was called with the right args
        mock_backup_manager.create_backup.assert_called_once_with(
            "mongodb://localhost:27017",
            "test-conn",
            "my-backup",
        )


# ── backup restore ────────────────────────────────────────────────────────────

class TestBackupRestore:
    """backup restore goes through Path A (special).

    Parses a composite backup_selector (folder_path|backup_name), looks up the
    backup via BackupManager.list_backups(), looks up the connection via
    ConnectionManager, then calls BackupManager.restore_backup().

    Guard clauses already tested in test_commands.py:
      - confirmation: False
    """

    BASE_PARAMS = {
        "backup_selector": "/backups/test-conn-backups|my-backup",
        "connection_name": "test-conn",
        "confirmation": True,
    }

    # ── guard clauses ─────────────────────────────────────────────────────────

    def test_missing_backup_selector(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """No backup_selector → success: False, error mentions 'backup selector'"""
        response = _post(client, auth_headers, "backup restore", {
            "connection_name": "test-conn",
            "confirmation": True,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "backup selector" in data["error"].lower()

    def test_missing_connection_name(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """No connection_name → success: False, error mentions 'connection name'"""
        response = _post(client, auth_headers, "backup restore", {
            "backup_selector": "/backups/test-conn-backups|my-backup",
            "confirmation": True,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "connection name" in data["error"].lower()

    def test_invalid_backup_selector_format_no_pipe(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """backup_selector without '|' → 'Invalid backup selector format' error"""
        response = _post(client, auth_headers, "backup restore", {
            "backup_selector": "no-pipe-here",
            "connection_name": "test-conn",
            "confirmation": True,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "invalid backup selector format" in data["error"].lower()

    def test_backup_not_found_in_list(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """list_backups returns empty list → 'Backup not found' error"""
        mock_backup_manager.list_backups.return_value = []

        response = _post(client, auth_headers, "backup restore", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_connection_not_found(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """Backup found but get_connection returns None → 'Connection not found' error"""
        mock_connection_manager.get_connection.return_value = None

        response = _post(client, auth_headers, "backup restore", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    # ── restore_backup exception branch ───────────────────────────────────────

    def test_restore_backup_raises_exception(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """restore_backup raises Exception → error prefixed with 'Restore failed:'"""
        mock_backup_manager.restore_backup.side_effect = Exception(
            "mongorestore exited with code 1"
        )

        response = _post(client, auth_headers, "backup restore", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"].startswith("Restore failed:")
        assert "mongorestore" in data["error"]

    # ── success paths ─────────────────────────────────────────────────────────

    def test_success_without_drop(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """All checks pass, drop_collections=False → success: True, no '--drop flag' in output"""
        response = _post(client, auth_headers, "backup restore", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "my-backup" in data["output"]
        assert "✓" in data["output"]
        assert "--drop flag" not in data["output"]

    def test_success_with_drop(
        self, client, auth_headers, mock_connection_manager, mock_backup_manager
    ):
        """drop_collections=True → success: True, output mentions '--drop flag'"""
        response = _post(client, auth_headers, "backup restore", {
            **self.BASE_PARAMS,
            "drop_collections": True,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "--drop flag" in data["output"]
