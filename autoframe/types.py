"""Core type definitions for autoframe.

This module provides type aliases and common types used throughout the autoframe library,
building on the functional programming patterns from logerr.
"""

from typing import TypeVar, Union, Dict, Any, List, Optional
import pandas as pd

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

from logerr import Result, Option, Ok, Err

# Type variables for generic programming
T = TypeVar("T")
E = TypeVar("E")

# Core type aliases from logerr
ResultType = Result[T, E]
OptionType = Option[T]

# Data types
DataFrameType = Union[pd.DataFrame, "pl.DataFrame"] if POLARS_AVAILABLE else pd.DataFrame
QueryDict = Dict[str, Any]
DocumentList = List[Dict[str, Any]]

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
ConnectionString = str
DatabaseName = str
CollectionName = str
FieldName = str

# Quality reporting types
QualityScore = float  # 0.0 to 1.0
QualityMetrics = Dict[str, Union[int, float, str]]
QualityThreshold = float