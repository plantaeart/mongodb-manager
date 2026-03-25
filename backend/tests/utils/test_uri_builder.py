"""Tests for MongoDB URI builder utility"""

import pytest
from app.core.utils.uri_builder import build_mongodb_uri, build_mongodb_uri_masked


class TestBuildMongodbUri:
    """Tests for build_mongodb_uri()"""

    def test_no_auth_returns_basic_uri(self):
        uri = build_mongodb_uri("localhost", 27017)
        assert uri == "mongodb://localhost:27017"

    def test_no_auth_no_query_string(self):
        uri = build_mongodb_uri("localhost", 27017)
        assert "?" not in uri

    def test_with_auth_no_auth_source_by_default(self):
        # auth_source defaults to None — no authSource appended unless explicitly set
        uri = build_mongodb_uri("localhost", 27017, "admin", "secret")
        assert uri == "mongodb://admin:secret@localhost:27017"
        assert "authSource" not in uri

    def test_with_auth_custom_auth_source(self):
        uri = build_mongodb_uri("localhost", 27017, "user", "pass", auth_source="mydb")
        assert "authSource=mydb" in uri

    def test_special_chars_in_credentials_are_url_encoded(self):
        uri = build_mongodb_uri("localhost", 27017, "user@email", "p@ss:w0rd")
        assert "user%40email" in uri
        assert "p%40ss%3Aw0rd" in uri
        assert "@email" not in uri.split("@")[0]  # raw @ not in credentials part

    def test_with_database(self):
        uri = build_mongodb_uri("localhost", 27017, database="mydb")
        assert "/mydb" in uri
        assert uri.startswith("mongodb://localhost:27017/mydb")

    def test_with_auth_and_database(self):
        uri = build_mongodb_uri("localhost", 27017, "user", "pass", database="mydb")
        assert "/mydb" in uri
        # auth_source not set → no authSource in URI
        assert "authSource" not in uri

    def test_with_options_dict(self):
        uri = build_mongodb_uri("localhost", 27017, options={"connectTimeoutMS": "3000", "retryWrites": "true"})
        assert "connectTimeoutMS=3000" in uri
        assert "retryWrites=true" in uri

    def test_with_auth_and_options(self):
        uri = build_mongodb_uri("localhost", 27017, "user", "pass", options={"ssl": "true"})
        # auth_source not set → no authSource in URI
        assert "authSource" not in uri
        assert "ssl=true" in uri

    def test_empty_host_raises_value_error(self):
        with pytest.raises(ValueError, match="Host cannot be empty"):
            build_mongodb_uri("", 27017)

    def test_whitespace_host_raises_value_error(self):
        with pytest.raises(ValueError, match="Host cannot be empty"):
            build_mongodb_uri("   ", 27017)

    def test_port_zero_raises_value_error(self):
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            build_mongodb_uri("localhost", 0)

    def test_port_too_large_raises_value_error(self):
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            build_mongodb_uri("localhost", 65536)

    def test_port_not_int_raises_value_error(self):
        with pytest.raises((ValueError, TypeError)):
            build_mongodb_uri("localhost", "abc")  # type: ignore

    def test_username_without_password_raises_value_error(self):
        with pytest.raises(ValueError, match="Both username and password must be provided together"):
            build_mongodb_uri("localhost", 27017, username="user")

    def test_password_without_username_raises_value_error(self):
        with pytest.raises(ValueError, match="Both username and password must be provided together"):
            build_mongodb_uri("localhost", 27017, password="secret")

    def test_custom_host_and_port(self):
        uri = build_mongodb_uri("db.example.com", 28000)
        assert uri == "mongodb://db.example.com:28000"

    def test_empty_database_not_added(self):
        uri = build_mongodb_uri("localhost", 27017, database="")
        assert "/?" not in uri
        assert uri == "mongodb://localhost:27017"


class TestBuildMongodbUriMasked:
    """Tests for build_mongodb_uri_masked()"""

    def test_no_auth_returns_basic_uri(self):
        uri = build_mongodb_uri_masked("localhost", 27017)
        assert uri == "mongodb://localhost:27017"

    def test_with_username_shows_masked_password(self):
        uri = build_mongodb_uri_masked("localhost", 27017, username="admin")
        assert "admin:***@" in uri
        assert "***" in uri

    def test_real_password_never_in_output(self):
        # masked version takes no password param — the real password is never passed
        uri = build_mongodb_uri_masked("localhost", 27017, username="admin")
        # Confirm no real password leaks (only *** placeholder)
        assert "secret" not in uri
        assert "password" not in uri.lower().replace("***", "")

    def test_masked_uri_no_auth_source_by_default(self):
        # auth_source defaults to None — no authSource in masked URI unless explicitly set
        uri = build_mongodb_uri_masked("localhost", 27017, username="admin")
        assert "authSource" not in uri

    def test_masked_uri_with_database(self):
        uri = build_mongodb_uri_masked("localhost", 27017, username="admin", database="mydb")
        assert "/mydb" in uri
        assert "admin:***@" in uri

    def test_masked_uri_without_username_no_auth_source(self):
        uri = build_mongodb_uri_masked("localhost", 27017)
        assert "authSource" not in uri
        assert "***" not in uri

    def test_masked_uri_with_options(self):
        uri = build_mongodb_uri_masked("localhost", 27017, options={"ssl": "true"})
        assert "ssl=true" in uri
