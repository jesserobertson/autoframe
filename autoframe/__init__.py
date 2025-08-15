"""AutoFrame - Automated dataframe creation with data quality reporting.

A Python library for creating dataframes from various data sources with
integrated quality assessment and functional error handling.
"""

__version__ = "0.1.0"
__author__ = "Jesse Robertson"
__email__ = "jess.robertson@niwa.co.nz"

# Re-export key components for convenient access
# Simplified functional, composable API
from autoframe import auth, mongodb
from autoframe.pipeline import pipeline
from autoframe.quality import log_conversion_operation, log_result_failure
from autoframe.utils.functional import apply_schema, pipe, to_dataframe
from autoframe.utils.retry import (
    retry_with_backoff,
    with_database_retry,
    with_network_retry,
)

__all__ = [
    "__version__",
    "apply_schema",
    "auth",
    "log_conversion_operation",
    # Transparent quality logging
    "log_result_failure",
    # Core functional API
    "mongodb",
    "pipe",
    "pipeline",
    "retry_with_backoff",
    "to_dataframe",
    # Retry utilities
    "with_database_retry",
    "with_network_retry",
]
