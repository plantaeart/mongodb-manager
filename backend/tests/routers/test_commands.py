"""Integration tests for /api/commands/execute endpoint"""

import pytest


class TestCommandsExecuteEndpoint:
    """HTTP integration tests for the commands execute endpoint"""

    # ── Sanity / auth ───────────────────────────────────────────────────────

    def test_health_check_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_execute_without_auth_returns_401(self, client):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect list", "params": {}}
        )
        assert response.status_code == 401

    def test_execute_with_invalid_token_returns_401(self, client):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect list", "params": {}},
            headers={"Authorization": "Bearer invalid.token.value"}
        )
        assert response.status_code == 401

    # ── connect list ────────────────────────────────────────────────────────

    def test_connect_list_with_auth_returns_200(self, client, auth_headers):
        """connect list should always succeed (even with empty list)"""
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect list", "params": {}},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_connect_list_response_has_expected_shape(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect list", "params": {}},
            headers=auth_headers
        )
        data = response.json()
        assert "success" in data
        assert "output" in data
        assert "exit_code" in data

    # ── connect remove — empty selection ────────────────────────────────────

    def test_connect_remove_empty_connections_returns_error(self, client, auth_headers):
        """Sending an empty connections list should return success=False"""
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect remove", "params": {"connections": []}},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "No connections selected"

    # ── backup folder delete — no confirmation ──────────────────────────────

    def test_backup_folder_delete_without_confirmation_returns_error(self, client, auth_headers):
        """Omitting confirmation flag should return a clear error message"""
        response = client.post(
            "/api/commands/execute",
            json={
                "command": "backup folder delete",
                "params": {
                    "connection_name": "test-conn",
                    "folder_path": "/backups/test",
                    "confirmation": False
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "confirm" in data["error"].lower()

    def test_backup_folder_delete_missing_connection_name_returns_error(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={
                "command": "backup folder delete",
                "params": {
                    "folder_path": "/backups/test",
                    "confirmation": True
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "connection" in data["error"].lower()

    def test_backup_folder_delete_missing_folder_path_returns_error(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={
                "command": "backup folder delete",
                "params": {
                    "connection_name": "test-conn",
                    "confirmation": True
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "folder" in data["error"].lower() or "path" in data["error"].lower()

    # ── connect test — empty selection ──────────────────────────────────────

    def test_connect_test_empty_connections_returns_error(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect test", "params": {"connections": []}},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "No connections selected"

    # ── connect update — no connection selected ──────────────────────────────

    def test_connect_update_without_connection_name_returns_error(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect update", "params": {"host": "localhost"}},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "connection" in data["error"].lower()

    # ── backup create — missing required fields ──────────────────────────────

    def test_backup_create_without_connection_name_returns_error(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={
                "command": "backup create",
                "params": {
                    "backup_name": "my-backup",
                    "backup_location": "/backups/test"
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "connection" in data["error"].lower()

    def test_backup_restore_without_confirmation_returns_error(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={
                "command": "backup restore",
                "params": {
                    "backup_selector": "folder|backup-name",
                    "connection_name": "test-conn",
                    "confirmation": False
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "confirm" in data["error"].lower()
