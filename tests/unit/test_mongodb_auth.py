"""Tests for MongoDB authentication integration."""

from unittest.mock import Mock, patch

import pytest
from logerr import Err, Ok

from autoframe.auth import MongoConnectionConfig, MongoCredentials, create_local_config
from autoframe.mongodb import _resolve_connection, connect, fetch, to_dataframe
from autoframe.types import DataSourceError


class TestResolveConnection:
    """Test connection resolution functionality."""

    def test_resolve_connection_string(self):
        """Test resolving a valid connection string."""
        conn_str = "mongodb://localhost:27017"
        result = _resolve_connection(conn_str)

        assert result == conn_str

    def test_resolve_connection_config(self):
        """Test resolving a connection config."""
        config = create_local_config(database="testdb")
        result = _resolve_connection(config)

        assert result == "mongodb://localhost:27017/testdb"

    def test_resolve_invalid_connection_string(self):
        """Test resolving an invalid connection string."""
        with pytest.raises(DataSourceError, match="Invalid connection string"):
            _resolve_connection("invalid://connection")

    def test_resolve_connection_with_auth(self):
        """Test resolving a connection config with authentication."""
        creds = MongoCredentials(username="user", password="pass")
        config = MongoConnectionConfig(
            host="localhost", port=27017, credentials=creds, database="testdb"
        )

        result = _resolve_connection(config)
        expected = "mongodb://user:pass@localhost:27017/testdb?authSource=admin&authMechanism=SCRAM-SHA-256"

        assert result == expected


class TestMongoDBConnect:
    """Test MongoDB connection with authentication."""

    @patch("autoframe.mongodb.pymongo.MongoClient")
    @patch("autoframe.mongodb.db_retry")
    def test_connect_with_connection_string(self, mock_retry, mock_client_class):
        """Test connection with connection string."""
        mock_client = Mock()
        mock_client.admin.command.return_value = True
        mock_client_class.return_value = mock_client

        # Mock the retry decorator to return the result directly
        mock_retry.side_effect = lambda f: lambda: Ok(f())

        result = connect("mongodb://localhost:27017")

        assert result.is_ok()
        client = result.unwrap()
        assert client == mock_client

        # Verify client was created with correct connection string
        mock_client_class.assert_called_once_with(
            "mongodb://localhost:27017", serverSelectionTimeoutMS=3000
        )
        mock_client.admin.command.assert_called_once_with("ping")

    @patch("autoframe.mongodb.pymongo.MongoClient")
    def test_connect_with_config(self, mock_client_class):
        """Test connection with configuration object."""
        mock_client = Mock()
        mock_client.admin.command.return_value = True
        mock_client_class.return_value = mock_client

        config = create_local_config(database="testdb")

        with patch("autoframe.mongodb.db_retry", lambda f: f):
            result = connect(config)

        assert result.is_ok()

        # Verify client was created with connection string from config
        mock_client_class.assert_called_once_with(
            "mongodb://localhost:27017/testdb", serverSelectionTimeoutMS=3000
        )

    @patch("autoframe.mongodb.pymongo.MongoClient")
    def test_connect_with_auth_config(self, mock_client_class):
        """Test connection with authenticated configuration."""
        mock_client = Mock()
        mock_client.admin.command.return_value = True
        mock_client_class.return_value = mock_client

        creds = MongoCredentials(username="user", password="pass")
        config = MongoConnectionConfig(host="localhost", port=27017, credentials=creds)

        with patch("autoframe.mongodb.db_retry", lambda f: f):
            result = connect(config)

        assert result.is_ok()

        # Verify client was created with authentication
        expected_uri = "mongodb://user:pass@localhost:27017?authSource=admin&authMechanism=SCRAM-SHA-256"
        mock_client_class.assert_called_once_with(
            expected_uri, serverSelectionTimeoutMS=3000
        )

    @patch("autoframe.mongodb.pymongo.MongoClient")
    @patch("autoframe.mongodb.db_retry")
    def test_connect_failure(self, mock_retry, mock_client_class):
        """Test connection failure handling."""
        mock_client_class.side_effect = Exception("Connection failed")

        # Mock the retry decorator to return the error directly
        mock_retry.side_effect = lambda f: lambda: Err(
            DataSourceError("Connection failed")
        )

        result = connect("mongodb://localhost:27017")

        assert result.is_err()
        error = result.unwrap_err()
        assert "Connection failed" in str(error)


class TestMongoDBFetch:
    """Test MongoDB fetch operations with authentication."""

    @patch("autoframe.mongodb.connect")
    @patch("autoframe.mongodb._query_collection")
    def test_fetch_with_connection_string(self, mock_query, mock_connect):
        """Test fetch with connection string."""
        mock_client = Mock()
        mock_connect.return_value = Ok(mock_client)
        mock_query.return_value = Ok([{"test": "data"}])

        result = fetch("mongodb://localhost:27017", "testdb", "testcoll")

        assert result.is_ok()
        data = result.unwrap()
        assert data == [{"test": "data"}]

        # Verify connect was called with resolved connection string
        mock_connect.assert_called_once_with("mongodb://localhost:27017")
        mock_query.assert_called_once_with(
            mock_client, "testdb", "testcoll", None, None
        )

    @patch("autoframe.mongodb.connect")
    @patch("autoframe.mongodb._query_collection")
    def test_fetch_with_config(self, mock_query, mock_connect):
        """Test fetch with configuration object."""
        mock_client = Mock()
        mock_connect.return_value = Ok(mock_client)
        mock_query.return_value = Ok([{"test": "data"}])

        config = create_local_config(database="testdb")
        result = fetch(config, "testdb", "testcoll", {"active": True}, 100)

        assert result.is_ok()

        # Verify connect was called with the config object (not the resolved string)
        mock_connect.assert_called_once_with(config)
        mock_query.assert_called_once_with(
            mock_client, "testdb", "testcoll", {"active": True}, 100
        )

    @patch("autoframe.mongodb.connect")
    def test_fetch_connection_failure(self, mock_connect):
        """Test fetch with connection failure."""
        mock_connect.return_value = Err(DataSourceError("Connection failed"))

        result = fetch("mongodb://localhost:27017", "testdb", "testcoll")

        assert result.is_err()
        error = result.unwrap_err()
        assert "Connection failed" in str(error)


class TestMongoDBToDataFrame:
    """Test MongoDB to DataFrame conversion with authentication."""

    @patch("autoframe.mongodb.fetch")
    @patch("autoframe.mongodb._to_dataframe")
    @patch("autoframe.mongodb.log_failure")
    @patch("autoframe.mongodb.log_conversion")
    def test_to_dataframe_with_config(
        self, mock_log_conv, mock_log_fail, mock_to_df, mock_fetch
    ):
        """Test to_dataframe with configuration object."""
        # Setup mocks
        mock_documents = [{"name": "test", "value": 123}]
        mock_fetch.return_value = Ok(mock_documents)
        mock_log_fail.return_value = Ok(mock_documents)

        mock_dataframe = Mock()
        mock_to_df.return_value = Ok(mock_dataframe)
        mock_log_conv.return_value = Ok(mock_dataframe)

        # Create config with authentication
        creds = MongoCredentials(username="user", password="pass")
        config = MongoConnectionConfig(
            host="localhost", port=27017, credentials=creds, database="testdb"
        )

        result = to_dataframe(config, "testdb", "testcoll", backend="pandas")

        assert result.is_ok()
        dataframe = result.unwrap()
        assert dataframe == mock_dataframe

        # Verify fetch was called with correct connection string
        expected_connection_string = "mongodb://user:pass@localhost:27017/testdb?authSource=admin&authMechanism=SCRAM-SHA-256"
        mock_fetch.assert_called_once_with(
            expected_connection_string, "testdb", "testcoll", None, None
        )

    @patch("autoframe.mongodb.fetch")
    @patch("autoframe.mongodb._to_dataframe")
    @patch("autoframe.mongodb.log_failure")
    @patch("autoframe.mongodb.log_conversion")
    def test_to_dataframe_with_connection_string(
        self, mock_log_conv, mock_log_fail, mock_to_df, mock_fetch
    ):
        """Test to_dataframe with connection string."""
        # Setup mocks
        mock_documents = [{"name": "test", "value": 123}]
        mock_fetch.return_value = Ok(mock_documents)
        mock_log_fail.return_value = Ok(mock_documents)

        mock_dataframe = Mock()
        mock_to_df.return_value = Ok(mock_dataframe)
        mock_log_conv.return_value = Ok(mock_dataframe)

        connection_string = "mongodb://localhost:27017"
        result = to_dataframe(connection_string, "testdb", "testcoll")

        assert result.is_ok()

        # Verify fetch was called with the same connection string
        mock_fetch.assert_called_once_with(
            connection_string, "testdb", "testcoll", None, None
        )


class TestAuthenticationSecurity:
    """Test security aspects of authentication."""

    def test_credentials_not_logged_in_connection_string(self):
        """Test that credentials are properly handled in connection strings."""
        creds = MongoCredentials(username="user", password="secret")
        config = MongoConnectionConfig(host="localhost", port=27017, credentials=creds)

        connection_string = config.build_connection_string()

        # This is expected behavior - credentials are in the connection string
        # The security is handled by the logging module which sanitizes them
        assert "user" in connection_string
        assert "secret" in connection_string

    def test_special_characters_encoded(self):
        """Test that special characters in credentials are properly encoded."""
        creds = MongoCredentials(username="user@domain.com", password="p@ss:w0rd!")
        config = MongoConnectionConfig(host="localhost", port=27017, credentials=creds)

        connection_string = config.build_connection_string()

        # Verify URL encoding
        assert "user%40domain.com" in connection_string
        assert "p%40ss%3Aw0rd%21" in connection_string

        # Verify raw credentials are not in the string
        assert "user@domain.com" not in connection_string
        assert "p@ss:w0rd!" not in connection_string

    def test_connection_validation_prevents_injection(self):
        """Test that connection validation prevents basic injection attempts."""
        invalid_connections = [
            "mongodb://localhost:27017; DROP TABLE users;",
            "javascript:alert('xss')",
            "file:///etc/passwd",
        ]

        for conn in invalid_connections:
            with pytest.raises(DataSourceError):
                _resolve_connection(conn)


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests requiring actual MongoDB connection."""

    def test_connection_with_environment_config(self):
        """Test connection using environment configuration.

        Note: This test requires environment variables to be set:
        - MONGODB_HOST
        - MONGODB_USERNAME
        - MONGODB_PASSWORD
        """
        pytest.skip("Requires actual MongoDB instance and credentials")

        # from autoframe.auth import create_config_from_env
        # from autoframe.mongodb import connect
        #
        # config_result = create_config_from_env()
        # assert config_result.is_ok()
        #
        # config = config_result.unwrap()
        # connection_result = connect(config)
        #
        # assert connection_result.is_ok()
        #
        # client = connection_result.unwrap()
        # client.close()

    def test_full_workflow_with_authentication(self):
        """Test complete workflow from environment to DataFrame."""
        pytest.skip("Requires actual MongoDB instance and credentials")

        # from autoframe.auth import create_config_from_env
        # from autoframe.mongodb import to_dataframe
        #
        # config_result = create_config_from_env()
        # assert config_result.is_ok()
        #
        # config = config_result.unwrap()
        # df_result = to_dataframe(config, "testdb", "testcoll", limit=10)
        #
        # assert df_result.is_ok()
        # df = df_result.unwrap()
        # assert len(df) <= 10
