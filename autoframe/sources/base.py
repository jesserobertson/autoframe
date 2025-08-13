"""Abstract base classes for data source adapters.

This module defines the interface that all data source adapters must implement,
providing a consistent functional API for different data backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Iterator, Any, Dict, List
from contextlib import contextmanager

from autoframe.types import (
    DataSourceResult, 
    DataFrameResult,
    DataFrameType,
    QueryDict,
    DocumentList,
    ConnectionString,
    DatabaseName,
    CollectionName,
    DataSourceError
)
from logerr import Result, Option


class DataSourceAdapter(ABC):
    """Abstract base class for all data source adapters.
    
    This class defines the interface that all data source implementations must follow,
    emphasizing functional programming patterns and Result-based error handling.
    """
    
    def __init__(self, connection_string: ConnectionString) -> None:
        """Initialize the data source adapter.
        
        Args:
            connection_string: Connection string for the data source
            
        Note:
            The actual connection is not established until connect() is called.
        """
        self.connection_string = connection_string
        self._connection: Optional[Any] = None
        self._is_connected = False
    
    @abstractmethod
    def connect(self) -> DataSourceResult[None]:
        """Establish connection to the data source.
        
        Returns:
            Result[None, DataSourceError]: Success or error information
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> DataSourceResult[None]:
        """Close connection to the data source.
        
        Returns:
            Result[None, DataSourceError]: Success or error information
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> DataSourceResult[bool]:
        """Test if the connection is alive and working.
        
        Returns:
            Result[bool, DataSourceError]: Connection status or error
        """
        pass
    
    @abstractmethod
    def list_databases(self) -> DataSourceResult[List[DatabaseName]]:
        """List available databases.
        
        Returns:
            Result[List[str], DataSourceError]: Database names or error
        """
        pass
    
    @abstractmethod
    def list_collections(self, database: DatabaseName) -> DataSourceResult[List[CollectionName]]:
        """List collections/tables in a database.
        
        Args:
            database: Name of the database
            
        Returns:
            Result[List[str], DataSourceError]: Collection names or error
        """
        pass
    
    @abstractmethod
    def query(
        self,
        database: DatabaseName,
        collection: CollectionName,
        query: Optional[QueryDict] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> DataSourceResult[DocumentList]:
        """Execute a query against the data source.
        
        Args:
            database: Database name
            collection: Collection/table name
            query: Query parameters (implementation-specific)
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            
        Returns:
            Result[List[Dict], DataSourceError]: Query results or error
        """
        pass
    
    @abstractmethod
    def count(
        self,
        database: DatabaseName,
        collection: CollectionName,
        query: Optional[QueryDict] = None
    ) -> DataSourceResult[int]:
        """Count documents matching the query.
        
        Args:
            database: Database name
            collection: Collection/table name  
            query: Query parameters (implementation-specific)
            
        Returns:
            Result[int, DataSourceError]: Document count or error
        """
        pass
    
    @abstractmethod
    def get_schema(
        self,
        database: DatabaseName,
        collection: CollectionName,
        sample_size: int = 1000
    ) -> DataSourceResult[Dict[str, str]]:
        """Infer schema from a sample of documents.
        
        Args:
            database: Database name
            collection: Collection/table name
            sample_size: Number of documents to sample for schema inference
            
        Returns:
            Result[Dict[str, str], DataSourceError]: Field names to types mapping or error
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if currently connected to the data source.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected
    
    @contextmanager
    def connection_context(self):
        """Context manager for automatic connection handling.
        
        Usage:
            with adapter.connection_context():
                result = adapter.query(...)
        """
        connect_result = self.connect()
        if connect_result.is_err():
            raise connect_result.unwrap_err()
            
        try:
            yield self
        finally:
            disconnect_result = self.disconnect()
            if disconnect_result.is_err():
                # Log the disconnect error but don't raise it
                # as we don't want to mask the original operation
                pass


class QueryBuilder(ABC):
    """Abstract base class for building queries in a functional style.
    
    This class provides a fluent interface for constructing queries
    that can be executed against different data sources.
    """
    
    def __init__(self, adapter: DataSourceAdapter, database: DatabaseName, collection: CollectionName):
        """Initialize the query builder.
        
        Args:
            adapter: Data source adapter to execute queries against
            database: Database name
            collection: Collection/table name
        """
        self.adapter = adapter
        self.database = database
        self.collection = collection
        self._query: QueryDict = {}
        self._limit: Optional[int] = None
        self._skip: Optional[int] = None
    
    @abstractmethod
    def filter(self, **conditions: Any) -> "QueryBuilder":
        """Add filter conditions to the query.
        
        Args:
            **conditions: Field-value pairs for filtering
            
        Returns:
            QueryBuilder: New query builder with added conditions
        """
        pass
    
    def limit(self, count: int) -> "QueryBuilder":
        """Limit the number of results.
        
        Args:
            count: Maximum number of results to return
            
        Returns:
            QueryBuilder: New query builder with limit applied
        """
        new_builder = self._copy()
        new_builder._limit = count
        return new_builder
    
    def skip(self, count: int) -> "QueryBuilder":
        """Skip a number of results.
        
        Args:
            count: Number of results to skip
            
        Returns:
            QueryBuilder: New query builder with skip applied
        """
        new_builder = self._copy()
        new_builder._skip = count
        return new_builder
    
    def execute(self) -> DataSourceResult[DocumentList]:
        """Execute the constructed query.
        
        Returns:
            Result[List[Dict], DataSourceError]: Query results or error
        """
        return self.adapter.query(
            database=self.database,
            collection=self.collection,
            query=self._query,
            limit=self._limit,
            skip=self._skip
        )
    
    def count(self) -> DataSourceResult[int]:
        """Count documents matching the query.
        
        Returns:
            Result[int, DataSourceError]: Document count or error
        """
        return self.adapter.count(
            database=self.database,
            collection=self.collection,
            query=self._query
        )
    
    @abstractmethod
    def _copy(self) -> "QueryBuilder":
        """Create a copy of this query builder.
        
        Returns:
            QueryBuilder: New instance with same configuration
        """
        pass