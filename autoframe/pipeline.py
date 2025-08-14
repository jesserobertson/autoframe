"""Composable data processing pipelines.

This module provides high-level composable functions for creating 
data processing pipelines in the logerr functional style.
"""

from typing import Callable, Dict, Any, List, Optional
from functools import partial

from logerr import Result
from autoframe.types import DataFrameResult, DocumentList, DataSourceResult
from autoframe.sources.simple import fetch_documents, fetch_documents_with_retry, create_fetcher
from autoframe.utils.functional import (
    to_dataframe,
    apply_schema, 
    transform_documents,
    filter_documents,
    limit_documents,
    validate_columns,
    pipe
)


def mongodb_to_dataframe(
    connection_string: str,
    database: str,
    collection: str,
    query: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    schema: Optional[Dict[str, str]] = None,
    backend: str = "pandas"
) -> DataFrameResult:
    """Simple MongoDB to DataFrame pipeline.
    
    Args:
        connection_string: MongoDB connection string
        database: Database name
        collection: Collection name
        query: Optional query filter
        limit: Optional result limit
        schema: Optional schema for type conversion
        backend: "pandas" or "polars"
        
    Returns:
        Result[DataFrame, Error]
        
    Examples:
        >>> df_result = mongodb_to_dataframe(
        ...     "mongodb://localhost:27017",
        ...     "mydb", 
        ...     "users",
        ...     query={"active": True},
        ...     limit=1000,
        ...     schema={"age": "int", "created_at": "datetime"}
        ... )
        >>> df = df_result.unwrap()
    """
    result = fetch_documents(connection_string, database, collection, query, limit)
    
    df_result = result.then(partial(to_dataframe, backend=backend))
    
    if schema:
        df_result = df_result.map(apply_schema(schema))
    
    return df_result


def create_pipeline(
    fetch_fn: Callable[[], DataSourceResult[DocumentList]]
) -> "DataPipeline":
    """Create a composable data processing pipeline.
    
    Args:
        fetch_fn: Function that fetches documents
        
    Returns:
        DataPipeline object for method chaining
        
    Examples:
        >>> fetch_users = lambda: fetch_documents("mongodb://localhost", "db", "users")
        >>> result = (
        ...     create_pipeline(fetch_users) 
        ...     .filter(lambda doc: doc["active"])
        ...     .transform(lambda doc: {**doc, "processed": True})
        ...     .limit(100)
        ...     .to_dataframe()
        ...     .apply_schema({"age": "int"})
        ...     .execute()
        ... )
    """
    return DataPipeline(fetch_fn)


class DataPipeline:
    """Composable data pipeline for method chaining.
    
    This provides a fluent interface while keeping individual functions simple.
    """
    
    def __init__(self, fetch_fn: Callable[[], DataSourceResult[DocumentList]]):
        self.fetch_fn = fetch_fn
        self.transforms = []
        self.df_transforms = []
        self.target_backend = "pandas"
        self.target_schema = None
    
    def filter(self, predicate: Callable[[Dict[str, Any]], bool]) -> "DataPipeline":
        """Add document filtering to pipeline."""
        self.transforms.append(filter_documents(predicate))
        return self
    
    def transform(self, transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> "DataPipeline":
        """Add document transformation to pipeline."""
        self.transforms.append(transform_documents(transform_fn))
        return self
    
    def limit(self, count: int) -> "DataPipeline":
        """Add document limiting to pipeline."""
        self.transforms.append(limit_documents(count))
        return self
    
    def to_dataframe(self, backend: str = "pandas") -> "DataPipeline":
        """Convert to dataframe in pipeline."""
        self.target_backend = backend
        return self
    
    def apply_schema(self, schema: Dict[str, str]) -> "DataPipeline":
        """Apply schema to dataframe in pipeline."""
        self.target_schema = schema
        return self
    
    def validate(self, required_columns: List[str]) -> "DataPipeline":
        """Add column validation to pipeline.""" 
        self.df_transforms.append(validate_columns(required_columns))
        return self
    
    def execute(self) -> DataFrameResult:
        """Execute the complete pipeline.
        
        Returns:
            Result[DataFrame, Error]
        """
        # Fetch documents
        docs_result = self.fetch_fn()
        
        # Apply document transforms
        if self.transforms:
            combined_transform = pipe(*self.transforms)
            docs_result = docs_result.map(combined_transform)
        
        # Convert to dataframe
        df_result = docs_result.then(
            partial(to_dataframe, backend=self.target_backend)
        )
        
        # Apply schema if specified
        if self.target_schema:
            df_result = df_result.map(apply_schema(self.target_schema))
        
        # Apply dataframe transforms
        for df_transform in self.df_transforms:
            df_result = df_transform(df_result)
        
        return df_result


# Convenience functions for common patterns
def fetch_and_process(
    connection_string: str,
    database: str,
    collection: str,
    *,
    query: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    transform_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    schema: Optional[Dict[str, str]] = None,
    backend: str = "pandas"
) -> DataFrameResult:
    """Fetch and process documents in a single call.
    
    A more imperative interface for those who prefer it over method chaining.
    
    Examples:
        >>> result = fetch_and_process(
        ...     "mongodb://localhost", "db", "users",
        ...     query={"active": True},
        ...     filter_fn=lambda doc: doc["age"] >= 18,
        ...     transform_fn=lambda doc: {**doc, "adult": True},
        ...     schema={"age": "int"},
        ...     limit=1000
        ... )
    """
    fetch_fn = lambda: fetch_documents(connection_string, database, collection, query, limit)
    
    pipeline = create_pipeline(fetch_fn)
    
    if filter_fn:
        pipeline = pipeline.filter(filter_fn)
    
    if transform_fn:
        pipeline = pipeline.transform(transform_fn)
    
    pipeline = pipeline.to_dataframe(backend)
    
    if schema:
        pipeline = pipeline.apply_schema(schema)
    
    return pipeline.execute()


def quick_dataframe(
    connection_string: str, 
    database: str, 
    collection: str
) -> DataFrameResult:
    """Quickly create a dataframe from a MongoDB collection.
    
    For when you just want a simple, no-frills dataframe.
    
    Examples:
        >>> df = quick_dataframe("mongodb://localhost", "mydb", "users").unwrap()
    """
    return mongodb_to_dataframe(connection_string, database, collection)