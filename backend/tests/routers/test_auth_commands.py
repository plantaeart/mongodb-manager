"""Integration tests for Authentication commands

Commands covered:
  - auth change-password (Path B — generic CLI fallback, CLI name: "auth change")
  - auth logout          (Path B — generic CLI fallback)

Fixtures used from tests/routers/conftest.py (auto-discovered by pytest):
  - mock_cli_app : patches app.routers.commands.cli_app

Fixtures used from tests/conftest.py:
  - client       : FastAPI TestClient
  - auth_headers : Authorization header with valid JWT

Both commands delegate entirely to cli_app — no special Path A handling in commands.py.
auth change-password calls _auth_manager.prompt_password_change() (interactive prompts),
auth logout calls _auth_manager.logout() then prints a success message.

Response shape (always HTTP 200):
  {"success": bool, "output": str, "error": str | None, "exit_code": int}
"""

import sys


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post(client, auth_headers, command, params=None):
    """Shorthand for posting to /api/commands/execute"""
    return client.post(
        "/api/commands/execute",
        json={"command": command, "params": params or {}},
        headers=auth_headers,
    )


def _make_stdout_writer(text):
    """Return a cli_app side_effect that writes *text* to the redirected stdout"""
    def _side_effect(args, standalone_mode=False):
        sys.stdout.write(text)
    return _side_effect


def _make_exit(code):
    """Return a cli_app side_effect that raises SystemExit with *code*"""
    def _side_effect(args, standalone_mode=False):
        raise SystemExit(code)
    return _side_effect


# ── auth change-password ──────────────────────────────────────────────────────

class TestAuthChangePassword:
    """auth change-password goes through Path B (generic CLI fallback).

    The CLI command name is 'auth change' (typer sub-command).
    Delegates to _auth_manager.prompt_password_change() which uses
    interactive prompts — fully mocked via mock_cli_app.
    """

    def test_success(self, client, auth_headers, mock_cli_app):
        """cli_app writes success message → success: True, output contains 'password'"""
        mock_cli_app.side_effect = _make_stdout_writer(
            "OK Password change initiated\n"
            "Remember: Update your environment variable and restart\n"
        )

        response = _post(client, auth_headers, "auth change-password")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "password" in data["output"].lower()

    def test_password_change_failed(self, client, auth_headers, mock_cli_app):
        """cli_app raises SystemExit(1) → success: False, exit_code: 1"""
        mock_cli_app.side_effect = _make_exit(1)

        response = _post(client, auth_headers, "auth change-password")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["exit_code"] == 1


# ── auth logout ───────────────────────────────────────────────────────────────

class TestAuthLogout:
    """auth logout goes through Path B (generic CLI fallback).

    Delegates to _auth_manager.logout() then prints a confirmation —
    fully mocked via mock_cli_app.
    """

    def test_success(self, client, auth_headers, mock_cli_app):
        """cli_app writes logout confirmation → success: True, output contains 'logged out'"""
        mock_cli_app.side_effect = _make_stdout_writer(
            "OK Logged out successfully\n"
        )

        response = _post(client, auth_headers, "auth logout")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert "logged out" in data["output"].lower()
