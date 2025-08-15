"""MongoDB-specific data processing functions.

This module provides MongoDB-specific functions for data extraction and DataFrame creation.
All MongoDB functionality is consolidated here for simplicity.
"""

from collections.abc import Callable
from functools import partial
from typing import Any

import pymongo
from logerr import Result  # type: ignore
from logerr.utils import execute  # type: ignore

from autoframe.auth import MongoConnectionConfig, validate_connection_string
from autoframe.quality import log_conversion_operation, log_result_failure
from autoframe.types import (
    DataFrameResult,
    DataSourceError,
    DataSourceResult,
    DocumentList,
    QueryDict,
)
from autoframe.utils.functional import apply_schema
from autoframe.utils.functional import to_dataframe as _to_dataframe
from autoframe.utils.retry import with_database_retry


def to_dataframe(
    connection: str | MongoConnectionConfig,
    database: str,
    collection: str,
    query: dict[str, Any] | None = None,
    limit: int | None = None,
    schema: dict[str, str] | None = None,
    backend: str = "pandas"
) -> DataFrameResult:
    """Convert MongoDB collection to DataFrame.

    This is the simplest way to get data from MongoDB into a DataFrame with
    optional filtering, limiting, and type conversion. Supports both connection
    strings and secure authentication configurations.

    Args:
        connection: MongoDB connection string or MongoConnectionConfig
        database: Database name
        collection: Collection name
        query: Optional MongoDB query filter (e.g., {"active": True})
        limit: Optional result limit (e.g., 1000)
        schema: Optional schema for type conversion (e.g., {"age": "int"})
        backend: "pandas" or "polars"

    Returns:
        Result[DataFrame, Error]: Success contains DataFrame, failure contains error message

    Examples:
        Basic usage with connection string:

        >>> import autoframe.mongodb as mongodb
        >>> # Note: These examples assume a running MongoDB instance
        >>> # df_result = mongodb.to_dataframe(
        >>> #     "mongodb://localhost:27017",
        >>> #     "ecommerce",
        >>> #     "orders"
        >>> # )

        With authentication configuration:

        >>> from autoframe.auth import create_authenticated_config
        >>> # config = create_authenticated_config(
        >>> #     "remote-mongo.example.com",
        >>> #     "myuser",
        >>> #     "mypassword",
        >>> #     database="ecommerce",
        >>> #     ssl=True
        >>> # )
        >>> # df_result = mongodb.to_dataframe(config, "ecommerce", "orders")

        With filtering and schema:

        >>> # df_result = mongodb.to_dataframe(
        >>> #     "mongodb://localhost:27017",
        >>> #     "ecommerce",
        >>> #     "orders",
        >>> #     query={"status": "completed", "total": {"$gt": 100}},
        >>> #     limit=500,
        >>> #     schema={"total": "float", "created_at": "datetime"}
        >>> # )

        Error handling with pattern matching:

        >>> # match mongodb.to_dataframe("invalid://connection", "db", "coll"):
        >>> #     case Ok(df):
        >>> #         print(f"Success: {len(df)} rows")
        >>> #     case Err(error):
        >>> #         print(f"Connection failed: {error}")
    """
    # Resolve connection to string
    connection_string = _resolve_connection(connection)

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

def connect(connection: str | MongoConnectionConfig) -> Result[pymongo.MongoClient, DataSourceError]:
    """Connect to MongoDB with automatic retry logic.

    Args:
        connection: MongoDB connection string or MongoConnectionConfig

    Returns:
        Result[MongoClient, DataSourceError]

    Examples:
        >>> client_result = connect("mongodb://localhost:27017")
        >>> client = client_result.unwrap()

        >>> from autoframe.auth import create_authenticated_config
        >>> config = create_authenticated_config("host", "user", "pass")
        >>> client_result = connect(config)
    """
    connection_string = _resolve_connection(connection)

    @with_database_retry
    def connect_impl() -> pymongo.MongoClient:
        client: pymongo.MongoClient = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")  # Test connection
        return client

    return connect_impl()


def fetch(
    connection: str | MongoConnectionConfig,
    database: str,
    collection: str,
    query: QueryDict | None = None,
    limit: int | None = None
) -> DataSourceResult[DocumentList]:
    """Fetch documents from MongoDB with retry logic.

    Args:
        connection: MongoDB connection string or MongoConnectionConfig
        database: Database name
        collection: Collection name
        query: Optional query filter
        limit: Optional result limit

    Returns:
        Result[list[dict], DataSourceError]

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
        connect(connection)
        .then(lambda client: _query_collection(client, database, collection, query, limit))
    )


def count(
    connection: str | MongoConnectionConfig,
    database: str,
    collection: str,
    query: QueryDict | None = None
) -> DataSourceResult[int]:
    """Count documents in MongoDB collection.

    Args:
        connection: MongoDB connection string or MongoConnectionConfig
        database: Database name
        collection: Collection name
        query: Optional query filter

    Returns:
        Result[int, DataSourceError]
    """
    return (
        connect(connection)
        .then(lambda client: _count_collection(client, database, collection, query))
    )


def create_fetcher(
    connection: str | MongoConnectionConfig,
    database: str,
    collection: str
) -> Callable[[QueryDict | None, int | None], DataSourceResult[DocumentList]]:
    """Create a specialized document fetcher function.

    Args:
        connection: MongoDB connection string or MongoConnectionConfig
        database: Database name
        collection: Collection name

    Returns:
        Function that fetches documents with query and limit

    Examples:
        >>> fetch_users = create_fetcher("mongodb://localhost", "mydb", "users")
        >>> active_users = fetch_users({"active": True}, 100)
        >>> all_users = fetch_users(None, None)
    """
    return partial(fetch, connection, database, collection)


def fetch_in_batches(
    connection: str | MongoConnectionConfig,
    database: str,
    collection: str,
    batch_size: int = 1000,
    query: QueryDict | None = None
) -> Result[list[DocumentList], DataSourceError]:
    """Fetch documents in batches with retry logic for large datasets.

    Args:
        connection: MongoDB connection string or MongoConnectionConfig
        database: Database name
        collection: Collection name
        batch_size: Number of documents per batch
        query: Optional query filter

    Returns:
        Result[list[list[dict]], DataSourceError]: List of batches

    Examples:
        >>> batches_result = fetch_in_batches("mongodb://localhost", "db", "coll", 500)
        >>> for batch in batches_result.unwrap():
        ...     df = to_dataframe(batch).unwrap()
        ...     # Process each batch
    """
    return (
        connect(connection)
        .then(lambda client: _fetch_batches_from_client_with_retry(client, database, collection, batch_size, query))
    )


# Private helper functions

def _resolve_connection(connection: str | MongoConnectionConfig) -> str:
    """Resolve connection to a connection string.

    Args:
        connection: Either a connection string or MongoConnectionConfig

    Returns:
        MongoDB connection string

    Raises:
        DataSourceError: If connection string validation fails
    """
    if isinstance(connection, str):
        # Validate connection string format
        validation_result = validate_connection_string(connection)
        if validation_result.is_err():
            raise DataSourceError(f"Invalid connection string: {validation_result.unwrap_err()}")
        return connection

    # It's a MongoConnectionConfig, build connection string
    return connection.build_connection_string()

def _query_collection(
    client: pymongo.MongoClient,
    database: str,
    collection: str,
    query: QueryDict | None,
    limit: int | None
) -> DataSourceResult[DocumentList]:
    """Query a MongoDB collection."""
    def query_collection() -> DocumentList:
        coll = client[database][collection]
        cursor = coll.find(query or {})

        if limit:
            cursor = cursor.limit(limit)

        documents = list(cursor)
        client.close()
        return documents

    return execute(query_collection).map_err(
        lambda e: DataSourceError(f"Query failed: {e!s}")
    )


def _count_collection(
    client: pymongo.MongoClient,
    database: str,
    collection: str,
    query: QueryDict | None
) -> DataSourceResult[int]:
    """Count documents in a MongoDB collection."""
    def count_collection() -> int:
        coll = client[database][collection]
        count = coll.count_documents(query or {})
        client.close()
        return count

    return execute(count_collection).map_err(
        lambda e: DataSourceError(f"Count failed: {e!s}")
    )


def _fetch_batches_from_client_with_retry(
    client: pymongo.MongoClient,
    database: str,
    collection: str,
    batch_size: int,
    query: QueryDict | None
) -> Result[list[DocumentList], DataSourceError]:
    """Fetch documents in batches from an established client connection with retry."""
    @with_database_retry
    def fetch_batches() -> list[DocumentList]:
        collection_obj = client[database][collection]

        total_docs = collection_obj.count_documents(query or {})
        batches: list[DocumentList] = []

        for skip in range(0, total_docs, batch_size):
            cursor = collection_obj.find(query or {}).skip(skip).limit(batch_size)
            batch = list(cursor)
            if batch:
                batches.append(batch)

        client.close()
        return batches

    return fetch_batches()
