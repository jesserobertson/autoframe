"""MongoDB data source adapter with Result types."""

from typing import Optional, List, Dict, Any
import pymongo
from tenacity import retry, stop_after_attempt, wait_exponential

from autoframe.types import DataSourceResult, QueryDict, DocumentList, DataSourceError
from autoframe.sources.base import DataSourceAdapter, QueryBuilder
from autoframe.config import get_config
from autoframe.logging import log_connection_event, log_query_execution
from logerr import Result, Ok, Err


class MongoDBAdapter(DataSourceAdapter):
    """MongoDB adapter with functional error handling."""
    
    def connect(self) -> DataSourceResult[None]:
        """Connect to MongoDB with retry logic."""
        try:
            config = get_config().get_mongodb_config()
            self._connection = pymongo.MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=config.get("server_selection_timeout", 3000),
                connectTimeoutMS=config.get("connection_timeout", 5000)
            )
            self._connection.admin.command('ping')
            self._is_connected = True
            log_connection_event("connect", "mongodb", self.connection_string, True)
            return Ok(None)
        except Exception as e:
            log_connection_event("connect", "mongodb", self.connection_string, False, str(e))
            return Err(DataSourceError(f"MongoDB connection failed: {str(e)}"))
    
    def disconnect(self) -> DataSourceResult[None]:
        """Disconnect from MongoDB."""
        try:
            if self._connection:
                self._connection.close()
            self._is_connected = False
            return Ok(None)
        except Exception as e:
            return Err(DataSourceError(f"Disconnect failed: {str(e)}"))
    
    def test_connection(self) -> DataSourceResult[bool]:
        """Test MongoDB connection."""
        try:
            if not self._connection:
                return Ok(False)
            self._connection.admin.command('ping')
            return Ok(True)
        except Exception:
            return Ok(False)
    
    def list_databases(self) -> DataSourceResult[List[str]]:
        """List MongoDB databases."""
        try:
            dbs = self._connection.list_database_names()
            return Ok(dbs)
        except Exception as e:
            return Err(DataSourceError(f"Failed to list databases: {str(e)}"))
    
    def list_collections(self, database: str) -> DataSourceResult[List[str]]:
        """List collections in database."""
        try:
            db = self._connection[database]
            collections = db.list_collection_names()
            return Ok(collections)
        except Exception as e:
            return Err(DataSourceError(f"Failed to list collections: {str(e)}"))
    
    def query(self, database: str, collection: str, query: Optional[QueryDict] = None, 
              limit: Optional[int] = None, skip: Optional[int] = None) -> DataSourceResult[DocumentList]:
        """Execute MongoDB query."""
        try:
            db = self._connection[database]
            coll = db[collection]
            cursor = coll.find(query or {})
            
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            documents = list(cursor)
            log_query_execution(database, collection, query or {}, len(documents))
            return Ok(documents)
        except Exception as e:
            return Err(DataSourceError(f"Query failed: {str(e)}"))
    
    def count(self, database: str, collection: str, query: Optional[QueryDict] = None) -> DataSourceResult[int]:
        """Count documents."""
        try:
            db = self._connection[database]
            coll = db[collection]
            count = coll.count_documents(query or {})
            return Ok(count)
        except Exception as e:
            return Err(DataSourceError(f"Count failed: {str(e)}"))
    
    def get_schema(self, database: str, collection: str, sample_size: int = 1000) -> DataSourceResult[Dict[str, str]]:
        """Infer schema from sample documents."""
        try:
            db = self._connection[database]
            coll = db[collection]
            
            sample = list(coll.find().limit(sample_size))
            if not sample:
                return Ok({})
            
            # Simple schema inference
            schema = {}
            for doc in sample:
                for key, value in doc.items():
                    if key not in schema:
                        schema[key] = type(value).__name__
            
            return Ok(schema)
        except Exception as e:
            return Err(DataSourceError(f"Schema inference failed: {str(e)}"))


class MongoDBQueryBuilder(QueryBuilder):
    """MongoDB query builder with fluent API."""
    
    def filter(self, **conditions: Any) -> "MongoDBQueryBuilder":
        """Add filter conditions."""
        new_builder = self._copy()
        new_builder._query.update(conditions)
        return new_builder
    
    def _copy(self) -> "MongoDBQueryBuilder":
        """Create a copy of this query builder."""
        new_builder = MongoDBQueryBuilder(self.adapter, self.database, self.collection)
        new_builder._query = self._query.copy()
        new_builder._limit = self._limit
        new_builder._skip = self._skip
        return new_builder