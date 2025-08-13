"""Data source adapters for various backends."""

from autoframe.sources.base import DataSourceAdapter
from autoframe.sources.mongodb import MongoDBAdapter

__all__ = ["DataSourceAdapter", "MongoDBAdapter"]