"""AutoFrame - Automated dataframe creation with data quality reporting.

A Python library for creating dataframes from various data sources with
integrated quality assessment and functional error handling.
"""

__version__ = "0.1.0"
__author__ = "Jesse Robertson"
__email__ = "jess.robertson@niwa.co.nz"

# Re-export key components for convenient access
from autoframe.frames import create_dataframe
from autoframe.quality import QualityReport
from autoframe.sources import DataSource

__all__ = [
    "create_dataframe",
    "QualityReport", 
    "DataSource",
    "__version__",
]