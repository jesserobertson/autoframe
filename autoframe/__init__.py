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
from autoframe.quality import (
    log_conversion,
    log_failure,
    log_conversion_operation,  # backward compatibility
    log_result_failure,        # backward compatibility
)
from autoframe.utils.functional import apply_schema, pipe, to_dataframe
from autoframe.utils.retry import (
    db_retry,
    net_retry,
    retry_backoff,
    with_database_retry,  # backward compatibility
    with_network_retry,   # backward compatibility
    retry_with_backoff,   # backward compatibility
)

__all__ = [
    "__version__",
    "apply_schema",
    "auth",
    "db_retry",
    "log_conversion",
    "log_conversion_operation",  # backward compatibility
    "log_failure",
    # Transparent quality logging
    "log_result_failure",        # backward compatibility
    # Core functional API
    "mongodb",
    "net_retry",
    "pipe",
    "pipeline",
    "retry_backoff",
    "retry_with_backoff",  # backward compatibility
    "to_dataframe",
    # Retry utilities
    "with_database_retry", # backward compatibility
    "with_network_retry",  # backward compatibility
]