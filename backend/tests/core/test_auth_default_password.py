"""Tests for AuthManager default-password reconciliation against NUXT_ADMIN_PASSWORD.

Spec: on every backend startup (CLI import + FastAPI app boot),
AuthManager must reconcile the admin row with the NUXT_ADMIN_PASSWORD env var:

  1. If no admin exists, seed it with the env password.
  2. If the env password is set and the stored admin hash differs, overwrite
     the stored hash with a fresh bcrypt of the env value.
  3. If the env password is unset/empty, leave any existing admin untouched
     (do not lock the user out).
  4. Idempotent: when hashes already match, no Mongo write happens.
"""

from unittest.mock import MagicMock, patch

from app.core.auth import AuthManager
from app.core.utils import get_current_time

ADMIN = AuthManager.DEFAULT_USERNAME


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_auth_manager(users_data=None, count=1):
    """Build an AuthManager whose users_collection is preloaded.

    Returns (auth_manager, users_collection_mock)."""
    fake_user = {
        "username": ADMIN,
        "password_hash": "old-hash",
        "is_default": True,
        "created_at": get_current_time(),
        "updated_at": get_current_time(),
    }
    if users_data is None:
        users_data = fake_user

    users_collection = MagicMock()
    users_collection.count_documents.return_value = count
    users_collection.find_one.return_value = users_data
    users_collection.update_one.return_value = MagicMock(modified_count=1)

    fake_client = MagicMock()
    fake_client.manager_app.users = users_collection
    fake_client.manager_app.sessions = MagicMock()

    with patch(
        "app.core.auth.ConfigManager.get_internal_db_client",
        return_value=fake_client,
    ):
        mgr = AuthManager()
    return mgr, users_collection


# ── Tests ────────────────────────────────────────────────────────────────────

class TestEnvSetAdminMissing:
    def test_seeds_admin_with_env_password(self, monkeypatch):
        monkeypatch.setenv("NUXT_ADMIN_PASSWORD", "fresh-secret-123")
        mgr, users = _make_auth_manager(count=0, users_data=None)

        users.insert_one.assert_called_once()
        inserted = users.insert_one.call_args[0][0]
        assert inserted["username"] == ADMIN
        # Bcrypt of "fresh-secret-123" must NOT equal the literal string
        assert inserted["password_hash"] != "fresh-secret-123"
        assert inserted["is_default"] is True


class TestEnvSetHashMismatch:
    def test_overwrites_admin_password(self, monkeypatch):
        monkeypatch.setenv("NUXT_ADMIN_PASSWORD", "new-secret-xyz")
        mgr, users = _make_auth_manager()

        users.update_one.assert_called_once()
        # We do not pin which bcrypt version produced the hash,
        # only that it is NOT the stale literal and matches a real bcrypt shape.
        payload = users.update_one.call_args[0][1]["$set"]
        assert payload["password_hash"] != "old-hash"
        assert payload["password_hash"].startswith("$2")
        assert payload["is_default"] is False
        assert "updated_at" in payload


class TestEnvSetHashMatch:
    def test_no_write_when_hash_already_matches(self, monkeypatch):
        monkeypatch.setenv("NUXT_ADMIN_PASSWORD", "same-secret-789")

        mgr = AuthManager()
        # Compute the real bcrypt the manager would store.
        same_hash = mgr.hash_password("same-secret-789")
        users = mgr.users_collection
        users.find_one.return_value = {
            "username": ADMIN,
            "password_hash": same_hash,
            "is_default": True,
        }
        users.update_one.reset_mock()

        mgr._ensure_default_user()

        users.update_one.assert_not_called()
        # No new insert either
        users.insert_one.assert_not_called()


class TestEnvUnset:
    def test_does_not_overwrite_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("NUXT_ADMIN_PASSWORD", raising=False)
        _make_auth_manager()  # admin exists with "old-hash"

        # Recreate with mocked collection to assert no writes
        users = MagicMock()
        users.count_documents.return_value = 1
        users.find_one.return_value = {"username": ADMIN, "password_hash": "old-hash"}
        fake_client = MagicMock()
        fake_client.manager_app.users = users
        fake_client.manager_app.sessions = MagicMock()
        with patch(
            "app.core.auth.ConfigManager.get_internal_db_client",
            return_value=fake_client,
        ):
            AuthManager()

        users.update_one.assert_not_called()
        users.insert_one.assert_not_called()
