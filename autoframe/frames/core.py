"""Core dataframe creation and manipulation functionality.

This module provides the main interface for creating dataframes from various data sources
with integrated quality assessment and functional error handling.
"""

from typing import Optional, Dict, Any, List, Callable, Union
import pandas as pd

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

from autoframe.types import (
    DataFrameResult,
    DataFrameType,
    DocumentList,
    DataFrameCreationError,
    QualityResult,
    FieldName
)
# Note: DataSourceAdapter and QueryBuilder removed - using direct MongoDB functions
from logerr import Result, Option, Ok, Err
from logerr.utils import execute


class DataFrameFactory:
    """Factory for creating dataframes from various data sources.
    
    This class provides a functional interface for dataframe creation
    with built-in error handling and quality assessment.
    """
    
    @staticmethod
    def from_documents(
        documents: DocumentList,
        backend: str = "pandas",
        schema: Optional[Dict[str, str]] = None,
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> DataFrameResult:
        """Create a dataframe from a list of documents using Result types.
        
        Args:
            documents: List of document dictionaries
            backend: Dataframe backend ("pandas" or "polars")
            schema: Optional schema specification for type conversion
            transform: Optional transformation function applied to each document
            
        Returns:
            Result[DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        def create_df():
            if not documents:
                return Ok(pd.DataFrame() if backend == "pandas" else pl.DataFrame())
            
            # Apply transformation if provided
            transformed_docs = [transform(doc) for doc in documents] if transform else documents
            
            if backend == "pandas":
                return DataFrameFactory._create_pandas_dataframe(transformed_docs, schema)
            elif backend == "polars" and POLARS_AVAILABLE:
                return DataFrameFactory._create_polars_dataframe(transformed_docs, schema)
            else:
                error_msg = f"Unsupported backend: {backend}"
                if backend == "polars" and not POLARS_AVAILABLE:
                    error_msg += " (polars not installed)"
                raise DataFrameCreationError(error_msg)
        
        return execute(create_df).then(lambda result: result).map_err(
            lambda e: e if isinstance(e, DataFrameCreationError) else 
                     DataFrameCreationError(f"Failed to create dataframe: {str(e)}")
        )
    
    @staticmethod
    def from_query_builder(
        query_builder: QueryBuilder,
        backend: str = "pandas",
        schema: Optional[Dict[str, str]] = None,
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> DataFrameResult:
        """Create a dataframe from a query builder.
        
        Args:
            query_builder: Configured query builder
            backend: Dataframe backend ("pandas" or "polars")
            schema: Optional schema specification for type conversion
            transform: Optional transformation function applied to each document
            
        Returns:
            Result[DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        # Execute the query
        query_result = query_builder.execute()
        
        return query_result.then(
            lambda documents: DataFrameFactory.from_documents(
                documents, backend, schema, transform
            )
        ).map_err(
            lambda source_error: DataFrameCreationError(f"Query failed: {str(source_error)}")
        )
    
    @staticmethod
    def _create_pandas_dataframe(
        documents: DocumentList, 
        schema: Optional[Dict[str, str]] = None
    ) -> DataFrameResult:
        """Create a pandas DataFrame from documents using Result types.
        
        Args:
            documents: List of document dictionaries
            schema: Optional schema for type conversion
            
        Returns:
            Result[pd.DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        def create_pandas():
            df = pd.DataFrame(documents)
            
            if schema:
                df = DataFrameFactory._apply_pandas_schema(df, schema)
            
            return df
        
        return execute(create_pandas).map_err(
            lambda e: DataFrameCreationError(f"Pandas dataframe creation failed: {str(e)}")
        )
    
    @staticmethod
    def _create_polars_dataframe(
        documents: DocumentList,
        schema: Optional[Dict[str, str]] = None
    ) -> DataFrameResult:
        """Create a polars DataFrame from documents using Result types.
        
        Args:
            documents: List of document dictionaries
            schema: Optional schema for type conversion
            
        Returns:
            Result[pl.DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        if not POLARS_AVAILABLE:
            return Err(DataFrameCreationError("Polars not available"))
        
        def create_polars():
            df = pl.DataFrame(documents)
            
            if schema:
                df = DataFrameFactory._apply_polars_schema(df, schema)
            
            return df
        
        return execute(create_polars).map_err(
            lambda e: DataFrameCreationError(f"Polars dataframe creation failed: {str(e)}")
        )
    
    @staticmethod
    def _apply_pandas_schema(df: pd.DataFrame, schema: Dict[str, str]) -> pd.DataFrame:
        """Apply schema to pandas DataFrame using Result types.
        
        Args:
            df: DataFrame to apply schema to
            schema: Field name to type mapping
            
        Returns:
            pd.DataFrame: DataFrame with applied schema
        """
        type_mapping = {
            "int": "int64",
            "float": "float64", 
            "string": "object",
            "datetime": "datetime64[ns]",
            "bool": "bool"
        }
        
        for field, field_type in schema.items():
            if field in df.columns:
                pandas_type = type_mapping.get(field_type, "object")
                
                def convert_field():
                    if pandas_type == "datetime64[ns]":
                        return pd.to_datetime(df[field], errors="coerce")
                    else:
                        return df[field].astype(pandas_type, errors="ignore")
                
                # Use Result types but keep original if conversion fails
                converted_result = execute(convert_field)
                if converted_result.is_ok():
                    df[field] = converted_result.unwrap()
        
        return df
    
    @staticmethod
    def _apply_polars_schema(df: "pl.DataFrame", schema: Dict[str, str]) -> "pl.DataFrame":
        """Apply schema to polars DataFrame using Result types.
        
        Args:
            df: DataFrame to apply schema to
            schema: Field name to type mapping
            
        Returns:
            pl.DataFrame: DataFrame with applied schema
        """
        if not POLARS_AVAILABLE:
            return df
            
        type_mapping = {
            "int": pl.Int64,
            "float": pl.Float64,
            "string": pl.Utf8,
            "datetime": pl.Datetime,
            "bool": pl.Boolean
        }
        
        cast_expressions = []
        for field, field_type in schema.items():
            if field in df.columns:
                polars_type = type_mapping.get(field_type)
                if polars_type:
                    cast_expr_result = execute(lambda: pl.col(field).cast(polars_type))
                    cast_expressions.append(cast_expr_result.unwrap_or(pl.col(field)))
                else:
                    cast_expressions.append(pl.col(field))
        
        if cast_expressions:
            return execute(lambda: df.with_columns(cast_expressions)).unwrap_or(df)
        
        return df


def create_dataframe(
    source: Union[DataSourceAdapter, QueryBuilder, DocumentList],
    backend: str = "pandas",
    schema: Optional[Dict[str, str]] = None,
    transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
) -> DataFrameResult:
    """Convenience function to create a dataframe from various sources.
    
    This is the main entry point for dataframe creation in autoframe.
    
    Args:
        source: Data source (adapter, query builder, or document list)
        backend: Dataframe backend ("pandas" or "polars")
        schema: Optional schema specification for type conversion
        transform: Optional transformation function applied to each document
        
    Returns:
        Result[DataFrame, DataFrameCreationError]: Created dataframe or error
        
    Examples:
        >>> from autoframe.frames.core import create_dataframe
        >>> 
        >>> # From documents
        >>> docs = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        >>> result = create_dataframe(docs)
        >>> result.is_ok()
        True
        >>> df = result.unwrap()
        >>> len(df)
        2
    """
    if isinstance(source, QueryBuilder):
        return DataFrameFactory.from_query_builder(source, backend, schema, transform)
    elif isinstance(source, list):
        return DataFrameFactory.from_documents(source, backend, schema, transform)
    else:
        return Err(DataFrameCreationError(f"Unsupported source type: {type(source)}"))


class DataFrameProcessor:
    """Processor for applying transformations and validations to dataframes.
    
    This class provides functional utilities for working with dataframes
    in a pipeline-style approach.
    """
    
    @staticmethod
    def apply_transform(
        df_result: DataFrameResult,
        transform: Callable[[DataFrameType], DataFrameType]
    ) -> DataFrameResult:
        """Apply a transformation to a dataframe result.
        
        Args:
            df_result: Result containing a dataframe
            transform: Transformation function
            
        Returns:
            Result[DataFrame, DataFrameCreationError]: Transformed dataframe or error
        """
        return df_result.map(transform)
    
    @staticmethod
    def validate_columns(
        df_result: DataFrameResult,
        required_columns: List[FieldName]
    ) -> DataFrameResult:
        """Validate that required columns exist in the dataframe.
        
        Args:
            df_result: Result containing a dataframe
            required_columns: List of required column names
            
        Returns:
            Result[DataFrame, DataFrameCreationError]: Validated dataframe or error
        """
        def validate(df: DataFrameType) -> DataFrameType:
            if isinstance(df, pd.DataFrame):
                missing = set(required_columns) - set(df.columns)
            elif POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
                missing = set(required_columns) - set(df.columns)
            else:
                missing = set()
                
            if missing:
                raise DataFrameCreationError(f"Missing required columns: {missing}")
            
            return df
        
        return df_result.then(
            lambda df: Result.Ok(validate(df))
        ).map_err(
            lambda e: e if isinstance(e, DataFrameCreationError) else DataFrameCreationError(str(e))
        )