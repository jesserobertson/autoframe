"""Core type definitions for autoframe.

This module provides type aliases and common types used throughout the autoframe library,
building on the functional programming patterns from logerr.
"""

from typing import TYPE_CHECKING, Any, TypeVar

import pandas as pd

if TYPE_CHECKING:
    try:
        import polars as pl
        POLARS_AVAILABLE = True
    except ImportError:
        POLARS_AVAILABLE = False
else:
    try:
        import polars as pl
        POLARS_AVAILABLE = True
    except ImportError:
        POLARS_AVAILABLE = False

from logerr import Option, Result

# Type variables for generic programming
T = TypeVar("T")
E = TypeVar("E")

# Core type aliases from logerr
ResultType = Result[T, E]
OptionType = Option[T]

# Data types - use modern type statement
if POLARS_AVAILABLE:
    import polars as pl
    type DataFrameType = pd.DataFrame | pl.DataFrame
else:
    type DataFrameType = pd.DataFrame
type QueryDict = dict[str, Any]
type DocumentList = list[dict[str, Any]]

# Error types for autoframe operations
class AutoFrameError(Exception):
    """Base exception for autoframe operations."""
    pass

class DataSourceError(AutoFrameError):
    """Raised when data source operations fail."""
    pass

class DataFrameCreationError(AutoFrameError):
    """Raised when dataframe creation fails."""
    pass

class QualityValidationError(AutoFrameError):
    """Raised when data quality validation fails."""
    pass

class ConfigurationError(AutoFrameError):
    """Raised when configuration is invalid."""
    pass

# Result type aliases for common operations
DataSourceResult = Result[T, DataSourceError]
DataFrameResult = Result[DataFrameType, DataFrameCreationError]
QualityResult = Result[T, QualityValidationError]
ConfigResult = Result[T, ConfigurationError]

# Connection and query types
type ConnectionString = str
type DatabaseName = str
type CollectionName = str
type FieldName = str

# Quality reporting types
type QualityScore = float  # 0.0 to 1.0
type QualityMetrics = dict[str, int | float | str]
type QualityThreshold = float
