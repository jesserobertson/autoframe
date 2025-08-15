"""Basic tests to verify autoframe setup works."""

import pytest
from autoframe.types import DataFrameCreationError
from autoframe.frames.core import create_dataframe


def test_imports():
    """Test that all core modules can be imported."""
    import autoframe
    import autoframe.types
    import autoframe.mongodb
    import autoframe.frames.core
    assert autoframe.__version__ == "0.1.0"


def test_mongodb_import():
    """Test MongoDB module import."""
    import autoframe.mongodb as mongodb
    assert hasattr(mongodb, 'to_dataframe')
    assert hasattr(mongodb, 'fetch')
    assert hasattr(mongodb, 'connect')


def test_create_dataframe_from_documents():
    """Test dataframe creation from document list."""
    documents = [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "LA"}
    ]
    
    result = create_dataframe(documents)
    assert result.is_ok()
    
    df = result.unwrap()
    assert len(df) == 2
    assert list(df.columns) == ["name", "age", "city"]


def test_create_dataframe_empty():
    """Test dataframe creation with empty document list."""
    result = create_dataframe([])
    assert result.is_ok()
    
    df = result.unwrap()
    assert len(df) == 0


def test_create_dataframe_invalid_backend():
    """Test error handling for invalid backend."""
    documents = [{"test": 1}]
    result = create_dataframe(documents, backend="invalid")
    
    assert result.is_err()
    assert isinstance(result.unwrap_err(), DataFrameCreationError)


if __name__ == "__main__":
    pytest.main([__file__])