"""Composable data processing pipelines.

This module provides high-level composable functions for creating 
data processing pipelines in the logerr functional style.
"""

from typing import Callable, Any
from functools import partial

from logerr import Result  # type: ignore
from autoframe.types import DataFrameResult, DocumentList, DataSourceResult
from autoframe.mongodb import fetch, create_fetcher
from autoframe.quality import log_result_failure, log_conversion_operation
from autoframe.utils.functional import (
    to_dataframe,
    apply_schema, 
    transform,
    filter,
    limit,
    validate_columns,
    pipe
)



def create_pipeline(
    fetch_fn: Callable[[], DataSourceResult[DocumentList]]
) -> "DataPipeline":
    """Create a composable data processing pipeline.
    
    Args:
        fetch_fn: Function that fetches documents
        
    Returns:
        DataPipeline object for method chaining
        
    Examples:
        >>> fetch_users = lambda: fetch("mongodb://localhost", "db", "users")
        >>> result = (
        ...     create_pipeline(fetch_users) 
        ...     .filter(lambda doc: doc["active"])
        ...     .transform(lambda doc: {**doc, "processed": True})
        ...     .limit(100)
        ...     .to_dataframe()
        ...     .apply_schema({"age": "int"})
        ...     .execute()
        ... )
    """
    return DataPipeline(fetch_fn)


class DataPipeline:
    """Composable data pipeline for method chaining.
    
    This provides a fluent interface while keeping individual functions simple.
    """
    
    def __init__(self, fetch_fn: Callable[[], DataSourceResult[DocumentList]]):
        self.fetch_fn = fetch_fn
        self.transforms: list[Callable] = []
        self.df_transforms: list[Callable] = []
        self.target_backend = "pandas"
        self.target_schema: dict[str, str] | None = None
    
    def filter(self, predicate: Callable[[dict[str, Any]], bool]) -> "DataPipeline":
        """Add document filtering to pipeline."""
        self.transforms.append(filter(predicate))
        return self
    
    def transform(self, transform_fn: Callable[[dict[str, Any]], dict[str, Any]]) -> "DataPipeline":
        """Add document transformation to pipeline."""
        self.transforms.append(transform(transform_fn))
        return self
    
    def limit(self, count: int) -> "DataPipeline":
        """Add document limiting to pipeline."""
        self.transforms.append(limit(count))
        return self
    
    def to_dataframe(self, backend: str = "pandas") -> "DataPipeline":
        """Convert to dataframe in pipeline."""
        self.target_backend = backend
        return self
    
    def apply_schema(self, schema: dict[str, str]) -> "DataPipeline":
        """Apply schema to dataframe in pipeline."""
        self.target_schema = schema
        return self
    
    def validate(self, required_columns: list[str]) -> "DataPipeline":
        """Add column validation to pipeline.""" 
        self.df_transforms.append(validate_columns(required_columns))
        return self
    
    def execute(self) -> DataFrameResult:
        """Execute the complete pipeline with quality logging.
        
        Returns:
            Result[DataFrame, Error]
        """
        # Fetch documents with logging
        docs_result = self.fetch_fn()
        docs_result = log_result_failure(docs_result, "pipeline_fetch", {
            "transforms": len(self.transforms),
            "backend": self.target_backend,
            "has_schema": bool(self.target_schema)
        })
        
        # Apply document transforms with logging
        if self.transforms:
            combined_transform = pipe(*self.transforms)
            original_count = len(docs_result.unwrap_or([]))
            docs_result = docs_result.map(combined_transform)
            new_count = len(docs_result.unwrap_or([]))
            
            if original_count != new_count:
                log_result_failure(docs_result, "pipeline_transforms", {
                    "original_count": original_count,
                    "new_count": new_count,
                    "change": new_count - original_count,
                    "transform_count": len(self.transforms)
                })
        
        # Convert to dataframe with logging
        df_result = docs_result.then(
            partial(to_dataframe, backend=self.target_backend)
        )
        df_result = log_conversion_operation(
            df_result,
            self.target_backend,
            len(docs_result.unwrap_or([]))
        )
        
        # Apply schema if specified
        if self.target_schema:
            df_result = df_result.map(apply_schema(self.target_schema))
            df_result = log_result_failure(df_result, "pipeline_schema", {
                "schema": self.target_schema,
                "backend": self.target_backend
            })
        
        # Apply dataframe transforms with logging
        for i, df_transform in enumerate(self.df_transforms):
            df_result = df_transform(df_result)
            df_result = log_result_failure(df_result, f"pipeline_df_transform_{i}", {
                "transform_index": i,
                "total_transforms": len(self.df_transforms)
            })
        
        return df_result


# Convenience functions for common patterns
