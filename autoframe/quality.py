"""Transparent quality logging utilities for Result-driven data processing.

This module provides automatic logging utilities that integrate with Result types
to capture error information transparently without manual logging calls.
The goal is transparent error handling through the Result framework.
"""

from typing import Dict, Any, Optional, TypeVar

from loguru import logger
from logerr import Result, Ok, Err

from autoframe.types import DataFrameResult

T = TypeVar('T')
E = TypeVar('E')


def log_result_failure(result: Result[T, E], operation: str, context: Optional[Dict[str, Any]] = None) -> Result[T, E]:
    """Automatically log when a Result contains an error.
    
    This function provides transparent error logging - it logs failures automatically
    when they occur in Result chains without requiring manual logging calls.
    
    Args:
        result: The Result to inspect
        operation: Description of the operation that produced this Result
        context: Optional additional context to log
        
    Returns:
        The original Result unchanged (for chaining)
        
    Examples:
        >>> from logerr import Err
        >>> from autoframe.types import DataSourceError
        >>> 
        >>> # Example with a failing result - error is logged automatically
        >>> result = Err(DataSourceError("Connection failed"))
        >>> logged_result = log_result_failure(result, "document_fetch", {"collection": "users"})
        >>> logged_result.is_err()
        True
    """
    match result:
        case Err(error):
            log_context = {
                "operation": operation,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **(context or {})
            }
            logger.error(f"Operation failed: {operation}", **log_context)
        case Ok(_):
            pass  # Success - no logging needed
    
    return result


def log_conversion_operation(df_result: DataFrameResult, backend: str, 
                           document_count: int) -> DataFrameResult:
    """Automatically log dataframe conversion operations.
    
    Provides transparent logging for document-to-dataframe conversions
    without requiring manual logging calls.
    
    Args:
        df_result: Result from conversion operation
        backend: DataFrame backend used (pandas/polars)
        document_count: Number of input documents
        
    Returns:
        The original result unchanged (for chaining)
    """
    match df_result:
        case Ok(df):
            log_context = {
                "operation": "dataframe_conversion",
                "backend": backend,
                "input_documents": document_count,
                "output_rows": len(df),
                "output_columns": len(df.columns)
            }
            logger.info(f"DataFrame conversion successful: {document_count} docs → {len(df)} rows", **log_context)
        case Err(_):
            # Error already logged by log_result_failure, just add conversion context
            log_context = {
                "operation": "dataframe_conversion", 
                "backend": backend,
                "input_documents": document_count
            }
            logger.error(f"DataFrame conversion failed", **log_context)
    
    return df_result