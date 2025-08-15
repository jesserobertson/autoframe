"""Tests for authentication and credential management."""

import os
from unittest.mock import patch

import pytest

from autoframe.auth import (
    MongoConnectionConfig,
    MongoCredentials,
    create_authenticated_config,
    create_config_from_env,
    create_credentials_from_env,
    create_local_config,
    validate_connection_string,
)


class TestMongoCredentials:
    """Test MongoDB credentials management."""

    def test_credentials_creation(self):
        """Test basic credential creation."""
        creds = MongoCredentials(
            username="testuser",
            password="testpass",
            auth_database="mydb",
            auth_mechanism="SCRAM-SHA-256",
        )

        assert creds.username == "testuser"
        assert creds.password == "testpass"
        assert creds.auth_database == "mydb"
        assert creds.auth_mechanism == "SCRAM-SHA-256"

    def test_credentials_defaults(self):
        """Test credential defaults."""
        creds = MongoCredentials(username="user", password="pass")

        assert creds.auth_database == "admin"
        assert creds.auth_mechanism == "SCRAM-SHA-256"

    def test_credentials_immutable(self):
        """Test that credentials are immutable."""
        creds = MongoCredentials(username="user", password="pass")

        with pytest.raises(AttributeError):
            creds.username = "newuser"  # type: ignore

    def test_to_connection_params(self):
        """Test conversion to connection parameters."""
        creds = MongoCredentials(
            username="testuser", password="testpass", auth_database="mydb"
        )

        params = creds.to_connection_params()
        expected = {
            "username": "testuser",
            "password": "testpass",
            "authSource": "mydb",
            "authMechanism": "SCRAM-SHA-256",
        }

        assert params == expected


class TestMongoConnectionConfig:
    """Test MongoDB connection configuration."""

    def test_basic_config(self):
        """Test basic configuration creation."""
        config = MongoConnectionConfig(host="localhost", port=27017)

        assert config.host == "localhost"
        assert config.port == 27017
        assert config.database is None
        assert config.credentials is None
        assert config.ssl is False

    def test_config_with_credentials(self):
        """Test configuration with credentials."""
        creds = MongoCredentials(username="user", password="pass")
        config = MongoConnectionConfig(
            host="remote.example.com",
            port=27017,
            database="mydb",
            credentials=creds,
            ssl=True,
        )

        assert config.credentials == creds
        assert config.ssl is True
        assert config.database == "mydb"

    def test_build_connection_string_simple(self):
        """Test building simple connection string."""
        config = MongoConnectionConfig(host="localhost", port=27017)
        connection_string = config.build_connection_string()

        assert connection_string == "mongodb://localhost:27017"

    def test_build_connection_string_with_database(self):
        """Test building connection string with database."""
        config = MongoConnectionConfig(host="localhost", port=27017, database="mydb")
        connection_string = config.build_connection_string()

        assert connection_string == "mongodb://localhost:27017/mydb"

    def test_build_connection_string_with_auth(self):
        """Test building connection string with authentication."""
        creds = MongoCredentials(username="user", password="pass")
        config = MongoConnectionConfig(host="localhost", port=27017, credentials=creds)
        connection_string = config.build_connection_string()

        expected = "mongodb://user:pass@localhost:27017?authSource=admin&authMechanism=SCRAM-SHA-256"
        assert connection_string == expected

    def test_build_connection_string_with_special_chars(self):
        """Test building connection string with special characters in password."""
        creds = MongoCredentials(username="user@domain", password="p@ss:w0rd")
        config = MongoConnectionConfig(host="localhost", port=27017, credentials=creds)
        connection_string = config.build_connection_string()

        # URL encoding should handle special characters
        assert "user%40domain" in connection_string
        assert "p%40ss%3Aw0rd" in connection_string

    def test_build_connection_string_with_ssl(self):
        """Test building connection string with SSL."""
        config = MongoConnectionConfig(
            host="localhost", port=27017, ssl=True, ssl_cert_path="/path/to/cert.pem"
        )
        connection_string = config.build_connection_string()

        assert "ssl=true" in connection_string
        assert "sslCertificateKeyFile=/path/to/cert.pem" in connection_string

    def test_build_connection_string_with_custom_options(self):
        """Test building connection string with custom options."""
        config = MongoConnectionConfig(
            host="localhost",
            port=27017,
            connection_options={"maxPoolSize": "50", "minPoolSize": "5"},
        )
        connection_string = config.build_connection_string()

        assert "maxPoolSize=50" in connection_string
        assert "minPoolSize=5" in connection_string


class TestEnvironmentCredentials:
    """Test environment-based credential loading."""

    @patch.dict(
        os.environ,
        {
            "MONGODB_USERNAME": "envuser",
            "MONGODB_PASSWORD": "envpass",
            "MONGODB_AUTH_DB": "envdb",
        },
    )
    def test_create_credentials_from_env_success(self):
        """Test successful credential creation from environment."""
        result = create_credentials_from_env()

        assert result.is_ok()
        creds = result.unwrap()
        assert creds.username == "envuser"
        assert creds.password == "envpass"
        assert creds.auth_database == "envdb"

    @patch.dict(
        os.environ, {"MONGODB_USERNAME": "envuser", "MONGODB_PASSWORD": "envpass"}
    )
    def test_create_credentials_from_env_default_auth_db(self):
        """Test credential creation with default auth database."""
        result = create_credentials_from_env()

        assert result.is_ok()
        creds = result.unwrap()
        assert creds.auth_database == "admin"

    @patch.dict(os.environ, {"MONGODB_USERNAME": "envuser"}, clear=True)
    def test_create_credentials_from_env_missing_password(self):
        """Test credential creation with missing password."""
        result = create_credentials_from_env()

        assert result.is_err()
        error = result.unwrap_err()
        assert "MONGODB_PASSWORD" in str(error)

    @patch.dict(os.environ, {"MONGODB_PASSWORD": "envpass"}, clear=True)
    def test_create_credentials_from_env_missing_username(self):
        """Test credential creation with missing username."""
        result = create_credentials_from_env()

        assert result.is_err()
        error = result.unwrap_err()
        assert "MONGODB_USERNAME" in str(error)

    @patch.dict(
        os.environ,
        {
            "MONGODB_HOST": "remote.example.com",
            "MONGODB_PORT": "27017",
            "MONGODB_DATABASE": "mydb",
            "MONGODB_USERNAME": "envuser",
            "MONGODB_PASSWORD": "envpass",
        },
    )
    def test_create_config_from_env_success(self):
        """Test successful config creation from environment."""
        result = create_config_from_env()

        assert result.is_ok()
        config = result.unwrap()
        assert config.host == "remote.example.com"
        assert config.port == 27017
        assert config.database == "mydb"
        assert config.credentials is not None
        assert config.credentials.username == "envuser"

    @patch.dict(os.environ, {}, clear=True)
    def test_create_config_from_env_defaults(self):
        """Test config creation with defaults."""
        result = create_config_from_env()

        assert result.is_ok()
        config = result.unwrap()
        assert config.host == "localhost"
        assert config.port == 27017
        assert config.database is None
        assert config.credentials is None

    @patch.dict(os.environ, {"MONGODB_PORT": "invalid"}, clear=True)
    def test_create_config_from_env_invalid_port(self):
        """Test config creation with invalid port."""
        result = create_config_from_env()

        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid port value" in str(error)

    @patch.dict(os.environ, {"MONGODB_PORT": "99999"}, clear=True)
    def test_create_config_from_env_port_out_of_range(self):
        """Test config creation with port out of range."""
        result = create_config_from_env()

        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid port number" in str(error)


class TestConfigFactories:
    """Test configuration factory functions."""

    def test_create_local_config(self):
        """Test local configuration creation."""
        config = create_local_config()

        assert config.host == "localhost"
        assert config.port == 27017
        assert config.database is None
        assert config.credentials is None

    def test_create_local_config_with_database(self):
        """Test local configuration with database."""
        config = create_local_config(database="testdb", port=27018)

        assert config.host == "localhost"
        assert config.port == 27018
        assert config.database == "testdb"
        assert config.credentials is None

    def test_create_authenticated_config(self):
        """Test authenticated configuration creation."""
        config = create_authenticated_config(
            host="remote.example.com",
            username="user",
            password="pass",
            database="mydb",
            ssl=True,
        )

        assert config.host == "remote.example.com"
        assert config.port == 27017
        assert config.database == "mydb"
        assert config.ssl is True
        assert config.credentials is not None
        assert config.credentials.username == "user"
        assert config.credentials.password == "pass"

    def test_create_authenticated_config_defaults(self):
        """Test authenticated configuration with defaults."""
        config = create_authenticated_config(
            host="remote.example.com", username="user", password="pass"
        )

        assert config.port == 27017
        assert config.database is None
        assert config.ssl is False
        assert config.credentials.auth_database == "admin"


class TestConnectionStringValidation:
    """Test connection string validation."""

    def test_validate_valid_connection_strings(self):
        """Test validation of valid connection strings."""
        valid_strings = [
            "mongodb://localhost:27017",
            "mongodb://user:pass@localhost:27017",
            "mongodb://user:pass@localhost:27017/database",
            "mongodb+srv://cluster.mongodb.net",
            "mongodb://localhost:27017?ssl=true",
        ]

        for conn_str in valid_strings:
            result = validate_connection_string(conn_str)
            assert result.is_ok(), f"Failed to validate: {conn_str}"

    def test_validate_invalid_connection_strings(self):
        """Test validation of invalid connection strings."""
        invalid_strings = [
            "",
            "http://localhost:27017",
            "localhost:27017",
            "invalid://string",
        ]

        for conn_str in invalid_strings:
            result = validate_connection_string(conn_str)
            assert result.is_err(), f"Should have failed validation: {conn_str}"

    def test_validate_empty_connection_string(self):
        """Test validation of empty connection string."""
        result = validate_connection_string("")

        assert result.is_err()
        error = result.unwrap_err()
        assert "cannot be empty" in str(error)


class TestIntegration:
    """Integration tests for authentication components."""

    def test_full_workflow_with_auth_config(self):
        """Test complete workflow with authentication config."""
        # Create authenticated configuration
        config = create_authenticated_config(
            host="localhost",
            username="testuser",
            password="testpass",
            database="testdb",
            ssl=False,
        )

        # Build connection string
        connection_string = config.build_connection_string()

        # Validate the connection string
        result = validate_connection_string(connection_string)
        assert result.is_ok()

        # Verify the string contains expected components
        assert "testuser" in connection_string
        assert "testpass" in connection_string
        assert "localhost" in connection_string
        assert "testdb" in connection_string
        assert "authSource=admin" in connection_string

    @patch.dict(
        os.environ,
        {
            "MONGODB_HOST": "testhost",
            "MONGODB_USERNAME": "testuser",
            "MONGODB_PASSWORD": "testpass",
            "MONGODB_DATABASE": "testdb",
        },
    )
    def test_full_workflow_from_env(self):
        """Test complete workflow from environment variables."""
        # Create config from environment
        config_result = create_config_from_env()
        assert config_result.is_ok()

        config = config_result.unwrap()

        # Build and validate connection string
        connection_string = config.build_connection_string()
        validation_result = validate_connection_string(connection_string)

        assert validation_result.is_ok()
        assert "testhost" in connection_string
        assert "testuser" in connection_string
        assert "testdb" in connection_string
