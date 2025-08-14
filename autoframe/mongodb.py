"""MongoDB-specific data processing functions.

This module provides MongoDB-specific functions for data extraction and DataFrame creation.
"""

from typing import Optional, Dict, Any
from functools import partial

from logerr import Result
from autoframe.types import DataFrameResult
from autoframe.sources.simple import fetch
from autoframe.quality import log_result_failure, log_conversion_operation
from autoframe.utils.functional import to_dataframe as _to_dataframe, apply_schema


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