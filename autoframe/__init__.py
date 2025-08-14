"""AutoFrame - Automated dataframe creation with data quality reporting.

A Python library for creating dataframes from various data sources with
integrated quality assessment and functional error handling.
"""

__version__ = "0.1.0"
__author__ = "Jesse Robertson"
__email__ = "jess.robertson@niwa.co.nz"

# Re-export key components for convenient access
# Functional, composable API
from autoframe.pipeline import create_pipeline, fetch_and_process, quick_dataframe
from autoframe import mongodb
from autoframe.sources.simple import fetch, fetch_with_retry, create_fetcher
from autoframe.utils.functional import to_dataframe, apply_schema, pipe
from autoframe.utils.retry import with_database_retry, with_network_retry, retry_with_backoff
from autoframe.quality import (
    log_result_failure, 
    log_document_completeness,
    log_dataframe_creation_stats,
    track_pipeline_operation,
    with_document_quality_logging
)

__all__ = [
    # Core functional API
    "mongodb",
    "create_pipeline", 
    "fetch_and_process",
    "quick_dataframe",
    "fetch",
    "to_dataframe",
    "apply_schema", 
    "pipe",
    # Retry utilities
    "with_database_retry",
    "with_network_retry", 
    "retry_with_backoff",
    # Quality logging
    "log_result_failure",
    "log_document_completeness", 
    "log_dataframe_creation_stats",
    "track_pipeline_operation",
    "with_document_quality_logging",
    "__version__",
]