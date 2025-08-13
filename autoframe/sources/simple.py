"""Simple, composable data source functions.

This module provides simple functions for data fetching that compose well
in functional pipelines, following logerr patterns.
"""

from typing import Optional, Dict, Any, List, Callable
from functools import partial
import pymongo
from tenacity import retry, stop_after_attempt, wait_exponential

from logerr import Result, Ok, Err
from logerr.utils import execute
from autoframe.types import DataSourceResult, DocumentList, DataSourceError, QueryDict


def connect_mongodb(connection_string: str) -> Result[pymongo.MongoClient, DataSourceError]:
    """Connect to MongoDB - simple function.
    
    Args:
        connection_string: MongoDB connection string
        
    Returns:
        Result[MongoClient, DataSourceError]
        
    Examples:
        >>> client_result = connect_mongodb("mongodb://localhost:27017")
        >>> client = client_result.unwrap()
    """
    def connect():
        client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')  # Test connection
        return client
    
    return execute(connect).map_err(
        lambda e: DataSourceError(f"MongoDB connection failed: {str(e)}")
    )


def fetch_documents(
    connection_string: str,
    database: str, 
    collection: str,
    query: Optional[QueryDict] = None,
    limit: Optional[int] = None
) -> DataSourceResult[DocumentList]:
    """Fetch documents from MongoDB - simple and composable.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name
        collection: Collection name
        query: Optional query filter
        limit: Optional result limit
        
    Returns:
        Result[List[Dict], DataSourceError]
        
    Examples:
        >>> docs = fetch_documents(
        ...     "mongodb://localhost:27017", 
        ...     "mydb", 
        ...     "users",
        ...     query={"active": True},
        ...     limit=100
        ... )
    """
    return (
        connect_mongodb(connection_string)
        .and_then(lambda client: _query_collection(client, database, collection, query, limit))
    )


def count_documents(
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
        .and_then(lambda client: _count_collection(client, database, collection, query))
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
    return partial(fetch_documents, connection_string, database, collection)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch_documents_with_retry(
    connection_string: str,
    database: str,
    collection: str,
    query: Optional[QueryDict] = None,
    limit: Optional[int] = None
) -> DataSourceResult[DocumentList]:
    """Fetch documents with automatic retry logic.
    
    Same as fetch_documents but with built-in retry for transient failures.
    """
    return fetch_documents(connection_string, database, collection, query, limit)


def fetch_in_batches(
    connection_string: str,
    database: str,
    collection: str,
    batch_size: int = 1000,
    query: Optional[QueryDict] = None
) -> Result[List[DocumentList], DataSourceError]:
    """Fetch documents in batches for large datasets.
    
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
    def fetch_batches():
        client = connect_mongodb(connection_string).unwrap()
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
    
    return execute(fetch_batches).map_err(
        lambda e: DataSourceError(f"Batch fetch failed: {str(e)}")
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