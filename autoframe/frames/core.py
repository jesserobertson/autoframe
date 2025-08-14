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
from autoframe.sources.base import DataSourceAdapter, QueryBuilder
from logerr import Result, Option, Ok, Err


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
        """Create a dataframe from a list of documents.
        
        Args:
            documents: List of document dictionaries
            backend: Dataframe backend ("pandas" or "polars")
            schema: Optional schema specification for type conversion
            transform: Optional transformation function applied to each document
            
        Returns:
            Result[DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        try:
            if not documents:
                return Ok(pd.DataFrame() if backend == "pandas" else pl.DataFrame())
            
            # Apply transformation if provided
            if transform:
                documents = [transform(doc) for doc in documents]
            
            if backend == "pandas":
                return DataFrameFactory._create_pandas_dataframe(documents, schema)
            elif backend == "polars" and POLARS_AVAILABLE:
                return DataFrameFactory._create_polars_dataframe(documents, schema)
            else:
                error_msg = f"Unsupported backend: {backend}"
                if backend == "polars" and not POLARS_AVAILABLE:
                    error_msg += " (polars not installed)"
                return Err(DataFrameCreationError(error_msg))
                
        except Exception as e:
            return Err(DataFrameCreationError(f"Failed to create dataframe: {str(e)}"))
    
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
        """Create a pandas DataFrame from documents.
        
        Args:
            documents: List of document dictionaries
            schema: Optional schema for type conversion
            
        Returns:
            Result[pd.DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        try:
            df = pd.DataFrame(documents)
            
            if schema:
                df = DataFrameFactory._apply_pandas_schema(df, schema)
            
            return Ok(df)
            
        except Exception as e:
            return Err(DataFrameCreationError(f"Pandas dataframe creation failed: {str(e)}"))
    
    @staticmethod
    def _create_polars_dataframe(
        documents: DocumentList,
        schema: Optional[Dict[str, str]] = None
    ) -> DataFrameResult:
        """Create a polars DataFrame from documents.
        
        Args:
            documents: List of document dictionaries
            schema: Optional schema for type conversion
            
        Returns:
            Result[pl.DataFrame, DataFrameCreationError]: Created dataframe or error
        """
        if not POLARS_AVAILABLE:
            return Err(DataFrameCreationError("Polars not available"))
            
        try:
            df = pl.DataFrame(documents)
            
            if schema:
                df = DataFrameFactory._apply_polars_schema(df, schema)
            
            return Ok(df)
            
        except Exception as e:
            return Err(DataFrameCreationError(f"Polars dataframe creation failed: {str(e)}"))
    
    @staticmethod
    def _apply_pandas_schema(df: pd.DataFrame, schema: Dict[str, str]) -> pd.DataFrame:
        """Apply schema to pandas DataFrame.
        
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
                try:
                    if pandas_type == "datetime64[ns]":
                        df[field] = pd.to_datetime(df[field], errors="coerce")
                    else:
                        df[field] = df[field].astype(pandas_type, errors="ignore")
                except Exception:
                    # If conversion fails, leave as original type
                    pass
        
        return df
    
    @staticmethod
    def _apply_polars_schema(df: "pl.DataFrame", schema: Dict[str, str]) -> "pl.DataFrame":
        """Apply schema to polars DataFrame.
        
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
                    try:
                        cast_expressions.append(pl.col(field).cast(polars_type))
                    except Exception:
                        # If cast fails, keep original
                        cast_expressions.append(pl.col(field))
                else:
                    cast_expressions.append(pl.col(field))
        
        if cast_expressions:
            try:
                return df.with_columns(cast_expressions)
            except Exception:
                return df
        
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
        >>> from autoframe import create_dataframe
        >>> from autoframe.sources.mongodb import MongoDBAdapter
        >>> 
        >>> # From adapter
        >>> adapter = MongoDBAdapter("mongodb://localhost:27017")
        >>> result = create_dataframe(adapter.query("mydb", "users"))
        >>> 
        >>> # From documents
        >>> docs = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        >>> result = create_dataframe(docs)
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