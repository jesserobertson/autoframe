"""MongoDB-specific data processing functions.

This module provides MongoDB-specific functions for data extraction and DataFrame creation.
All MongoDB functionality is consolidated here for simplicity.
"""

from typing import Optional, Dict, Any, List, Callable
from functools import partial
import pymongo

from logerr import Result, Ok, Err
from logerr.utils import execute
from autoframe.types import DataFrameResult, DataSourceResult, DocumentList, DataSourceError, QueryDict
from autoframe.quality import log_result_failure, log_conversion_operation
from autoframe.utils.functional import to_dataframe as _to_dataframe, apply_schema
from autoframe.utils.retry import with_database_retry


def to_dataframe(
    connection_string: str,
    database: str,
    collection: str,
    query: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    schema: Optional[Dict[str, str]] = None,
    backend: str = "pandas"
) -> DataFrameResult:
    """Convert MongoDB collection to DataFrame.
    
    This is the simplest way to get data from MongoDB into a DataFrame with
    optional filtering, limiting, and type conversion.
    
    Args:
        connection_string: MongoDB connection string (e.g., "mongodb://localhost:27017")
        database: Database name
        collection: Collection name
        query: Optional MongoDB query filter (e.g., {"active": True})
        limit: Optional result limit (e.g., 1000)
        schema: Optional schema for type conversion (e.g., {"age": "int"})
        backend: "pandas" or "polars"
        
    Returns:
        Result[DataFrame, Error]: Success contains DataFrame, failure contains error message
        
    Examples:
        Basic usage:
        
        >>> import autoframe.mongodb as mongodb
        >>> # Note: These examples assume a running MongoDB instance
        >>> # df_result = mongodb.to_dataframe(
        >>> #     "mongodb://localhost:27017", 
        >>> #     "ecommerce", 
        >>> #     "orders"
        >>> # )
        >>> # df = df_result.unwrap()
        
        With filtering and schema:
        
        >>> # df_result = mongodb.to_dataframe(
        >>> #     "mongodb://localhost:27017",
        >>> #     "ecommerce", 
        >>> #     "orders",
        >>> #     query={"status": "completed", "total": {"$gt": 100}},
        >>> #     limit=500,
        >>> #     schema={"total": "float", "created_at": "datetime"}
        >>> # )
        >>> # if df_result.is_ok():
        >>> #     df = df_result.unwrap()
        >>> #     print(f"Retrieved {len(df)} orders")
        
        Error handling:
        
        >>> # result = mongodb.to_dataframe("invalid://connection", "db", "coll")
        >>> # if result.is_err():
        >>> #     print(f"Connection failed: {result.unwrap_err()}")
    """
    # Fetch documents with quality logging
    result = fetch(connection_string, database, collection, query, limit)
    logged_result = log_result_failure(result, "mongodb_fetch", {
        "database": database,
        "collection": collection, 
        "query": query,
        "limit": limit
    })
    
    # Convert to dataframe with logging
    df_result = logged_result.then(partial(_to_dataframe, backend=backend))
    df_result = log_conversion_operation(
        df_result, 
        backend, 
        len(logged_result.unwrap_or([]))
    )
    
    # Apply schema if provided
    if schema:
        df_result = df_result.map(apply_schema(schema))
        df_result = log_result_failure(df_result, "schema_application", {
            "schema": schema,
            "backend": backend
        })
    
    return df_result


# Core MongoDB functions (moved from sources/simple.py)

def connect_mongodb(connection_string: str) -> Result[pymongo.MongoClient, DataSourceError]:
    """Connect to MongoDB with automatic retry logic.
    
    Args:
        connection_string: MongoDB connection string
        
    Returns:
        Result[MongoClient, DataSourceError]
        
    Examples:
        >>> client_result = connect_mongodb("mongodb://localhost:27017")
        >>> client = client_result.unwrap()
    """
    @with_database_retry
    def connect():
        client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')  # Test connection
        return client
    
    return connect()


def fetch(
    connection_string: str,
    database: str, 
    collection: str,
    query: Optional[QueryDict] = None,
    limit: Optional[int] = None
) -> DataSourceResult[DocumentList]:
    """Fetch documents from MongoDB with retry logic.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name
        collection: Collection name
        query: Optional query filter
        limit: Optional result limit
        
    Returns:
        Result[List[Dict], DataSourceError]
        
    Examples:
        >>> docs = fetch(
        ...     "mongodb://localhost:27017", 
        ...     "mydb", 
        ...     "users",
        ...     query={"active": True},
        ...     limit=100
        ... )
    """
    return (
        connect_mongodb(connection_string)
        .then(lambda client: _query_collection(client, database, collection, query, limit))
    )


def count(
    connection_string: str,
    database: str,
    collection: str, 
    query: Optional[QueryDict] = None
) -> DataSourceResult[int]:
    """Count documents in MongoDB collection.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name
        collection: Collection name
        query: Optional query filter
        
    Returns:
        Result[int, DataSourceError]
    """
    return (
        connect_mongodb(connection_string)
        .then(lambda client: _count_collection(client, database, collection, query))
    )


def create_fetcher(
    connection_string: str,
    database: str,
    collection: str
) -> Callable[[Optional[QueryDict], Optional[int]], DataSourceResult[DocumentList]]:
    """Create a specialized document fetcher function.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name  
        collection: Collection name
        
    Returns:
        Function that fetches documents with query and limit
        
    Examples:
        >>> fetch_users = create_fetcher("mongodb://localhost", "mydb", "users")
        >>> active_users = fetch_users({"active": True}, 100)
        >>> all_users = fetch_users(None, None)
    """
    return partial(fetch, connection_string, database, collection)


def fetch_in_batches(
    connection_string: str,
    database: str,
    collection: str,
    batch_size: int = 1000,
    query: Optional[QueryDict] = None
) -> Result[List[DocumentList], DataSourceError]:
    """Fetch documents in batches with retry logic for large datasets.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name
        collection: Collection name
        batch_size: Number of documents per batch
        query: Optional query filter
        
    Returns:
        Result[List[List[Dict]], DataSourceError]: List of batches
        
    Examples:
        >>> batches_result = fetch_in_batches("mongodb://localhost", "db", "coll", 500)
        >>> for batch in batches_result.unwrap():
        ...     df = to_dataframe(batch).unwrap()
        ...     # Process each batch
    """
    return (
        connect_mongodb(connection_string)
        .then(lambda client: _fetch_batches_from_client_with_retry(client, database, collection, batch_size, query))
    )


# Private helper functions

def _query_collection(
    client: pymongo.MongoClient,
    database: str,
    collection: str,
    query: Optional[QueryDict],
    limit: Optional[int]
) -> DataSourceResult[DocumentList]:
    """Query a MongoDB collection."""
    def query_docs():
        coll = client[database][collection]
        cursor = coll.find(query or {})
        
        if limit:
            cursor = cursor.limit(limit)
            
        documents = list(cursor)
        client.close()
        return documents
    
    return execute(query_docs).map_err(
        lambda e: DataSourceError(f"Query failed: {str(e)}")
    )


def _count_collection(
    client: pymongo.MongoClient,
    database: str,
    collection: str,
    query: Optional[QueryDict]
) -> DataSourceResult[int]:
    """Count documents in a MongoDB collection."""
    def count_docs():
        coll = client[database][collection]
        count = coll.count_documents(query or {})
        client.close()
        return count
    
    return execute(count_docs).map_err(
        lambda e: DataSourceError(f"Count failed: {str(e)}")
    )


def _fetch_batches_from_client_with_retry(
    client: pymongo.MongoClient,
    database: str,
    collection: str,
    batch_size: int,
    query: Optional[QueryDict]
) -> Result[List[DocumentList], DataSourceError]:
    """Fetch documents in batches from an established client connection with retry."""
    @with_database_retry  
    def fetch_batches():
        collection_obj = client[database][collection]
        
        total_docs = collection_obj.count_documents(query or {})
        batches = []
        
        for skip in range(0, total_docs, batch_size):
            cursor = collection_obj.find(query or {}).skip(skip).limit(batch_size)
            batch = list(cursor)
            if batch:
                batches.append(batch)
        
        client.close()
        return batches
    
    return fetch_batches()