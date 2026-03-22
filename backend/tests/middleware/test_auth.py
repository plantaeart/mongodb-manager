"""Tests for JWT authentication middleware"""

import pytest
from fastapi import HTTPException
from freezegun import freeze_time
from datetime import datetime, timezone, timedelta
from jose import jwt

from app.middleware.auth import (
    create_access_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_HOURS,
)


class TestCreateAccessToken:
    """Tests for create_access_token()"""

    def test_returns_string(self):
        token = create_access_token({"username": "admin"})
        assert isinstance(token, str)

    def test_token_has_three_parts(self):
        token = create_access_token({"username": "admin"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_includes_username_claim(self):
        token = create_access_token({"username": "testuser"})
        payload = verify_token(token)
        assert payload["username"] == "testuser"

    def test_token_includes_exp_claim(self):
        token = create_access_token({"username": "admin"})
        payload = verify_token(token)
        assert "exp" in payload

    def test_exp_is_approximately_24_hours_from_now(self):
        now = datetime.now(timezone.utc)
        token = create_access_token({"username": "admin"})
        payload = verify_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        delta = exp - now
        # Should be roughly ACCESS_TOKEN_EXPIRE_HOURS hours (within 60 seconds tolerance)
        assert abs(delta.total_seconds() - ACCESS_TOKEN_EXPIRE_HOURS * 3600) < 60


class TestVerifyToken:
    """Tests for verify_token()"""

    def test_valid_token_returns_payload(self):
        token = create_access_token({"username": "admin"})
        payload = verify_token(token)
        assert payload["username"] == "admin"

    def test_tampered_signature_raises_401(self):
        token = create_access_token({"username": "admin"})
        # Corrupt the signature part
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".invalidsignature"
        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered)
        assert exc_info.value.status_code == 401

    def test_completely_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.token")
        assert exc_info.value.status_code == 401

    def test_token_missing_username_claim_raises_401(self):
        # Create a token without 'username' claim
        payload = {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        # Create token that expires 1 hour in the past
        payload = {
            "username": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == 401


class TestAuthEndpointIntegration:
    """Integration tests for auth via TestClient"""

    def test_health_check_requires_no_auth(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_protected_endpoint_without_token_returns_401(self, client):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect list", "params": {}}
        )
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token_returns_200(self, client, auth_headers):
        response = client.post(
            "/api/commands/execute",
            json={"command": "connect list", "params": {}},
            headers=auth_headers
        )
        # Should reach the handler (200 or at most a business-logic error, not 401/403)
        assert response.status_code not in (401, 403)
