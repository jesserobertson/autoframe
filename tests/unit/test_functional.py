"""Tests for the new functional API."""

import pandas as pd
import pytest

from autoframe import apply_schema, pipe, to_dataframe
from autoframe.utils.functional import filter, limit, transform, validate_columns


def test_to_dataframe_simple():
    """Test simple document to dataframe conversion."""
    documents = [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "LA"}
    ]

    result = to_dataframe(documents)
    assert result.is_ok()

    df = result.unwrap()
    assert len(df) == 2
    assert list(df.columns) == ["name", "age", "city"]


def test_apply_schema():
    """Test schema application."""
    documents = [{"age": "30", "active": "true"}]
    schema = {"age": "int", "active": "bool"}

    result = (
        to_dataframe(documents)
        .map(apply_schema(schema))
    )

    assert result.is_ok()
    df = result.unwrap()
    assert df["age"].dtype.name.startswith("int")


def test_document_transforms():
    """Test document transformation functions."""
    documents = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 17},
        {"name": "Charlie", "age": 25}
    ]

    # Test filtering
    adults_only = filter(lambda doc: doc["age"] >= 18)
    adult_docs = adults_only(documents)
    assert len(adult_docs) == 2

    # Test transformation
    add_adult_flag = transform(lambda doc: {**doc, "adult": doc["age"] >= 18})
    transformed_docs = add_adult_flag(documents)
    assert all("adult" in doc for doc in transformed_docs)

    # Test limiting
    limit_two = limit(2)
    limited_docs = limit_two(documents)
    assert len(limited_docs) == 2


def test_pipe_composition():
    """Test function composition with pipe."""
    documents = [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 17, "active": True},
        {"name": "Charlie", "age": 25, "active": False},
        {"name": "David", "age": 35, "active": True}
    ]

    process = pipe(
        filter(lambda doc: doc["active"]),
        filter(lambda doc: doc["age"] >= 18),
        transform(lambda doc: {**doc, "processed": True}),
        limit(2)
    )

    result_docs = process(documents)

    assert len(result_docs) == 2
    assert all(doc["active"] for doc in result_docs)
    assert all(doc["age"] >= 18 for doc in result_docs)
    assert all(doc["processed"] for doc in result_docs)


def test_validate_columns():
    """Test column validation function."""
    documents = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

    # Test successful validation
    validate_func = validate_columns(["name", "age"])
    result = to_dataframe(documents)
    validated_result = validate_func(result)

    assert validated_result.is_ok()
    df = validated_result.unwrap()
    assert len(df) == 2

    # Test failed validation
    validate_missing = validate_columns(["name", "age", "missing_column"])
    failed_result = validate_missing(result)

    assert failed_result.is_err()
    error = failed_result.unwrap_err()
    assert "missing_column" in str(error)


def test_result_chaining():
    """Test that Result types chain properly in our API."""
    documents = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    # Chain multiple operations
    result = (
        to_dataframe(documents)
        .map(apply_schema({"age": "int"}))
        .map(lambda df: df.assign(processed=True))
    )

    assert result.is_ok()
    df = result.unwrap()
    assert "processed" in df.columns
    assert df["age"].dtype.name.startswith("int")
    assert all(df["processed"])


def test_error_handling():
    """Test that errors are properly handled and propagated."""
    # Test invalid backend
    documents = [{"test": "value"}]
    result = to_dataframe(documents, backend="invalid_backend")

    assert result.is_err()
    error = result.unwrap_err()
    assert "Unsupported backend" in str(error)


def test_empty_documents():
    """Test handling of empty document lists."""
    result = to_dataframe([])

    assert result.is_ok()
    df = result.unwrap()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_schema_application_edge_cases():
    """Test schema application with edge cases."""
    documents = [
        {"age": "30", "score": "95.5", "active": "true", "name": "Alice"},
        {"age": "invalid", "score": "not_a_number", "active": "false", "name": "Bob"}
    ]

    schema = {"age": "int", "score": "float", "active": "bool"}

    result = (
        to_dataframe(documents)
        .map(apply_schema(schema))
    )

    assert result.is_ok()
    df = result.unwrap()

    # Should handle conversion gracefully
    assert len(df) == 2
    assert "name" in df.columns  # Non-schema columns preserved


def test_import_functionality():
    """Test that main imports work correctly."""
    import autoframe as af

    # Test that key functions are accessible
    assert hasattr(af, "to_dataframe")
    assert hasattr(af, "apply_schema")
    assert hasattr(af, "pipe")
    assert hasattr(af, "__version__")

    # Test version
    assert af.__version__ == "0.1.0"


if __name__ == "__main__":
    pytest.main([__file__])
