"""Workflow integration tests — sequential multi-step API flows

Each test in this module exercises a realistic multi-call sequence that mirrors
what the frontend stepper UI performs: one API call per step, using the result of
the previous call to feed the next one.

Workflows covered:
  1. Connection lifecycle  — add → test → update → remove
  2. Backup folder lifecycle — add folder → list → delete folder
  3. Full backup lifecycle — add connection + folder → create → list → restore → delete
  4. Failure path — add → test fails → remove (cleanup still works)

All external I/O is mocked via the shared fixtures from conftest.py:
  - mock_cli_app            : CLI dispatcher (connect add/remove/test, backup folder list)
  - mock_connection_manager : ConnectionManager (connect update, backup folder add/delete)
  - mock_backup_manager     : BackupManager (backup create/restore)
  - mock_path_exists        : pathlib.Path.exists()
  - mock_os_access          : os.access()
  - mock_shutil_rmtree      : shutil.rmtree()

Each test only activates the fixtures it actually needs — the function signature
documents this dependency at a glance.
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock


# ── Shared helpers ────────────────────────────────────────────────────────────

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


def _assert_ok(response, *, contains=None):
    """Assert HTTP 200 + success=True. Optionally check output substring."""
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True, f"Expected success but got error: {data.get('error')}"
    if contains:
        assert contains in data["output"], (
            f"Expected {contains!r} in output, got: {data['output']!r}"
        )
    return data


def _assert_fail(response, *, error_contains=None):
    """Assert HTTP 200 + success=False. Optionally check error substring."""
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False, f"Expected failure but got success: {data.get('output')}"
    if error_contains:
        assert error_contains in data["error"].lower(), (
            f"Expected {error_contains!r} in error, got: {data['error']!r}"
        )
    return data


# ── Workflow 1: Connection lifecycle ──────────────────────────────────────────

class TestConnectionLifecycle:
    """Simulate the full connection lifecycle:
    add → test → update → remove

    Step 1 — connect add  (Path B, mock_cli_app)
    Step 2 — connect test (Path A, mock_cli_app)
    Step 3 — connect update (Path A, mock_connection_manager)
    Step 4 — connect remove (Path B, mock_cli_app)
    """

    _CONN_NAME = "workflow-conn"
    _TEST_JSON = json.dumps({
        "results": [
            {"name": _CONN_NAME, "success": True, "message": "Connected successfully"}
        ],
        "summary": {"total": 1, "success": 1, "failure": 0},
    })

    def test_add_then_test_then_update_then_remove(
        self,
        client,
        auth_headers,
        mock_cli_app,
        mock_connection_manager,
    ):
        """Full happy path: every step returns success."""

        # ── Step 1: connect add ───────────────────────────────────────────────
        mock_cli_app.side_effect = _make_stdout_writer(
            f"✓ Connection '{self._CONN_NAME}' added successfully\n"
        )
        r1 = _post(client, auth_headers, "connect add", {
            "name": self._CONN_NAME,
            "host": "localhost",
            "port": 27017,
        })
        _assert_ok(r1)

        # ── Step 2: connect test ──────────────────────────────────────────────
        mock_cli_app.side_effect = _make_stdout_writer(self._TEST_JSON)
        r2 = _post(client, auth_headers, "connect test", {
            "connections": [self._CONN_NAME]
        })
        data2 = _assert_ok(r2)
        assert "✓" in data2["output"]
        assert self._CONN_NAME in data2["output"]

        # ── Step 3: connect update ────────────────────────────────────────────
        mock_connection_manager.update_connection.return_value = True
        r3 = _post(client, auth_headers, "connect update", {
            "connection_name": self._CONN_NAME,
            "host": "new-host",
            "port": 27018,
        })
        _assert_ok(r3, contains="updated successfully")

        # ── Step 4: connect remove ────────────────────────────────────────────
        mock_cli_app.side_effect = None
        mock_cli_app.return_value = None  # silent success
        r4 = _post(client, auth_headers, "connect remove", {
            "connections": [self._CONN_NAME]
        })
        _assert_ok(r4)
        assert "1" in r4.json()["output"]

    def test_add_then_update_fails_then_remove_still_succeeds(
        self,
        client,
        auth_headers,
        mock_cli_app,
        mock_connection_manager,
    ):
        """Even if the update step fails, remove (cleanup) still works."""

        # add
        mock_cli_app.side_effect = _make_stdout_writer("✓ Connection added\n")
        _assert_ok(_post(client, auth_headers, "connect add", {
            "name": self._CONN_NAME, "host": "localhost", "port": 27017
        }))

        # update → fails (manager returns False, get_connection returns None = not a duplicate)
        mock_connection_manager.update_connection.return_value = False
        mock_connection_manager.get_connection.return_value = None
        r_fail = _post(client, auth_headers, "connect update", {
            "connection_name": self._CONN_NAME,
            "host": "bad-host",
        })
        _assert_fail(r_fail, error_contains="failed to update")

        # remove — should still succeed
        mock_cli_app.side_effect = None
        mock_cli_app.return_value = None
        _assert_ok(_post(client, auth_headers, "connect remove", {
            "connections": [self._CONN_NAME]
        }))


# ── Workflow 2: Backup folder lifecycle ───────────────────────────────────────

class TestBackupFolderLifecycle:
    """Simulate the backup folder lifecycle:
    add folder → list → delete folder

    Step 1 — backup folder add  (Path A, mock_connection_manager + filesystem mocks)
    Step 2 — backup folder list (Path B, mock_cli_app)
    Step 3 — backup folder delete (Path A, mock_connection_manager + filesystem mocks)
    """

    _CONN_NAME = "workflow-conn"
    _FOLDER_PATH = "/backups_mongodb_manager/workflow-conn_mongodb_manager"

    def test_add_folder_then_list_then_delete(
        self,
        client,
        auth_headers,
        mock_cli_app,
        mock_connection_manager,
        mock_path_exists,
        mock_os_access,
        mock_shutil_rmtree,
    ):
        """Full happy path."""

        # ── Step 1: backup folder add ─────────────────────────────────────────
        mock_path_exists.return_value = True
        mock_os_access.return_value = True
        mock_connection_manager.add_backup_path.return_value = True
        r1 = _post(client, auth_headers, "backup folder add", {
            "connection_name": self._CONN_NAME,
            "folder_path": "workflow-conn",  # raw name — normalized by router
        })
        _assert_ok(r1)

        # ── Step 2: backup folder list ────────────────────────────────────────
        mock_cli_app.side_effect = _make_stdout_writer(
            f"Backup folders for {self._CONN_NAME}:\n  {self._FOLDER_PATH}\n"
        )
        r2 = _post(client, auth_headers, "backup folder list", {
            "connection_name": self._CONN_NAME
        })
        _assert_ok(r2)

        # ── Step 3: backup folder delete ──────────────────────────────────────
        mock_connection_manager.get_connection.return_value = {
            "name": self._CONN_NAME,
            "backup_paths": [self._FOLDER_PATH],
        }
        mock_connection_manager.remove_backup_path.return_value = True
        mock_path_exists.return_value = True
        mock_shutil_rmtree.return_value = None
        r3 = _post(client, auth_headers, "backup folder delete", {
            "connection_name": self._CONN_NAME,
            "folder_path": self._FOLDER_PATH,
            "confirmation": True,
        })
        _assert_ok(r3, contains="deleted successfully")
        mock_shutil_rmtree.assert_called_once()

    def test_add_folder_not_writable_then_fix_and_add_succeeds(
        self,
        client,
        auth_headers,
        mock_connection_manager,
        mock_path_exists,
        mock_os_access,
    ):
        """If first add fails (not writable), correcting permissions and retrying succeeds."""

        # First attempt — path not writable
        mock_path_exists.return_value = True
        mock_os_access.return_value = False
        r1 = _post(client, auth_headers, "backup folder add", {
            "connection_name": self._CONN_NAME,
            "folder_path": "workflow-conn",
        })
        _assert_fail(r1, error_contains="not writable")

        # Second attempt — path is now writable
        mock_os_access.return_value = True
        mock_connection_manager.add_backup_path.return_value = True
        r2 = _post(client, auth_headers, "backup folder add", {
            "connection_name": self._CONN_NAME,
            "folder_path": "workflow-conn",
        })
        _assert_ok(r2)


# ── Workflow 3: Full backup lifecycle ─────────────────────────────────────────

class TestFullBackupLifecycle:
    """Simulate the complete backup lifecycle end-to-end:
    add connection → add folder → create backup → list backups → restore → delete

    This covers the longest realistic user journey and validates that:
    - Data from earlier steps (connection URI, folder paths) is used correctly
      by later steps (backup create, restore).
    - All mocks interact predictably in sequence.
    """

    _CONN_NAME = "lifecycle-conn"
    _BACKUP_NAME = "lifecycle-backup"
    _BACKUP_LOCATION = "/backups/lifecycle-conn-backups"
    _BACKUP_SELECTOR = f"{_BACKUP_LOCATION}|{_BACKUP_NAME}"

    def test_full_lifecycle(
        self,
        client,
        auth_headers,
        mock_cli_app,
        mock_connection_manager,
        mock_backup_manager,
        mock_path_exists,
        mock_os_access,
        mock_shutil_rmtree,
    ):
        """Full happy path through every lifecycle stage."""

        # ── Stage 1: connect add ──────────────────────────────────────────────
        mock_cli_app.side_effect = _make_stdout_writer(
            f"✓ Connection '{self._CONN_NAME}' added successfully\n"
        )
        _assert_ok(_post(client, auth_headers, "connect add", {
            "name": self._CONN_NAME,
            "host": "localhost",
            "port": 27017,
        }))

        # ── Stage 2: backup folder add ────────────────────────────────────────
        mock_path_exists.return_value = True
        mock_os_access.return_value = True
        mock_connection_manager.add_backup_path.return_value = True
        mock_connection_manager.get_connection.return_value = {
            "name": self._CONN_NAME,
            "host": "localhost",
            "port": 27017,
            "username": None,
            "password": None,
            "database": None,
            "auth_source": "admin",
            "description": "",
            "backup_paths": [self._BACKUP_LOCATION],
        }
        _assert_ok(_post(client, auth_headers, "backup folder add", {
            "connection_name": self._CONN_NAME,
            "folder_path": "lifecycle-conn",
        }))

        # ── Stage 3: backup create ────────────────────────────────────────────
        mock_backup_manager.create_backup.return_value = Path(
            f"{self._BACKUP_LOCATION}/{self._BACKUP_NAME}"
        )
        r_create = _post(client, auth_headers, "backup create", {
            "connection_name": self._CONN_NAME,
            "backup_name": self._BACKUP_NAME,
            "backup_location": self._BACKUP_LOCATION,
        })
        _assert_ok(r_create)
        assert self._BACKUP_NAME in r_create.json()["output"]
        mock_backup_manager.create_backup.assert_called_once()

        # ── Stage 4: backup list (via CLI) ────────────────────────────────────
        mock_cli_app.side_effect = _make_stdout_writer(
            f"Backups for {self._CONN_NAME}:\n  {self._BACKUP_NAME}\n"
        )
        r_list = _post(client, auth_headers, "backup list", {
            "connection_name": self._CONN_NAME
        })
        _assert_ok(r_list)

        # ── Stage 5: backup restore ───────────────────────────────────────────
        mock_backup_manager.list_backups.return_value = [
            {
                "name": self._BACKUP_NAME,
                "backup_name": self._BACKUP_NAME,
                "path": Path(f"{self._BACKUP_LOCATION}/{self._BACKUP_NAME}"),
                "connection_name": self._CONN_NAME,
                "timestamp": "20260322_120000",
                "created_at": "2026-03-22T12:00:00",
                "databases": ["testdb"],
                "size": 1024,
            }
        ]
        mock_backup_manager.restore_backup.return_value = None
        r_restore = _post(client, auth_headers, "backup restore", {
            "backup_selector": self._BACKUP_SELECTOR,
            "connection_name": self._CONN_NAME,
            "confirmation": True,
        })
        _assert_ok(r_restore)
        assert self._BACKUP_NAME in r_restore.json()["output"]
        mock_backup_manager.restore_backup.assert_called_once()

        # ── Stage 6: backup folder delete ─────────────────────────────────────
        mock_connection_manager.get_connection.return_value = {
            "name": self._CONN_NAME,
            "backup_paths": [self._BACKUP_LOCATION],
        }
        mock_connection_manager.remove_backup_path.return_value = True
        mock_path_exists.return_value = False  # folder already gone from disk
        r_del_folder = _post(client, auth_headers, "backup folder delete", {
            "connection_name": self._CONN_NAME,
            "folder_path": self._BACKUP_LOCATION,
            "confirmation": True,
        })
        _assert_ok(r_del_folder, contains="deleted successfully")
        # rmtree should NOT be called — path doesn't exist
        mock_shutil_rmtree.assert_not_called()

        # ── Stage 7: connect remove ───────────────────────────────────────────
        mock_cli_app.side_effect = None
        mock_cli_app.return_value = None
        _assert_ok(_post(client, auth_headers, "connect remove", {
            "connections": [self._CONN_NAME]
        }))


# ── Workflow 4: Failure paths ──────────────────────────────────────────────────

class TestFailurePaths:
    """Simulate realistic failure scenarios mid-workflow.

    The key assertion in each case: earlier successful steps don't become
    retroactively invalid, and cleanup operations still work after a failure.
    """

    _CONN_NAME = "fail-conn"

    def test_connect_add_then_test_fails_then_remove_succeeds(
        self,
        client,
        auth_headers,
        mock_cli_app,
    ):
        """add → test fails (connection refused) → remove (cleanup) still works."""

        # add succeeds
        mock_cli_app.side_effect = _make_stdout_writer("✓ Connection added\n")
        _assert_ok(_post(client, auth_headers, "connect add", {
            "name": self._CONN_NAME,
            "host": "localhost",
            "port": 27017,
        }))

        # test fails — CLI writes JSON with success=False
        failed_json = json.dumps({
            "results": [
                {"name": self._CONN_NAME, "success": False, "message": "Connection refused"}
            ],
            "summary": {"total": 1, "success": 0, "failure": 1},
        })
        mock_cli_app.side_effect = _make_stdout_writer(failed_json)
        r_test = _post(client, auth_headers, "connect test", {
            "connections": [self._CONN_NAME]
        })
        # The router still returns success=True (no SystemExit), but output shows ✗
        assert r_test.status_code == 200
        assert "✗" in r_test.json()["output"] or "Connection refused" in r_test.json()["output"]

        # cleanup — remove still works
        mock_cli_app.side_effect = None
        mock_cli_app.return_value = None
        _assert_ok(_post(client, auth_headers, "connect remove", {
            "connections": [self._CONN_NAME]
        }))

    def test_backup_create_fails_then_folder_delete_still_works(
        self,
        client,
        auth_headers,
        mock_connection_manager,
        mock_backup_manager,
        mock_path_exists,
        mock_os_access,
        mock_shutil_rmtree,
    ):
        """Backup creation fails → folder cleanup still succeeds."""
        _FOLDER = "/backups/fail-conn-backups"

        # setup connection
        mock_connection_manager.get_connection.return_value = {
            "name": self._CONN_NAME,
            "host": "localhost",
            "port": 27017,
            "username": None,
            "password": None,
            "database": None,
            "auth_source": "admin",
            "description": "",
            "backup_paths": [_FOLDER],
        }

        # add folder
        mock_path_exists.return_value = True
        mock_os_access.return_value = True
        mock_connection_manager.add_backup_path.return_value = True
        _assert_ok(_post(client, auth_headers, "backup folder add", {
            "connection_name": self._CONN_NAME,
            "folder_path": "fail-conn",
        }))

        # backup create fails
        mock_backup_manager.create_backup.side_effect = Exception("mongodump exited with code 1")
        r_fail = _post(client, auth_headers, "backup create", {
            "connection_name": self._CONN_NAME,
            "backup_name": "doomed-backup",
            "backup_location": _FOLDER,
        })
        _assert_fail(r_fail, error_contains="backup failed")

        # folder delete still works
        mock_connection_manager.get_connection.return_value = {
            "name": self._CONN_NAME,
            "backup_paths": [_FOLDER],
        }
        mock_connection_manager.remove_backup_path.return_value = True
        mock_path_exists.return_value = False  # already cleaned up externally
        r_del = _post(client, auth_headers, "backup folder delete", {
            "connection_name": self._CONN_NAME,
            "folder_path": _FOLDER,
            "confirmation": True,
        })
        _assert_ok(r_del, contains="deleted successfully")
        mock_shutil_rmtree.assert_not_called()

    def test_backup_restore_fails_connection_not_found(
        self,
        client,
        auth_headers,
        mock_connection_manager,
        mock_backup_manager,
    ):
        """Restore fails gracefully when the target connection is not found."""
        _BACKUP_SELECTOR = "/backups/fail-conn-backups|some-backup"

        mock_backup_manager.list_backups.return_value = [
            {
                "name": "some-backup",
                "backup_name": "some-backup",
                "path": Path("/backups/fail-conn-backups/some-backup"),
                "connection_name": self._CONN_NAME,
                "timestamp": "20260322_120000",
                "created_at": "2026-03-22T12:00:00",
                "databases": ["testdb"],
                "size": 512,
            }
        ]
        mock_connection_manager.get_connection.return_value = None  # target connection gone

        r = _post(client, auth_headers, "backup restore", {
            "backup_selector": _BACKUP_SELECTOR,
            "connection_name": "gone-conn",
            "confirmation": True,
        })
        _assert_fail(r, error_contains="not found")

    def test_invalid_port_mid_workflow_does_not_crash_server(
        self,
        client,
        auth_headers,
        mock_connection_manager,
    ):
        """A malformed port in an update call returns a clean error, not a 500."""
        r = _post(client, auth_headers, "connect update", {
            "connection_name": self._CONN_NAME,
            "port": "not-a-number",
        })
        assert r.status_code == 200
        _assert_fail(r, error_contains="invalid port value")
