"""Functional utilities for composable data processing.

This module provides simple, composable functions following logerr patterns
for functional data processing pipelines.
"""

from typing import Callable, Dict, Any, List, Optional, TypeVar
import pandas as pd
from functools import partial

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

from logerr import Result, Ok, Err
from logerr.utils import execute
from autoframe.types import (
    DataFrameResult, 
    DocumentList, 
    DataFrameCreationError,
    DataFrameType
)

T = TypeVar("T")
U = TypeVar("U")


def to_dataframe(
    documents: DocumentList, 
    backend: str = "pandas"
) -> DataFrameResult:
    """Convert documents to dataframe - simple and composable.
    
    Args:
        documents: List of document dictionaries
        backend: "pandas" or "polars"
        
    Returns:
        Result[DataFrame, DataFrameCreationError]: Success contains DataFrame, failure contains error
        
    Examples:
        Basic usage:
        
        >>> docs = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        >>> result = to_dataframe(docs)
        >>> result.is_ok()
        True
        >>> df = result.unwrap()
        >>> len(df)
        2
        
        Empty documents:
        
        >>> empty_result = to_dataframe([])
        >>> empty_result.is_ok()
        True
        >>> empty_df = empty_result.unwrap()
        >>> len(empty_df)
        0
        
        Error handling:
        
        >>> error_result = to_dataframe([{"test": 1}], backend="invalid")
        >>> error_result.is_err()
        True
    """
    # Define backend constructors - much cleaner!
    constructors = {
        "pandas": lambda docs: pd.DataFrame(docs),
        "polars": lambda docs: pl.DataFrame(docs) if POLARS_AVAILABLE else None
    }
    
    def create_df():
        if not documents:
            return constructors[backend]([])
            
        constructor = constructors.get(backend)
        if constructor is None:
            if backend == "polars" and not POLARS_AVAILABLE:
                raise DataFrameCreationError("Polars not available - install with: pip install polars")
            raise DataFrameCreationError(f"Unsupported backend: {backend}")
        
        result = constructor(documents)
        if result is None:
            raise DataFrameCreationError(f"Failed to create {backend} dataframe")
        
        return result
    
    return execute(create_df).map_err(
        lambda e: DataFrameCreationError(f"DataFrame creation failed: {str(e)}")
    )


def apply_schema(schema: Dict[str, str]) -> Callable[[DataFrameType], DataFrameType]:
    """Create a schema application function - composable transform.
    
    Args:
        schema: Field name to type mapping (supports: "int", "float", "string", "datetime", "bool")
        
    Returns:
        Function that applies schema to dataframe
        
    Examples:
        Basic schema application:
        
        >>> docs = [{"age": "30", "score": "95.5"}, {"age": "25", "score": "87.2"}]
        >>> schema = {"age": "int", "score": "float"}
        >>> result = to_dataframe(docs).map(apply_schema(schema))
        >>> df = result.unwrap()
        >>> df["age"].dtype.name.startswith("int")
        True
        >>> df["score"].dtype.name.startswith("float")
        True
        
        Functional composition:
        
        >>> from autoframe.utils.functional import pipe, transform_documents
        >>> process = pipe(
        ...     transform_documents(lambda d: {**d, "processed": True}),
        ...     lambda docs: to_dataframe(docs).map(apply_schema({"age": "int"})).unwrap()
        ... )
    """
    def apply_to_df(df: DataFrameType) -> DataFrameType:
        if isinstance(df, pd.DataFrame):
            return _apply_pandas_schema(df, schema)
        elif POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
            return _apply_polars_schema(df, schema)
        return df
    
    return apply_to_df


def transform_documents(
    transform_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
) -> Callable[[DocumentList], DocumentList]:
    """Create a document transformation function.
    
    Args:
        transform_fn: Function to apply to each document
        
    Returns:
        Function that transforms document list
        
    Examples:
        >>> add_timestamp = lambda doc: {**doc, "processed_at": "2024-01-01"}
        >>> transform = transform_documents(add_timestamp)
        >>> docs = [{"name": "Alice"}, {"name": "Bob"}] 
        >>> transformed_docs = transform(docs)
        >>> transformed_docs[0]["processed_at"]
        '2024-01-01'
    """
    return lambda docs: [transform_fn(doc) for doc in docs]


def filter_documents(
    predicate: Callable[[Dict[str, Any]], bool]
) -> Callable[[DocumentList], DocumentList]:
    """Create a document filtering function.
    
    Args:
        predicate: Function that returns True for documents to keep
        
    Returns:
        Function that filters document list
        
    Examples:
        >>> docs = [{"name": "Alice", "active": True}, {"name": "Bob", "active": False}]
        >>> active_only = filter_documents(lambda doc: doc.get("active", True))
        >>> filtered_docs = active_only(docs)
        >>> len(filtered_docs)
        1
        >>> filtered_docs[0]["name"]
        'Alice'
    """
    return lambda docs: [doc for doc in docs if predicate(doc)]


def validate_columns(required_cols: List[str]) -> Callable[[DataFrameResult], DataFrameResult]:
    """Create a column validation function.
    
    Args:
        required_cols: List of required column names
        
    Returns:
        Function that validates dataframe columns
        
    Examples:
        >>> validate = validate_columns(["name", "age"])
        >>> docs = [{"name": "Alice", "age": 30}]
        >>> df_result = to_dataframe(docs)
        >>> validated_result = validate(df_result)
        >>> validated_result.is_ok()
        True
    """
    def validate_df(df_result: DataFrameResult) -> DataFrameResult:
        return df_result.then(lambda df: _check_columns(df, required_cols))
    
    return validate_df


def limit_documents(count: int) -> Callable[[DocumentList], DocumentList]:
    """Create a document limiting function.
    
    Args:
        count: Maximum number of documents
        
    Returns:
        Function that limits document list
        
    Examples:
        >>> limit_100 = limit_documents(100)
        >>> docs = [{"id": i} for i in range(200)]
        >>> limited_docs = limit_100(docs)
        >>> len(limited_docs)
        100
    """
    return lambda docs: docs[:count]


def pipe(*functions: Callable[[T], T]) -> Callable[[T], T]:
    """Compose functions in a pipeline - the heart of functional composition.
    
    This function allows you to chain multiple transformations together in a 
    readable, left-to-right manner, following functional programming principles.
    
    Args:
        *functions: Functions to compose, applied left-to-right
        
    Returns:
        Composed function that applies all transformations in sequence
        
    Examples:
        Document processing pipeline:
        
        >>> docs = [
        ...     {"name": "Alice", "age": 30, "active": True},
        ...     {"name": "Bob", "age": 17, "active": True}, 
        ...     {"name": "Charlie", "age": 25, "active": False}
        ... ]
        >>> process = pipe(
        ...     filter_documents(lambda d: d["active"]),
        ...     filter_documents(lambda d: d["age"] >= 18),
        ...     transform_documents(lambda d: {**d, "processed": True}),
        ...     limit_documents(10)
        ... )
        >>> result_docs = process(docs)
        >>> len(result_docs)
        1
        >>> result_docs[0]["name"]
        'Alice'
        >>> result_docs[0]["processed"]
        True
        
        With dataframe conversion:
        
        >>> full_pipeline = pipe(
        ...     filter_documents(lambda d: d["active"]),
        ...     transform_documents(lambda d: {**d, "category": "user"})
        ... )
        >>> processed_docs = full_pipeline(docs)
        >>> df_result = to_dataframe(processed_docs)
        >>> df = df_result.unwrap()
        >>> "category" in df.columns
        True
    """
    def composed(value: T) -> T:
        for fn in functions:
            value = fn(value)
        return value
    return composed


# Private helper functions
def _apply_pandas_schema(df: pd.DataFrame, schema: Dict[str, str]) -> pd.DataFrame:
    """Apply schema to pandas DataFrame."""
    type_mapping = {
        "int": "int64",
        "float": "float64", 
        "string": "object",
        "datetime": "datetime64[ns]",
        "bool": "bool"
    }
    
    for field, field_type in schema.items():
        if field in df.columns:
            pandas_type = type_mapping.get(field_type, "object")
            try:
                if pandas_type == "datetime64[ns]":
                    df[field] = pd.to_datetime(df[field], errors="coerce")
                else:
                    df[field] = df[field].astype(pandas_type, errors="ignore")
            except Exception:
                pass  # Keep original type if conversion fails
    
    return df


def _apply_polars_schema(df: "pl.DataFrame", schema: Dict[str, str]) -> "pl.DataFrame":
    """Apply schema to polars DataFrame."""
    if not POLARS_AVAILABLE:
        return df
        
    type_mapping = {
        "int": pl.Int64,
        "float": pl.Float64,
        "string": pl.Utf8,
        "datetime": pl.Datetime,
        "bool": pl.Boolean
    }
    
    for field, field_type in schema.items():
        if field in df.columns:
            polars_type = type_mapping.get(field_type)
            if polars_type:
                try:
                    df = df.with_columns(pl.col(field).cast(polars_type))
                except Exception:
                    pass  # Keep original type if cast fails
    
    return df


def _check_columns(df: DataFrameType, required_cols: List[str]) -> DataFrameResult:
    """Check if dataframe has required columns."""
    if isinstance(df, pd.DataFrame):
        missing = set(required_cols) - set(df.columns)
    elif POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
        missing = set(required_cols) - set(df.columns)
    else:
        missing = set()
        
    if missing:
        return Err(DataFrameCreationError(f"Missing required columns: {missing}"))
    
    return Ok(df)