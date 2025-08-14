"""AutoFrame - Automated dataframe creation with data quality reporting.

A Python library for creating dataframes from various data sources with
integrated quality assessment and functional error handling.
"""

__version__ = "0.1.0"
__author__ = "Jesse Robertson"
__email__ = "jess.robertson@niwa.co.nz"

# Re-export key components for convenient access
# Functional, composable API
from autoframe.pipeline import mongodb_to_dataframe, create_pipeline, fetch_and_process, quick_dataframe
from autoframe.sources.simple import fetch_documents, fetch_documents_with_retry, create_fetcher
from autoframe.utils.functional import to_dataframe, apply_schema, pipe
from autoframe.utils.retry import with_database_retry, with_network_retry, retry_with_backoff

__all__ = [
    # Core functional API
    "mongodb_to_dataframe",
    "create_pipeline", 
    "fetch_and_process",
    "quick_dataframe",
    "fetch_documents",
    "to_dataframe",
    "apply_schema", 
    "pipe",
    # Retry utilities
    "with_database_retry",
    "with_network_retry", 
    "retry_with_backoff",
    "__version__",
]