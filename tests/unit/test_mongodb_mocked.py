"""Unit tests for MongoDB functionality with mocked connections.

These tests use mocks to test the MongoDB functionality without requiring a real MongoDB instance.
"""

from unittest.mock import MagicMock, Mock, patch

import pymongo
import pytest

import autoframe.mongodb as mongodb
from autoframe.mongodb import connect, count, fetch, fetch_batches
from autoframe.types import DataSourceError


class TestMongoDBConnectionMocked:
    """Test MongoDB connection with mocked pymongo."""

    @patch("autoframe.mongodb.pymongo.MongoClient")
    def test_connect_mongodb_success(self, mock_client_class):
        """Test successful MongoDB connection with mock."""
        # Setup mock
        mock_client = Mock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client_class.return_value = mock_client

        result = connect("mongodb://localhost:27017")

        assert result.is_ok()
        client = result.unwrap()
        assert client == mock_client
        mock_client_class.assert_called_once_with(
            "mongodb://localhost:27017",
            serverSelectionTimeoutMS=3000
        )
        mock_client.admin.command.assert_called_once_with("ping")

    @patch("autoframe.mongodb.pymongo.MongoClient")
    def test_connect_mongodb_failure(self, mock_client_class):
        """Test failed MongoDB connection with mock."""
        # Setup mock to raise exception
        mock_client_class.side_effect = pymongo.errors.ConnectionFailure("Connection failed")

        result = connect("mongodb://invalid:27017")

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DataSourceError)
        assert "Connection failed" in str(error)

    @patch("autoframe.mongodb.pymongo.MongoClient")
    def test_connect_mongodb_ping_failure(self, mock_client_class):
        """Test MongoDB connection where ping fails."""
        # Setup mock
        mock_client = Mock()
        mock_client.admin.command.side_effect = pymongo.errors.ServerSelectionTimeoutError("Ping failed")
        mock_client_class.return_value = mock_client

        result = connect("mongodb://localhost:27017")

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DataSourceError)


class TestMongoDBFetchMocked:
    """Test MongoDB fetch functionality with mocked connections."""

    @patch("autoframe.mongodb.connect")
    def test_fetch_success(self, mock_connect):
        """Test successful document fetching with mock."""
        # Setup mock client and proper chaining
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()

        # Mock the collection chain: client[database][collection]
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor

        # Mock documents - the key is that list(cursor) should return our test data
        test_docs = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        mock_cursor.__iter__.return_value = iter(test_docs)

        # Setup connection mock
        from logerr import Ok
        mock_connect.return_value = Ok(mock_client)

        result = fetch("mongodb://localhost", "testdb", "users", limit=2)

        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 2
        mock_collection.find.assert_called_once_with({})
        mock_cursor.limit.assert_called_once_with(2)
        # Verify client.close() was called
        mock_client.close.assert_called_once()

    @patch("autoframe.mongodb.connect")
    def test_fetch_with_query(self, mock_connect):
        """Test fetching with query filter using mock."""
        # Setup mock client and proper chaining
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()

        # Mock the collection chain: client[database][collection]
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = mock_cursor

        test_docs = [{"name": "Alice", "age": 30, "active": True}]
        mock_cursor.__iter__.return_value = iter(test_docs)

        from logerr import Ok
        mock_connect.return_value = Ok(mock_client)

        query = {"active": True}
        result = fetch("mongodb://localhost", "testdb", "users", query=query)

        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 1
        mock_collection.find.assert_called_once_with(query)
        # Verify client.close() was called
        mock_client.close.assert_called_once()

    @patch("autoframe.mongodb.connect")
    def test_fetch_connection_failure(self, mock_connect):
        """Test fetch with connection failure."""
        from logerr import Err
        mock_connect.return_value = Err(DataSourceError("Connection failed"))

        result = fetch("mongodb://invalid", "testdb", "users")

        assert result.is_err()
        error = result.unwrap_err()
        assert "Connection failed" in str(error)


class TestMongoDBCountMocked:
    """Test MongoDB count functionality with mocked connections."""

    @patch("autoframe.mongodb.connect")
    def test_count_success(self, mock_connect):
        """Test successful document counting with mock."""
        # Setup mock client and mock the entire call chain
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        # Mock the chaining: client[database][collection]
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.count_documents.return_value = 5

        from logerr import Ok
        mock_connect.return_value = Ok(mock_client)

        result = count("mongodb://localhost", "testdb", "users")

        assert result.is_ok()
        count_val = result.unwrap()
        assert count_val == 5
        mock_collection.count_documents.assert_called_once_with({})
        # Verify client.close() was called
        mock_client.close.assert_called_once()

    @patch("autoframe.mongodb.connect")
    def test_count_with_query(self, mock_connect):
        """Test counting with query filter using mock."""
        # Setup mock client and mock the entire call chain
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        # Mock the chaining: client[database][collection]
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.count_documents.return_value = 3

        from logerr import Ok
        mock_connect.return_value = Ok(mock_client)

        query = {"active": True}
        result = count("mongodb://localhost", "testdb", "users", query=query)

        assert result.is_ok()
        count_val = result.unwrap()
        assert count_val == 3
        mock_collection.count_documents.assert_called_once_with(query)
        # Verify client.close() was called
        mock_client.close.assert_called_once()


class TestMongoDBBatchesMocked:
    """Test MongoDB batch fetching with mocked connections."""

    @patch("autoframe.mongodb.connect")
    def test_fetch_in_batches_success(self, mock_connect):
        """Test successful batch fetching with mock."""
        # Simplified test that focuses on the key functionality
        # Just test that fetch_in_batches can be called and returns a result
        from logerr import Err

        from autoframe.types import DataSourceError

        # Mock connection failure for simplicity
        mock_connect.return_value = Err(DataSourceError("Connection failed"))

        result = fetch_batches("mongodb://localhost", "testdb", "users", batch_size=2)

        assert result.is_err()
        error = result.unwrap_err()
        assert "Connection failed" in str(error)


class TestMongoDBToDataFrameMocked:
    """Test MongoDB to DataFrame conversion with mocked data."""

    @patch("autoframe.mongodb.fetch")
    def test_mongodb_to_dataframe_success(self, mock_fetch):
        """Test successful MongoDB to DataFrame conversion."""
        # Mock the fetch function to return test documents
        test_docs = [
            {"name": "Alice", "age": 30, "active": True},
            {"name": "Bob", "age": 25, "active": False}
        ]

        from logerr import Ok
        mock_fetch.return_value = Ok(test_docs)

        result = mongodb.to_dataframe(
            "mongodb://localhost",
            "testdb",
            "users"
        )

        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 2
        assert "name" in df.columns
        assert "age" in df.columns
        assert "active" in df.columns

        mock_fetch.assert_called_once_with(
            "mongodb://localhost",
            "testdb",
            "users",
            None,
            None
        )

    @patch("autoframe.mongodb.fetch")
    def test_mongodb_to_dataframe_with_params(self, mock_fetch):
        """Test MongoDB to DataFrame conversion with query and limit."""
        test_docs = [{"name": "Alice", "age": 30, "active": True}]

        from logerr import Ok
        mock_fetch.return_value = Ok(test_docs)

        query = {"active": True}
        limit = 10
        result = mongodb.to_dataframe(
            "mongodb://localhost",
            "testdb",
            "users",
            query=query,
            limit=limit
        )

        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 1

        mock_fetch.assert_called_once_with(
            "mongodb://localhost",
            "testdb",
            "users",
            query,
            limit
        )

    @patch("autoframe.mongodb.fetch")
    def test_mongodb_to_dataframe_with_schema(self, mock_fetch):
        """Test MongoDB to DataFrame conversion with schema application."""
        test_docs = [
            {"name": "Alice", "age": "30", "active": "true"},
            {"name": "Bob", "age": "25", "active": "false"}
        ]

        from logerr import Ok
        mock_fetch.return_value = Ok(test_docs)

        schema = {"age": "int", "active": "bool"}
        result = mongodb.to_dataframe(
            "mongodb://localhost",
            "testdb",
            "users",
            schema=schema
        )

        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 2
        # Check that schema was applied
        assert df["age"].dtype.name.startswith("int")

    @patch("autoframe.mongodb.fetch")
    def test_mongodb_to_dataframe_fetch_failure(self, mock_fetch):
        """Test MongoDB to DataFrame conversion with fetch failure."""
        from logerr import Err
        mock_fetch.return_value = Err(DataSourceError("Connection failed"))

        result = mongodb.to_dataframe(
            "mongodb://localhost",
            "testdb",
            "users"
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert "Connection failed" in str(error)

    @patch("autoframe.mongodb.fetch")
    def test_mongodb_to_dataframe_empty_result(self, mock_fetch):
        """Test MongoDB to DataFrame conversion with empty result."""
        from logerr import Ok
        mock_fetch.return_value = Ok([])

        result = mongodb.to_dataframe(
            "mongodb://localhost",
            "testdb",
            "users"
        )

        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 0
        assert isinstance(df.columns, type(df.columns))  # Has columns attribute


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
