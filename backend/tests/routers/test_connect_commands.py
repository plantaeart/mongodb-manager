"""Integration tests for Connection Management commands

Commands covered:
  - connect add    (Path B — generic CLI fallback)
  - connect remove (Path A — special, loops per connection)
  - connect test   (Path A — special, JSON output)
  - connect update (Path A — special, direct ConnectionManager call)

Fixtures used from tests/routers/conftest.py (auto-discovered by pytest):
  - mock_cli_app            : patches app.routers.commands.cli_app
  - mock_connection_manager : patches app.routers.commands.ConnectionManager

Fixtures used from tests/conftest.py:
  - client       : FastAPI TestClient
  - auth_headers : Authorization header with valid JWT
"""

import sys
import json
import pytest


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


# ── connect add ───────────────────────────────────────────────────────────────

class TestConnectAdd:
    """connect add goes through Path B (generic CLI fallback).

    The router pre-processes the port value before forwarding to cli_app,
    so we only need to verify the HTTP response — not the internal CLI args.
    """

    BASE_PARAMS = {"name": "my-conn", "host": "localhost", "port": 27017}

    def test_success(self, client, auth_headers, mock_cli_app):
        """Valid params with cli_app succeeding → success: True"""
        mock_cli_app.side_effect = _make_stdout_writer("✓ Connection 'my-conn' added successfully\n")

        response = _post(client, auth_headers, "connect add", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0

    def test_port_string_coerced_to_int(self, client, auth_headers, mock_cli_app):
        """Port given as a numeric string → coerced to int, no crash"""
        mock_cli_app.side_effect = _make_stdout_writer("✓ Connection added\n")

        response = _post(client, auth_headers, "connect add", {**self.BASE_PARAMS, "port": "5432"})

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_port_empty_string_defaults_to_27017(self, client, auth_headers, mock_cli_app):
        """Empty-string port → silently replaced with 27017, no crash"""
        mock_cli_app.side_effect = _make_stdout_writer("✓ Connection added\n")

        response = _post(client, auth_headers, "connect add", {**self.BASE_PARAMS, "port": ""})

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_port_none_defaults_to_27017(self, client, auth_headers, mock_cli_app):
        """None port → silently replaced with 27017, no crash"""
        mock_cli_app.side_effect = _make_stdout_writer("✓ Connection added\n")

        response = _post(client, auth_headers, "connect add", {**self.BASE_PARAMS, "port": None})

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_internal_mode_param_excluded_from_cli(self, client, auth_headers, mock_cli_app):
        """_mode (internal param) must NOT be forwarded as --mode to the CLI"""
        captured_args = []

        def _capture(args, standalone_mode=False):
            captured_args.extend(args)
            sys.stdout.write("✓ ok\n")

        mock_cli_app.side_effect = _capture

        response = _post(client, auth_headers, "connect add", {
            "name": "my-conn",
            "host": "localhost",
            "_mode": "advanced",
        })

        assert response.status_code == 200
        assert "--mode" not in captured_args
        assert "_mode" not in captured_args


# ── connect remove ────────────────────────────────────────────────────────────

class TestConnectRemove:
    """connect remove goes through Path A (special loop).

    cli_app is called once per connection name with --yes.
    """

    def test_single_connection_success(self, client, auth_headers, mock_cli_app):
        """One valid connection → success: True, summary mentions 1 removed"""
        mock_cli_app.return_value = None  # silent success, exit 0

        response = _post(client, auth_headers, "connect remove", {"connections": ["my-conn"]})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "1" in data["output"]
        mock_cli_app.assert_called_once()

    def test_multiple_connections_success(self, client, auth_headers, mock_cli_app):
        """Two valid connections → success: True, summary mentions 2 removed"""
        mock_cli_app.return_value = None

        response = _post(client, auth_headers, "connect remove", {"connections": ["conn-a", "conn-b"]})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "2" in data["output"]
        assert mock_cli_app.call_count == 2

    def test_non_list_string_coerced_to_single_item(self, client, auth_headers, mock_cli_app):
        """connections given as a bare string → treated as [string], cli_app called once"""
        mock_cli_app.return_value = None

        response = _post(client, auth_headers, "connect remove", {"connections": "single-conn"})

        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_cli_app.assert_called_once()


# ── connect test ──────────────────────────────────────────────────────────────

class TestConnectTest:
    """connect test goes through Path A (special).

    cli_app is called with --json; the router parses the JSON and formats output.
    """

    _VALID_JSON = json.dumps({
        "results": [
            {"name": "conn-a", "success": True, "message": "Connected successfully"}
        ],
        "summary": {"total": 1, "success": 1, "failure": 0}
    })

    def test_success_with_valid_json_output(self, client, auth_headers, mock_cli_app):
        """cli_app writes valid JSON → formatted output contains ✓ and connection name"""
        mock_cli_app.side_effect = _make_stdout_writer(self._VALID_JSON)

        response = _post(client, auth_headers, "connect test", {"connections": ["conn-a"]})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "✓" in data["output"]
        assert "conn-a" in data["output"]

    def test_json_parse_fallback_on_bad_output(self, client, auth_headers, mock_cli_app):
        """cli_app writes non-JSON → router falls back to raw output, still success: True"""
        mock_cli_app.side_effect = _make_stdout_writer("plain text output, not json")

        response = _post(client, auth_headers, "connect test", {"connections": ["conn-a"]})

        assert response.status_code == 200
        data = response.json()
        # exit_code is 0 (no SystemExit raised), so success must be True
        assert data["success"] is True
        assert "plain text output, not json" in data["output"]


# ── connect update ────────────────────────────────────────────────────────────

class TestConnectUpdate:
    """connect update goes through Path A (special).

    ConnectionManager.update_connection() is called directly — no CLI involved.
    """

    BASE_PARAMS = {"connection_name": "my-conn", "host": "new-host"}

    def test_success(self, client, auth_headers, mock_connection_manager):
        """update_connection returns True → success: True, output confirms update"""
        response = _post(client, auth_headers, "connect update", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated successfully" in data["output"].lower()

    def test_connection_name_as_list_uses_first_element(self, client, auth_headers, mock_connection_manager):
        """connection_name given as a list → first element is used"""
        response = _post(client, auth_headers, "connect update", {
            "connection_name": ["my-conn", "other-conn"],
            "host": "new-host",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Verify update_connection was called with the first name
        call_kwargs = mock_connection_manager.update_connection.call_args.kwargs
        assert call_kwargs["name"] == "my-conn"

    def test_update_returns_false_gives_generic_error(self, client, auth_headers, mock_connection_manager):
        """update_connection returns False, no duplicate → generic failure message"""
        mock_connection_manager.update_connection.return_value = False
        mock_connection_manager.get_connection.return_value = None  # no duplicate

        response = _post(client, auth_headers, "connect update", self.BASE_PARAMS)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed to update" in data["error"].lower()

    def test_update_fails_duplicate_name_detected(self, client, auth_headers, mock_connection_manager):
        """update_connection returns False and new name already exists → 'already exists' error"""
        mock_connection_manager.update_connection.return_value = False
        # get_connection returns a hit for the new name → duplicate detected
        mock_connection_manager.get_connection.return_value = {"name": "new-conn"}

        response = _post(client, auth_headers, "connect update", {
            "connection_name": "my-conn",
            "name": "new-conn",  # trying to rename to an existing name
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_invalid_port_gives_error(self, client, auth_headers, mock_connection_manager):
        """Non-numeric port value → success: False with 'Invalid port value' message.

        Previously the shared pre-processor at commands.py:90-104 called int()
        without a try/except, crashing before the connect update branch was reached.
        The fix wraps that int() call so the endpoint returns a clean error response.
        """
        response = _post(client, auth_headers, "connect update", {
            "connection_name": "my-conn",
            "port": "not-a-number",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "invalid port value" in data["error"].lower()
