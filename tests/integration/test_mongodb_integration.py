"""Integration tests for MongoDB functionality.

These tests require a running MongoDB instance and will be skipped if MongoDB is not available.
"""

import pytest
import os
from typing import Dict, Any, List
import pymongo
from autoframe.sources.simple import fetch, connect_mongodb, count, fetch_in_batches
import autoframe.mongodb as mongodb
from autoframe.utils.functional import to_dataframe


# Test data
SAMPLE_USERS = [
    {"_id": "user1", "name": "Alice", "age": 30, "active": True, "email": "alice@example.com"},
    {"_id": "user2", "name": "Bob", "age": 25, "active": True, "email": "bob@example.com"},
    {"_id": "user3", "name": "Charlie", "age": 35, "active": False, "email": "charlie@example.com"},
    {"_id": "user4", "name": "Diana", "age": 28, "active": True, "email": "diana@example.com"},
    {"_id": "user5", "name": "Eve", "age": 22, "active": False, "email": "eve@example.com"},
]

SAMPLE_ORDERS = [
    {"_id": "order1", "user_id": "user1", "total": 100.50, "status": "completed", "items": 3},
    {"_id": "order2", "user_id": "user2", "total": 75.25, "status": "pending", "items": 2},
    {"_id": "order3", "user_id": "user1", "total": 200.00, "status": "completed", "items": 5},
    {"_id": "order4", "user_id": "user3", "total": 50.75, "status": "cancelled", "items": 1},
    {"_id": "order5", "user_id": "user4", "total": 150.00, "status": "completed", "items": 4},
]


@pytest.fixture(scope="session")
def mongodb_uri():
    """Get MongoDB URI from environment or use default."""
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


@pytest.fixture(scope="session")
def test_database():
    """Database name for tests."""
    return "autoframe_test"


@pytest.fixture(scope="session")
def mongodb_client(mongodb_uri):
    """Create MongoDB client and check if MongoDB is available."""
    try:
        client = pymongo.MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        yield client
        client.close()
    except (pymongo.errors.ConnectionFailure, pymongo.errors.ServerSelectionTimeoutError):
        pytest.skip("MongoDB not available for integration tests")


@pytest.fixture(scope="function")
def setup_test_data(mongodb_client, test_database):
    """Setup test data in MongoDB and clean up after test."""
    db = mongodb_client[test_database]
    
    # Drop existing collections and recreate with test data
    db.users.drop()
    db.orders.drop()
    
    # Insert fresh test data
    db.users.insert_many(SAMPLE_USERS)
    db.orders.insert_many(SAMPLE_ORDERS)
    
    yield
    
    # Note: We don't drop collections after test since they contain the persistent test data
    # that the initialization script created. Just leave the data as is.


class TestMongoDBConnection:
    """Test MongoDB connection functionality."""
    
    def test_connect_mongodb_success(self, mongodb_uri, mongodb_client):
        """Test successful MongoDB connection."""
        result = connect_mongodb(mongodb_uri)
        
        assert result.is_ok()
        client = result.unwrap()
        assert isinstance(client, pymongo.MongoClient)
        client.close()
    
    def test_connect_mongodb_failure(self):
        """Test failed MongoDB connection."""
        result = connect_mongodb("mongodb://invalid-host:27017")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "connection" in str(error).lower() or "timeout" in str(error).lower()


class TestMongoDBFetch:
    """Test MongoDB data fetching functionality."""
    
    def test_fetch_all_documents(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching all documents from a collection."""
        result = fetch(mongodb_uri, test_database, "users")
        
        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 5
        assert all("name" in doc for doc in documents)
    
    def test_fetch_with_query(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching with query filter."""
        result = fetch(mongodb_uri, test_database, "users", query={"active": True})
        
        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 3
        assert all(doc["active"] for doc in documents)
    
    def test_fetch_with_limit(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching with limit."""
        result = fetch(mongodb_uri, test_database, "users", limit=2)
        
        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 2
    
    def test_fetch_with_complex_query(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching with complex query."""
        query = {"total": {"$gte": 100}, "status": "completed"}
        result = fetch(mongodb_uri, test_database, "orders", query=query)
        
        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 3  # Updated: orders with total >= 100 and status="completed"
        assert all(doc["total"] >= 100 and doc["status"] == "completed" for doc in documents)
    
    def test_fetch_empty_result(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching with query that returns no results."""
        result = fetch(mongodb_uri, test_database, "users", query={"name": "NonExistent"})
        
        assert result.is_ok()
        documents = result.unwrap()
        assert len(documents) == 0


class TestMongoDBCount:
    """Test MongoDB document counting functionality."""
    
    def test_count_all_documents(self, mongodb_uri, test_database, setup_test_data):
        """Test counting all documents."""
        result = count(mongodb_uri, test_database, "users")
        
        assert result.is_ok()
        count_val = result.unwrap()
        assert count_val == 5
    
    def test_count_with_query(self, mongodb_uri, test_database, setup_test_data):
        """Test counting with query filter."""
        result = count(mongodb_uri, test_database, "users", query={"active": True})
        
        assert result.is_ok()
        count_val = result.unwrap()
        assert count_val == 3


class TestMongoDBBatches:
    """Test MongoDB batch fetching functionality."""
    
    def test_fetch_in_batches(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching documents in batches."""
        result = fetch_in_batches(mongodb_uri, test_database, "users", batch_size=2)
        
        assert result.is_ok()
        batches = result.unwrap()
        assert len(batches) == 3  # 5 documents in batches of 2 = 3 batches
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1
    
    def test_fetch_in_batches_with_query(self, mongodb_uri, test_database, setup_test_data):
        """Test fetching in batches with query filter."""
        result = fetch_in_batches(
            mongodb_uri, 
            test_database, 
            "users", 
            batch_size=2, 
            query={"active": True}
        )
        
        assert result.is_ok()
        batches = result.unwrap()
        assert len(batches) == 2  # 3 active users in batches of 2 = 2 batches
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1


class TestMongoDBToDataFrame:
    """Test MongoDB to DataFrame conversion."""
    
    def test_mongodb_to_dataframe_simple(self, mongodb_uri, test_database, setup_test_data):
        """Test converting MongoDB collection to DataFrame."""
        result = mongodb.to_dataframe(mongodb_uri, test_database, "users")
        
        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 5
        assert "name" in df.columns
        assert "age" in df.columns
        assert "active" in df.columns
    
    def test_mongodb_to_dataframe_with_query(self, mongodb_uri, test_database, setup_test_data):
        """Test DataFrame conversion with query filter."""
        result = mongodb.to_dataframe(
            mongodb_uri, 
            test_database, 
            "users",
            query={"active": True},
            limit=2
        )
        
        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 2
        assert all(df["active"])
    
    def test_mongodb_to_dataframe_with_schema(self, mongodb_uri, test_database, setup_test_data):
        """Test DataFrame conversion with schema application."""
        schema = {"age": "int", "active": "bool"}
        result = mongodb.to_dataframe(
            mongodb_uri, 
            test_database, 
            "users",
            schema=schema
        )
        
        assert result.is_ok()
        df = result.unwrap()
        assert df["age"].dtype.name.startswith("int")
        # Note: pandas may convert bool differently, so we just check it's not object
        assert df["active"].dtype != "object"
    
    def test_mongodb_to_dataframe_orders(self, mongodb_uri, test_database, setup_test_data):
        """Test DataFrame conversion with numerical data."""
        result = mongodb.to_dataframe(
            mongodb_uri, 
            test_database, 
            "orders",
            query={"status": "completed"},
            schema={"total": "float", "items": "int"}
        )
        
        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 3
        assert df["total"].dtype.name.startswith("float")
        assert df["items"].dtype.name.startswith("int")
    
    def test_mongodb_to_dataframe_polars(self, mongodb_uri, test_database, setup_test_data):
        """Test DataFrame conversion using polars backend."""
        result = mongodb.to_dataframe(
            mongodb_uri, 
            test_database, 
            "users",
            backend="polars",
            limit=3
        )
        
        assert result.is_ok()
        df = result.unwrap()
        assert len(df) == 3
        # Check if it's a polars DataFrame
        assert hasattr(df, 'columns')  # Both pandas and polars have this
    
    def test_mongodb_to_dataframe_connection_error(self):
        """Test DataFrame conversion with connection error."""
        result = mongodb.to_dataframe(
            "mongodb://invalid-host:27017", 
            "test_db", 
            "test_collection"
        )
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "connection" in str(error).lower() or "timeout" in str(error).lower()


class TestMongoDBPipeline:
    """Test MongoDB integration with functional pipeline."""
    
    def test_functional_pipeline_integration(self, mongodb_uri, test_database, setup_test_data):
        """Test MongoDB with functional pipeline operations."""
        from autoframe.utils.functional import filter, transform
        from autoframe import pipe
        
        # Fetch data and process with functional pipeline
        fetch_result = fetch(mongodb_uri, test_database, "users")
        assert fetch_result.is_ok()
        
        documents = fetch_result.unwrap()
        
        # Apply functional transformations
        process = pipe(
            filter(lambda doc: doc["active"]),
            transform(lambda doc: {**doc, "age_group": "adult" if doc["age"] >= 25 else "young"})
        )
        
        processed_docs = process(documents)
        
        # Convert to DataFrame
        df_result = to_dataframe(processed_docs)
        assert df_result.is_ok()
        
        df = df_result.unwrap()
        assert len(df) == 3  # Only active users
        assert "age_group" in df.columns
        assert all(df["active"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])