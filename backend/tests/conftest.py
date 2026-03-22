"""Test fixtures for MongoDB Manager backend tests

Strategy: several app modules create MongoDB connections at import time:
  - database.py:93  → _db_client = DatabaseClient()  → MongoClient.ping()
  - app/api/auth.py:19 → auth_manager = AuthManager() → create_index()
  - app/core/utils/config.py:124 → from pymongo import MongoClient (local import)

The only reliable approach is to mock pymongo.MongoClient itself BEFORE
any app module is imported, so the real network call never happens.
"""

import atexit
import pytest
from unittest.mock import patch, MagicMock


# ── Build a fully-mocked MongoClient before any app code is imported ─────────

def _make_mongo_client_mock(*args, **kwargs):
    """Factory that returns a MagicMock mimicking a connected MongoClient"""
    client = MagicMock()
    # admin.command('ping') must not raise
    client.admin.command.return_value = {"ok": 1}
    return client


# Patch MongoClient at the pymongo package level — this is what all local
# `from pymongo import MongoClient` statements resolve to at runtime.
_mongo_patcher = patch("pymongo.MongoClient", side_effect=_make_mongo_client_mock)
_mongo_patcher.start()
atexit.register(_mongo_patcher.stop)

# Now it is safe to import app modules — no real socket connections will be made
from fastapi.testclient import TestClient  # noqa: E402
from app.main_api import app               # noqa: E402
from app.middleware.auth import create_access_token  # noqa: E402

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """TestClient with mocked database init/close to avoid needing real MongoDB"""
    with patch("app.main_api.init_database"), patch("app.main_api.close_database"):
        with TestClient(app) as c:
            yield c


@pytest.fixture
def auth_token():
    """Valid JWT token for test user"""
    return create_access_token({"username": "admin"})


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers with valid JWT token"""
    return {"Authorization": f"Bearer {auth_token}"}
