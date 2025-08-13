"""AutoFrame - Automated dataframe creation with data quality reporting.

A Python library for creating dataframes from various data sources with
integrated quality assessment and functional error handling.
"""

__version__ = "0.1.0"
__author__ = "Jesse Robertson"
__email__ = "jess.robertson@niwa.co.nz"

# Re-export key components for convenient access
from autoframe.frames.core import create_dataframe
from autoframe.sources.mongodb import MongoDBAdapter
from autoframe.config import get_config, AutoFrameConfig

__all__ = [
    "create_dataframe",
    "MongoDBAdapter",
    "get_config", 
    "AutoFrameConfig",
    "__version__",
]