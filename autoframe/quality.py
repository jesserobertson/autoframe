"""Simple quality logging utilities for Result-driven data processing.

This module provides lightweight logging utilities that integrate with Result types
to capture basic information about data processing failures and missing data,
following patterns similar to logerr.recipes.
"""

from typing import Dict, Any, List, Optional, Callable, TypeVar, Union
from functools import wraps
import json

from loguru import logger
from logerr import Result, Ok, Err
from logerr.utils import execute

from autoframe.types import DocumentList, DataFrameResult, DataSourceResult

T = TypeVar('T')
E = TypeVar('E')


def log_result_failure(result: Result[T, E], operation: str, context: Optional[Dict[str, Any]] = None) -> Result[T, E]:
    """Log information when a Result contains an error.
    
    Args:
        result: The Result to inspect
        operation: Description of the operation that produced this Result
        context: Optional additional context to log
        
    Returns:
        The original Result unchanged (for chaining)
        
    Examples:
        >>> from autoframe.sources.simple import fetch
        >>> from logerr import Err
        >>> from autoframe.types import DataSourceError
        >>> 
        >>> # Example with a failing result
        >>> result = Err(DataSourceError("Connection failed"))
        >>> logged_result = log_result_failure(result, "document_fetch", {"collection": "users"})
        >>> logged_result.is_err()
        True
    """
    if result.is_err():
        error = result.unwrap_err()
        log_context = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(context or {})
        }
        
        logger.warning(f"Operation failed: {operation}", **log_context)
    
    return result


def log_document_completeness(documents: DocumentList, expected_fields: List[str], 
                            operation: str = "document_processing") -> DocumentList:
    """Log completeness information about document fields.
    
    Args:
        documents: List of documents to analyze
        expected_fields: List of field names that should be present
        operation: Description of the operation for logging context
        
    Returns:
        The original documents unchanged (for chaining)
        
    Examples:
        >>> docs = [{"name": "Alice", "age": 30}, {"name": "Bob"}]  # Missing age in second doc
        >>> logged_docs = log_document_completeness(docs, ["name", "age", "email"], "user_fetch")
        >>> # Logs missing field statistics
    """
    if not documents:
        logger.info(f"No documents to analyze for {operation}")
        return documents
    
    total_docs = len(documents)
    field_stats = {}
    
    # Calculate completeness for each expected field
    for field in expected_fields:
        present_count = sum(1 for doc in documents if field in doc and doc[field] is not None)
        missing_count = total_docs - present_count
        completeness_pct = (present_count / total_docs) * 100
        
        field_stats[field] = {
            "present": present_count,
            "missing": missing_count,
            "completeness_pct": completeness_pct
        }
    
    # Log overall completeness
    overall_completeness = sum(
        stats["completeness_pct"] for stats in field_stats.values()
    ) / len(expected_fields) if expected_fields else 100
    
    log_context = {
        "operation": operation,
        "total_documents": total_docs,
        "expected_fields": expected_fields,
        "overall_completeness_pct": round(overall_completeness, 1),
        "field_completeness": {k: round(v["completeness_pct"], 1) for k, v in field_stats.items()}
    }
    
    if overall_completeness < 95:  # Log if completeness is concerning
        logger.warning(f"Document completeness below 95% for {operation}", **log_context)
    else:
        logger.info(f"Document completeness check for {operation}", **log_context)
    
    # Log details about missing fields if significant
    for field, stats in field_stats.items():
        if stats["missing"] > 0:
            logger.debug(
                f"Field '{field}' missing in {stats['missing']}/{total_docs} documents",
                operation=operation,
                field=field,
                missing_count=stats["missing"],
                completeness_pct=stats["completeness_pct"]
            )
    
    return documents


def log_dataframe_creation_stats(df_result: DataFrameResult, source_info: Dict[str, Any]) -> DataFrameResult:
    """Log statistics about DataFrame creation results.
    
    Args:
        df_result: Result from DataFrame creation
        source_info: Information about the data source
        
    Returns:
        The original DataFrameResult unchanged (for chaining)
    """
    if df_result.is_ok():
        df = df_result.unwrap()
        
        # Basic DataFrame stats
        stats = {
            "operation": "dataframe_creation",
            "source": source_info,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
        }
        
        # Add memory usage info if available (pandas has it, polars doesn't)
        if hasattr(df, 'memory_usage'):
            stats["memory_usage_mb"] = round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        else:
            stats["memory_usage_mb"] = "unknown"
        
        # Check for common data quality indicators
        if hasattr(df, 'isnull'):  # pandas
            null_counts = df.isnull().sum()
            stats["null_counts"] = {col: int(count) for col, count in null_counts.items() if count > 0}
            stats["total_nulls"] = int(null_counts.sum())
        
        logger.info("DataFrame created successfully", **stats)
        
        # Log warnings for potential issues
        if len(df) == 0:
            logger.warning("DataFrame is empty", **source_info)
        elif stats.get("total_nulls", 0) > len(df) * 0.1:  # More than 10% nulls
            logger.warning("High null value percentage in DataFrame", **stats)
        
    else:
        # Log DataFrame creation failure
        log_result_failure(df_result, "dataframe_creation", source_info)
    
    return df_result


def track_pipeline_operation(operation_name: str, context: Optional[Dict[str, Any]] = None):
    """Decorator to track pipeline operations with automatic logging.
    
    Args:
        operation_name: Name of the operation for logging
        context: Additional context to include in logs
        
    Returns:
        Decorator function
        
    Examples:
        >>> @track_pipeline_operation("user_data_fetch", {"source": "mongodb"})
        ... def fetch_user_data():
        ...     return fetch_documents("mongodb://localhost", "db", "users")
    """
    def decorator(func: Callable[[], Result[T, E]]) -> Callable[[], Result[T, E]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Result[T, E]:
            start_context = {
                "operation": operation_name,
                "function": func.__name__,
                **(context or {})
            }
            
            logger.info(f"Starting operation: {operation_name}", **start_context)
            
            result = execute(lambda: func(*args, **kwargs))
            
            # Log the result
            if result.is_ok():
                logger.info(f"Operation completed successfully: {operation_name}", **start_context) 
            else:
                log_result_failure(result, operation_name, start_context)
            
            return result
        
        return wrapper
    return decorator


def with_document_quality_logging(expected_fields: List[str], operation: str = "processing"):
    """Decorator to add document quality logging to functions that process DocumentList.
    
    Args:
        expected_fields: List of fields that should be present in documents
        operation: Operation name for logging context
        
    Returns:
        Decorator function
        
    Examples:
        >>> @with_document_quality_logging(["name", "email", "age"], "user_processing")
        ... def process_users(docs):
        ...     return [doc for doc in docs if doc.get("active")]
    """
    def decorator(func: Callable[[DocumentList], DocumentList]) -> Callable[[DocumentList], DocumentList]:
        @wraps(func)
        def wrapper(documents: DocumentList) -> DocumentList:
            # Log input quality
            log_document_completeness(documents, expected_fields, f"{operation}_input")
            
            # Execute function
            result_docs = func(documents)
            
            # Log output quality
            log_document_completeness(result_docs, expected_fields, f"{operation}_output")
            
            # Log transformation stats
            if len(documents) != len(result_docs):
                logger.info(
                    f"Document count changed during {operation}",
                    operation=operation,
                    input_count=len(documents),
                    output_count=len(result_docs),
                    change=len(result_docs) - len(documents)
                )
            
            return result_docs
        
        return wrapper
    return decorator


def log_batch_processing_stats(batches: List[DocumentList], operation: str = "batch_processing"):
    """Log statistics about batch processing operations.
    
    Args:
        batches: List of document batches
        operation: Operation name for logging context
        
    Returns:
        The original batches unchanged (for chaining)
    """
    if not batches:
        logger.warning(f"No batches to process for {operation}")
        return batches
    
    total_docs = sum(len(batch) for batch in batches)
    batch_sizes = [len(batch) for batch in batches]
    
    stats = {
        "operation": operation,
        "batch_count": len(batches),
        "total_documents": total_docs,
        "avg_batch_size": round(sum(batch_sizes) / len(batch_sizes), 1),
        "min_batch_size": min(batch_sizes),
        "max_batch_size": max(batch_sizes)
    }
    
    logger.info(f"Batch processing stats for {operation}", **stats)
    
    # Log warning if batch sizes vary significantly
    if stats["max_batch_size"] > stats["min_batch_size"] * 2:
        logger.warning(
            f"Significant batch size variation in {operation}",
            **stats,
            size_ratio=round(stats["max_batch_size"] / stats["min_batch_size"], 1)
        )
    
    return batches


# Convenience functions for common patterns
def log_fetch_operation(result: DataSourceResult[DocumentList], source: str, 
                       collection: str, query: Optional[Dict[str, Any]] = None) -> DataSourceResult[DocumentList]:
    """Log a document fetch operation with context.
    
    Args:
        result: Result from fetch operation
        source: Data source name
        collection: Collection/table name
        query: Optional query that was executed
        
    Returns:
        The original result unchanged (for chaining)
    """
    context = {
        "source": source,
        "collection": collection,
        "query": query or {}
    }
    
    return log_result_failure(result, "document_fetch", context)


def log_conversion_operation(df_result: DataFrameResult, backend: str, 
                           document_count: int) -> DataFrameResult:
    """Log a document-to-dataframe conversion operation.
    
    Args:
        df_result: Result from conversion operation
        backend: DataFrame backend used (pandas/polars)
        document_count: Number of input documents
        
    Returns:
        The original result unchanged (for chaining)
    """
    context = {
        "backend": backend,
        "input_document_count": document_count
    }
    
    return log_dataframe_creation_stats(df_result, context)


# Integration with existing pipeline functions
def with_quality_logging(func: Callable[..., Result[T, E]], operation: str, 
                        context: Optional[Dict[str, Any]] = None) -> Callable[..., Result[T, E]]:
    """Add quality logging to any function that returns a Result.
    
    Args:
        func: Function to wrap with logging
        operation: Operation name for logging
        context: Additional context for logs
        
    Returns:
        Wrapped function with logging
        
    Examples:
        >>> from autoframe.sources.simple import fetch
        >>> logged_fetch = with_quality_logging(
        ...     fetch, 
        ...     "document_fetch",
        ...     {"source": "mongodb"}
        ... )
        >>> # logged_fetch can now be called like: logged_fetch("mongodb://localhost", "db", "coll")
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return log_result_failure(result, operation, context)
    
    return wrapper