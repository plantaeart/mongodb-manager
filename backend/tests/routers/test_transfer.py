"""Integration tests for Transfer router endpoints

Endpoints covered:
  - GET  /api/transfer/backup/export/options
  - GET  /api/transfer/backup/import/options
  - GET  /api/transfer/backup/export?backup_selector=...
  - POST /api/transfer/backup/import
  - GET  /api/transfer/connect/export
  - POST /api/transfer/connect/import

Fixtures used from tests/conftest.py (auto-discovered):
  - client       : FastAPI TestClient
  - auth_headers : Authorization header with valid JWT

All manager classes are mocked so no real filesystem or MongoDB access occurs.
"""

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch



# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_zip_bytes(backup_name: str = "my-backup") -> bytes:
    """Build a minimal valid ZIP containing one top-level folder + metadata.json."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{backup_name}/metadata.json", json.dumps({"name": backup_name}))
        zf.writestr(f"{backup_name}/testdb/collection.bson", b"data")
    return buf.getvalue()


def _make_connections_json(connections: list[dict] | None = None) -> bytes:
    """Build a valid connections JSON payload."""
    if connections is None:
        connections = [
            {
                "name": "test-conn",
                "host": "localhost",
                "port": 27017,
                "username": None,
                "database": None,
                "auth_source": "admin",
                "description": "Test",
                "backup_paths": [],
            }
        ]
    return json.dumps({"connections": connections}).encode("utf-8")


SAMPLE_CONNECTIONS = [
    {
        "name": "conn-a",
        "host": "localhost",
        "port": 27017,
        "username": None,
        "password": None,
        "database": None,
        "auth_source": "admin",
        "description": "",
        "backup_paths": ["/backups/conn-a"],
    }
]

SAMPLE_BACKUPS = [
    {
        "backup_name": "my-backup",
        "folder_path": "/backups/conn-a",
        "connection_name": "conn-a",
        "created_at": "2026-03-22T12:00:00",
    }
]


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/transfer/backup/export/options
# ─────────────────────────────────────────────────────────────────────────────

class TestBackupExportOptions:

    def test_returns_backups_list(self, client, auth_headers):
        """Should return a list of backup options with value/label/description."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM, \
             patch("app.routers.transfer.collect_all_backups", return_value=SAMPLE_BACKUPS):

            MockCM.return_value.list_connections.return_value = SAMPLE_CONNECTIONS

            response = client.get(
                "/api/transfer/backup/export/options",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "backups" in data
        assert len(data["backups"]) == 1
        opt = data["backups"][0]
        assert opt["value"] == "/backups/conn-a|my-backup"
        assert "my-backup" in opt["label"]
        assert "description" in opt

    def test_empty_when_no_backups(self, client, auth_headers):
        """No backups available → empty list."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM, \
             patch("app.routers.transfer.collect_all_backups", return_value=[]):

            MockCM.return_value.list_connections.return_value = []

            response = client.get(
                "/api/transfer/backup/export/options",
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert response.json()["backups"] == []

    def test_requires_auth(self, client):
        """Unauthenticated request → 401."""
        response = client.get("/api/transfer/backup/export/options")
        assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/transfer/backup/import/options
# ─────────────────────────────────────────────────────────────────────────────

class TestBackupImportOptions:

    def test_returns_deduplicated_folders(self, client, auth_headers):
        """All backup_paths across connections, deduplicated and sorted."""
        connections = [
            {"name": "a", "backup_paths": ["/backups/b", "/backups/a"]},
            {"name": "b", "backup_paths": ["/backups/a"]},  # duplicate
        ]
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.list_connections.return_value = connections

            response = client.get(
                "/api/transfer/backup/import/options",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "folders" in data
        # "/backups/a" appears twice in source but should be deduplicated
        values = [f["value"] for f in data["folders"]]
        assert values == sorted(set(values))
        assert len(values) == 2

    def test_requires_auth(self, client):
        response = client.get("/api/transfer/backup/import/options")
        assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/transfer/backup/export
# ─────────────────────────────────────────────────────────────────────────────

class TestBackupExport:

    def test_success_streams_zip(self, client, auth_headers):
        """Valid backup_selector → 200, ZIP content-type, correct filename."""
        zip_bytes = _make_zip_bytes("my-backup")

        with patch("app.routers.transfer.BackupManager") as MockBM, \
             patch("app.routers.transfer.parse_backup_selector",
                   return_value=("/backups/conn-a", "my-backup")):

            MockBM.return_value.export_backup_zip.return_value = zip_bytes

            response = client.get(
                "/api/transfer/backup/export",
                params={"backup_selector": "/backups/conn-a|my-backup"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert 'filename="my-backup.zip"' in response.headers["content-disposition"]
        # Verify it's actually a valid ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            assert any(n.startswith("my-backup/") for n in zf.namelist())

    def test_invalid_selector_format_returns_400(self, client, auth_headers):
        """parse_backup_selector raises ValueError → 400."""
        with patch("app.routers.transfer.parse_backup_selector",
                   side_effect=ValueError("bad format")):

            response = client.get(
                "/api/transfer/backup/export",
                params={"backup_selector": "no-pipe"},
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert "Invalid backup_selector format" in response.json()["detail"]

    def test_backup_not_found_returns_404(self, client, auth_headers):
        """export_backup_zip raises ValueError (not found) → 404."""
        with patch("app.routers.transfer.BackupManager") as MockBM, \
             patch("app.routers.transfer.parse_backup_selector",
                   return_value=("/backups/conn-a", "ghost-backup")):

            MockBM.return_value.export_backup_zip.side_effect = ValueError(
                "Backup 'ghost-backup' not found"
            )

            response = client.get(
                "/api/transfer/backup/export",
                params={"backup_selector": "/backups/conn-a|ghost-backup"},
                headers=auth_headers,
            )

        assert response.status_code == 404

    def test_unexpected_error_returns_500(self, client, auth_headers):
        """export_backup_zip raises Exception → 500."""
        with patch("app.routers.transfer.BackupManager") as MockBM, \
             patch("app.routers.transfer.parse_backup_selector",
                   return_value=("/backups/conn-a", "my-backup")):

            MockBM.return_value.export_backup_zip.side_effect = OSError("disk error")

            response = client.get(
                "/api/transfer/backup/export",
                params={"backup_selector": "/backups/conn-a|my-backup"},
                headers=auth_headers,
            )

        assert response.status_code == 500

    def test_requires_auth(self, client):
        response = client.get(
            "/api/transfer/backup/export",
            params={"backup_selector": "/backups/conn-a|my-backup"},
        )
        assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/transfer/backup/import
# ─────────────────────────────────────────────────────────────────────────────

class TestBackupImport:

    VALID_FOLDER = "/backups/conn-a"

    def _post(self, client, auth_headers, zip_bytes: bytes, folder_path: str, overwrite: bool = False):
        return client.post(
            "/api/transfer/backup/import",
            files={"file": ("backup.zip", io.BytesIO(zip_bytes), "application/zip")},
            data={"folder_path": folder_path, "overwrite": str(overwrite).lower()},
            headers=auth_headers,
        )

    def _mock_conn_mgr(self, folder_path: str = VALID_FOLDER):
        """Return a ConnectionManager mock that reports folder_path as registered."""
        mock = MagicMock()
        mock.return_value.list_connections.return_value = [
            {"name": "conn-a", "backup_paths": [folder_path]}
        ]
        return mock

    def test_success(self, client, auth_headers):
        """Valid ZIP + registered folder → 200, success: True."""
        zip_bytes = _make_zip_bytes("my-backup")

        with patch("app.routers.transfer.ConnectionManager", self._mock_conn_mgr()), \
             patch("app.routers.transfer.BackupManager") as MockBM:

            MockBM.return_value.import_backup_zip.return_value = "my-backup"

            response = self._post(client, auth_headers, zip_bytes, self.VALID_FOLDER)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["backup_name"] == "my-backup"
        assert "my-backup" in data["message"]

    def test_unregistered_folder_returns_400(self, client, auth_headers):
        """folder_path not in registered paths → 400."""
        with patch("app.routers.transfer.ConnectionManager", self._mock_conn_mgr()):
            response = self._post(
                client, auth_headers, _make_zip_bytes(), "/backups/unknown"
            )

        assert response.status_code == 400
        assert "not a registered backup folder" in response.json()["detail"]

    def test_invalid_zip_returns_400(self, client, auth_headers):
        """import_backup_zip raises ValueError (bad ZIP) → 400."""
        with patch("app.routers.transfer.ConnectionManager", self._mock_conn_mgr()), \
             patch("app.routers.transfer.BackupManager") as MockBM:

            MockBM.return_value.import_backup_zip.side_effect = ValueError(
                "Uploaded file is not a valid ZIP archive"
            )

            response = self._post(
                client, auth_headers, b"not-a-zip", self.VALID_FOLDER
            )

        assert response.status_code == 400

    def test_already_exists_no_overwrite_returns_400(self, client, auth_headers):
        """import_backup_zip raises ValueError (exists, no overwrite) → 400."""
        with patch("app.routers.transfer.ConnectionManager", self._mock_conn_mgr()), \
             patch("app.routers.transfer.BackupManager") as MockBM:

            MockBM.return_value.import_backup_zip.side_effect = ValueError(
                "Backup 'my-backup' already exists."
            )

            response = self._post(
                client, auth_headers, _make_zip_bytes(), self.VALID_FOLDER, overwrite=False
            )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_overwrite_flag_passed_to_manager(self, client, auth_headers):
        """overwrite=true is forwarded to import_backup_zip."""
        zip_bytes = _make_zip_bytes("my-backup")

        with patch("app.routers.transfer.ConnectionManager", self._mock_conn_mgr()), \
             patch("app.routers.transfer.BackupManager") as MockBM:

            MockBM.return_value.import_backup_zip.return_value = "my-backup"

            self._post(client, auth_headers, zip_bytes, self.VALID_FOLDER, overwrite=True)

            MockBM.return_value.import_backup_zip.assert_called_once_with(
                zip_bytes, overwrite=True
            )

    def test_unexpected_error_returns_500(self, client, auth_headers):
        """Unexpected exception from import_backup_zip → 500."""
        with patch("app.routers.transfer.ConnectionManager", self._mock_conn_mgr()), \
             patch("app.routers.transfer.BackupManager") as MockBM:

            MockBM.return_value.import_backup_zip.side_effect = OSError("disk full")

            response = self._post(
                client, auth_headers, _make_zip_bytes(), self.VALID_FOLDER
            )

        assert response.status_code == 500

    def test_requires_auth(self, client):
        response = client.post(
            "/api/transfer/backup/import",
            files={"file": ("backup.zip", io.BytesIO(b"data"), "application/zip")},
            data={"folder_path": self.VALID_FOLDER},
        )
        assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/transfer/connect/export
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectExport:

    def test_success_streams_json(self, client, auth_headers):
        """Connections exist → 200, JSON content-type, passwords stripped."""
        exported = [
            {
                "name": "conn-a",
                "host": "localhost",
                "port": 27017,
                "backup_paths": [],
            }
        ]
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.export_connections.return_value = exported

            response = client.get(
                "/api/transfer/connect/export",
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert 'filename="connections.json"' in response.headers["content-disposition"]

        payload = response.json()
        assert "connections" in payload
        assert payload["connections"][0]["name"] == "conn-a"
        # No password field should be present (stripped at manager level)
        assert "password" not in payload["connections"][0]

    def test_export_connections_exception_returns_500(self, client, auth_headers):
        """export_connections raises Exception → 500."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.export_connections.side_effect = Exception("db error")

            response = client.get(
                "/api/transfer/connect/export",
                headers=auth_headers,
            )

        assert response.status_code == 500

    def test_requires_auth(self, client):
        response = client.get("/api/transfer/connect/export")
        assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/transfer/connect/import
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectImport:

    def _post(
        self,
        client,
        auth_headers,
        json_bytes: bytes,
        overwrite: bool = False,
        import_backup_paths: bool = False,
    ):
        return client.post(
            "/api/transfer/connect/import",
            files={"file": ("connections.json", io.BytesIO(json_bytes), "application/json")},
            data={
                "overwrite": str(overwrite).lower(),
                "import_backup_paths": str(import_backup_paths).lower(),
            },
            headers=auth_headers,
        )

    def test_success_imported(self, client, auth_headers):
        """Valid file, new connections → success: True, imported count."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.import_connections.return_value = {
                "imported": 1,
                "overwritten": 0,
                "skipped": 0,
                "errors": [],
            }

            response = self._post(client, auth_headers, _make_connections_json())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported"] == 1
        assert "1 imported" in data["message"]

    def test_success_overwritten(self, client, auth_headers):
        """Overwrite=true, connection already exists → overwritten count in message."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.import_connections.return_value = {
                "imported": 0,
                "overwritten": 1,
                "skipped": 0,
                "errors": [],
            }

            response = self._post(
                client, auth_headers, _make_connections_json(), overwrite=True
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "1 overwritten" in data["message"]

    def test_success_skipped(self, client, auth_headers):
        """Duplicate, overwrite=false → skipped count in message."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.import_connections.return_value = {
                "imported": 0,
                "overwritten": 0,
                "skipped": 1,
                "errors": [],
            }

            response = self._post(client, auth_headers, _make_connections_json())

        assert response.status_code == 200
        data = response.json()
        assert "1 skipped" in data["message"]

    def test_empty_connections_array_no_manager_call(self, client, auth_headers):
        """Empty 'connections' array → 200 immediately, no manager call needed."""
        payload = json.dumps({"connections": []}).encode("utf-8")

        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            response = self._post(client, auth_headers, payload)

            MockCM.return_value.import_connections.assert_not_called()

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported"] == 0

    def test_invalid_json_returns_400(self, client, auth_headers):
        """Non-JSON bytes → 400."""
        response = self._post(client, auth_headers, b"this is not json")
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    def test_missing_connections_key_returns_400(self, client, auth_headers):
        """JSON without 'connections' array → 400."""
        bad_payload = json.dumps({"data": []}).encode("utf-8")
        response = self._post(client, auth_headers, bad_payload)
        assert response.status_code == 400
        assert "connections" in response.json()["detail"]

    def test_import_backup_paths_flag_forwarded(self, client, auth_headers):
        """import_backup_paths=true is forwarded to import_connections."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.import_connections.return_value = {
                "imported": 1,
                "overwritten": 0,
                "skipped": 0,
                "errors": [],
            }

            self._post(
                client, auth_headers, _make_connections_json(), import_backup_paths=True
            )

            call_kwargs = MockCM.return_value.import_connections.call_args
            assert call_kwargs.kwargs["overwrite"] is False
            assert call_kwargs.kwargs["import_backup_paths"] is True
            assert isinstance(call_kwargs.kwargs["connections"], list)

    def test_errors_in_result_reflected_in_message(self, client, auth_headers):
        """Per-connection errors reported in message suffix."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.import_connections.return_value = {
                "imported": 1,
                "overwritten": 0,
                "skipped": 0,
                "errors": ["Error importing 'bad': field missing"],
            }

            response = self._post(client, auth_headers, _make_connections_json())

        assert response.status_code == 200
        data = response.json()
        assert "1 error" in data["message"]
        assert len(data["errors"]) == 1

    def test_unexpected_exception_returns_500(self, client, auth_headers):
        """import_connections raises Exception → 500."""
        with patch("app.routers.transfer.ConnectionManager") as MockCM:
            MockCM.return_value.import_connections.side_effect = Exception("crash")

            response = self._post(client, auth_headers, _make_connections_json())

        assert response.status_code == 500

    def test_requires_auth(self, client):
        response = client.post(
            "/api/transfer/connect/import",
            files={"file": ("connections.json", io.BytesIO(b"{}"), "application/json")},
            data={"overwrite": "false", "import_backup_paths": "false"},
        )
        assert response.status_code == 401
