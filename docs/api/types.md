# Types and Interfaces

This section documents the core types and interfaces used throughout AutoFrame.

## Error Types

::: autoframe.types.AutoFrameError

::: autoframe.types.DataFrameCreationError

::: autoframe.types.DataSourceError

::: autoframe.types.QualityValidationError

::: autoframe.types.ConfigurationError

## Type Aliases

The module provides modern Python 3.12+ type aliases for common data structures:

- `DataFrameType`: Union of pandas and polars DataFrames
- `QueryDict`: Dictionary for MongoDB queries  
- `DocumentList`: List of documents from data sources
- `ConnectionString`, `DatabaseName`, `CollectionName`, `FieldName`: String aliases for clarity
- `QualityScore`, `QualityMetrics`, `QualityThreshold`: Quality reporting types

## Result Types

Result types built on logerr for functional error handling:

- `DataFrameResult`: Result for DataFrame operations
- `DataSourceResult`: Result for data source operations  
- `QualityResult`: Result for quality validation operations
- `ConfigResult`: Result for configuration operations