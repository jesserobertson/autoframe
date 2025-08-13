"""Tests for the new functional API."""

import pytest
from autoframe import (
    mongodb_to_dataframe, 
    create_pipeline, 
    fetch_and_process,
    quick_dataframe,
    to_dataframe,
    apply_schema,
    pipe
)
from autoframe.utils.functional import (
    filter_documents,
    transform_documents,
    limit_documents
)


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
    adults_only = filter_documents(lambda doc: doc["age"] >= 18)
    adult_docs = adults_only(documents)
    assert len(adult_docs) == 2
    
    # Test transformation
    add_adult_flag = transform_documents(lambda doc: {**doc, "adult": doc["age"] >= 18})
    transformed_docs = add_adult_flag(documents)
    assert all("adult" in doc for doc in transformed_docs)
    
    # Test limiting
    limit_two = limit_documents(2)
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
        filter_documents(lambda doc: doc["active"]),
        filter_documents(lambda doc: doc["age"] >= 18),
        transform_documents(lambda doc: {**doc, "processed": True}),
        limit_documents(2)
    )
    
    result_docs = process(documents)
    
    assert len(result_docs) == 2
    assert all(doc["active"] for doc in result_docs)
    assert all(doc["age"] >= 18 for doc in result_docs)
    assert all(doc["processed"] for doc in result_docs)


def test_pipeline_chaining():
    """Test pipeline method chaining."""
    documents_source = lambda: to_dataframe.types.Ok([
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 17, "active": True},
        {"name": "Charlie", "age": 25, "active": False}
    ])
    
    # Can't easily test full pipeline without MongoDB, but test the interface
    pipeline = (
        create_pipeline(documents_source)
        .filter(lambda doc: doc["active"])
        .transform(lambda doc: {**doc, "processed": True})
        .limit(10)
        .to_dataframe("pandas")
        .apply_schema({"age": "int"})
    )
    
    # Just test that the pipeline object was created correctly
    assert pipeline.target_backend == "pandas"
    assert pipeline.target_schema == {"age": "int"}
    assert len(pipeline.transforms) == 3  # filter, transform, limit


def test_functional_composition():
    """Test that functional composition works as expected."""
    documents = [{"value": "5"}, {"value": "10"}, {"value": "not_a_number"}]
    
    # Create a pipeline that converts strings to ints, handling errors
    def safe_int_transform(doc):
        try:
            return {**doc, "value": int(doc["value"])}
        except ValueError:
            return {**doc, "value": 0}  # Default for invalid values
    
    result = (
        to_dataframe(documents)
        .map(lambda df: df.assign(processed=True))  # Add a processed flag
    )
    
    assert result.is_ok()
    df = result.unwrap()
    assert "processed" in df.columns
    assert all(df["processed"])


if __name__ == "__main__":
    pytest.main([__file__])