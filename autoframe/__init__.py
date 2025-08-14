"""AutoFrame - Automated dataframe creation with data quality reporting.

A Python library for creating dataframes from various data sources with
integrated quality assessment and functional error handling.
"""

__version__ = "0.1.0"
__author__ = "Jesse Robertson"
__email__ = "jess.robertson@niwa.co.nz"

# Re-export key components for convenient access
# Simplified functional, composable API
from autoframe.pipeline import create_pipeline
from autoframe import mongodb
from autoframe.utils.functional import to_dataframe, apply_schema, pipe
from autoframe.utils.retry import with_database_retry, with_network_retry, retry_with_backoff
from autoframe.quality import log_result_failure, log_conversion_operation

__all__ = [
    # Core functional API
    "mongodb",
    "create_pipeline", 
    "to_dataframe",
    "apply_schema", 
    "pipe",
    # Retry utilities
    "with_database_retry",
    "with_network_retry", 
    "retry_with_backoff",
    # Transparent quality logging
    "log_result_failure",
    "log_conversion_operation",
    "__version__",
]