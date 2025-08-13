"""Logging integration for autoframe using logerr.

This module sets up logging integration between autoframe and logerr,
providing consistent logging patterns throughout the library.
"""

from typing import Optional, Any, Dict
import sys
from pathlib import Path

from loguru import logger

from autoframe.config import get_config


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    enable_performance_logging: Optional[bool] = None,
    log_query_details: Optional[bool] = None
) -> None:
    """Set up logging for autoframe.
    
    This function configures loguru and logerr integration based on
    autoframe configuration settings.
    
    Args:
        level: Log level override
        log_file: Optional log file path
        enable_performance_logging: Enable performance timing logs
        log_query_details: Enable detailed query logging
    """
    config = get_config()
    logging_config = config.get_logging_config()
    
    # Determine log level
    log_level = level or logging_config.get("level", "INFO")
    
    # Remove default handler and add configured handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler if specified
    if log_file:
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="gz"
        )
    
    # logerr will automatically use loguru if available
    
    # Set up additional context for autoframe
    logger.configure(extra={
        "autoframe_version": "0.1.0",
        "enable_query_logging": log_query_details or logging_config.get("log_query_details", False)
    })


def get_logger(name: str) -> Any:
    """Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logger.bind(module=name)


def log_dataframe_operation(
    operation: str,
    source_type: str,
    document_count: int,
    execution_time: Optional[float] = None,
    **kwargs: Any
) -> None:
    """Log dataframe operations with consistent formatting.
    
    Args:
        operation: Operation type (e.g., "create_dataframe", "query")
        source_type: Data source type (e.g., "mongodb", "postgres")
        document_count: Number of documents processed
        execution_time: Optional execution time in seconds
        **kwargs: Additional context to log
    """
    config = get_config()
    logging_config = config.get_logging_config()
    
    if not logging_config.get("enable_performance_logging", False):
        return
    
    log_context = {
        "operation": operation,
        "source_type": source_type,
        "document_count": document_count,
        **kwargs
    }
    
    if execution_time is not None:
        log_context["execution_time_seconds"] = execution_time
    
    logger.info(
        f"DataFrameOperation completed: {operation}",
        **log_context
    )


def log_quality_assessment(
    collection_name: str,
    quality_score: float,
    metrics: Dict[str, Any],
    **kwargs: Any
) -> None:
    """Log data quality assessment results.
    
    Args:
        collection_name: Name of the collection assessed
        quality_score: Overall quality score (0.0 to 1.0)
        metrics: Quality metrics dictionary
        **kwargs: Additional context
    """
    logger.info(
        f"QualityAssessment completed for {collection_name}",
        quality_score=quality_score,
        metrics=metrics,
        **kwargs
    )


def log_connection_event(
    event_type: str,
    source_type: str,
    connection_string: str,
    success: bool,
    error: Optional[str] = None,
    **kwargs: Any
) -> None:
    """Log database connection events.
    
    Args:
        event_type: Event type ("connect", "disconnect", "test")
        source_type: Data source type
        connection_string: Connection string (will be sanitized)  
        success: Whether the operation succeeded
        error: Error message if failed
        **kwargs: Additional context
    """
    # Sanitize connection string for logging
    sanitized_connection = _sanitize_connection_string(connection_string)
    
    log_context = {
        "event_type": event_type,
        "source_type": source_type,
        "connection": sanitized_connection,
        "success": success,
        **kwargs
    }
    
    if error:
        log_context["error"] = error
    
    if success:
        logger.info(f"ConnectionEvent: {event_type} succeeded", **log_context)
    else:
        logger.error(f"ConnectionEvent: {event_type} failed", **log_context)


def log_query_execution(
    database: str,
    collection: str,
    query: Dict[str, Any],
    result_count: int,
    execution_time: Optional[float] = None,
    **kwargs: Any
) -> None:
    """Log query execution details.
    
    Args:
        database: Database name
        collection: Collection name
        query: Query dictionary (will be sanitized)
        result_count: Number of results returned
        execution_time: Execution time in seconds
        **kwargs: Additional context
    """
    config = get_config()
    logging_config = config.get_logging_config()
    
    if not logging_config.get("log_query_details", False):
        return
    
    # Sanitize query for logging (remove potential sensitive data)
    sanitized_query = _sanitize_query(query)
    
    log_context = {
        "database": database,
        "collection": collection,
        "query": sanitized_query,
        "result_count": result_count,
        **kwargs
    }
    
    if execution_time is not None:
        log_context["execution_time_seconds"] = execution_time
    
    logger.debug(f"QueryExecution completed", **log_context)


def _sanitize_connection_string(connection_string: str) -> str:
    """Sanitize connection string for logging by removing credentials.
    
    Args:
        connection_string: Original connection string
        
    Returns:
        Sanitized connection string
    """
    try:
        # Basic sanitization - remove anything that looks like credentials
        if "://" in connection_string:
            protocol, rest = connection_string.split("://", 1)
            if "@" in rest:
                # Remove username:password@ part
                _, host_part = rest.split("@", 1)
                return f"{protocol}://***@{host_part}"
        return connection_string
    except Exception:
        return "***"


def _sanitize_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize query dictionary for logging.
    
    Args:
        query: Original query dictionary
        
    Returns:
        Sanitized query dictionary
    """
    sensitive_fields = {"password", "token", "secret", "key", "auth"}
    
    def sanitize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: sanitize_value(v) if k.lower() not in sensitive_fields else "***" 
                   for k, v in value.items()}
        elif isinstance(value, list):
            return [sanitize_value(v) for v in value]
        elif isinstance(value, str) and len(value) > 100:
            # Truncate very long strings
            return value[:97] + "..."
        return value
    
    try:
        return sanitize_value(query)
    except Exception:
        return {"query": "***"}


# Initialize logging on module import
def _initialize_default_logging() -> None:
    """Initialize default logging if not already configured."""
    try:
        # Only set up logging if loguru hasn't been configured yet
        if not logger._core.handlers:
            setup_logging()
    except Exception:
        # Fail silently if logging setup fails
        pass


# Auto-initialize logging
_initialize_default_logging()