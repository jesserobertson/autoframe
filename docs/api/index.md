# API Reference

AutoFrame provides a functional API built around simple, composable functions. The API is organized into several modules:

## Core Modules

### [Functional Utilities](functional.md)
The heart of AutoFrame - composable functions for data processing:

- `to_dataframe()` - Convert documents to DataFrames
- `apply_schema()` - Type conversion functions  
- `pipe()` - Function composition
- Document transformations: `filter_documents()`, `transform_documents()`, etc.

### [Pipeline Interface](pipeline.md)  
High-level pipeline creation and fluent interfaces:

- `mongodb_to_dataframe()` - One-function MongoDB to DataFrame
- `create_pipeline()` - Fluent method chaining interface
- `fetch_and_process()` - Imperative-style processing

### [Data Sources](sources.md)
Simple functions for data fetching:

- `fetch_documents()` - MongoDB document fetching
- `connect_mongodb()` - MongoDB connection handling
- Connection utilities and retry logic

### [Types](types.md)
Type definitions and error classes:

- Result and Option type aliases
- Custom error types  
- DataFrame and document type definitions

## Quick Reference

### Essential Functions

```python
import autoframe as af

# Core functions you'll use most
af.to_dataframe(documents)              # Documents → DataFrame
af.apply_schema(schema)                 # Schema application function  
af.pipe(fn1, fn2, fn3)                 # Function composition
af.fetch_documents(conn, db, coll)     # MongoDB fetching
af.mongodb_to_dataframe(conn, db, coll) # All-in-one MongoDB → DataFrame
```

### Functional Composition

```python
from autoframe.utils.functional import filter_documents, transform_documents

# Document processing functions
filter_documents(predicate)           # Filter function creator
transform_documents(transform_fn)     # Transform function creator  
limit_documents(count)               # Limiting function creator
validate_columns(required_cols)      # Validation function creator
```

### Pipeline Interface

```python
# Method chaining
af.create_pipeline(fetch_fn)
  .filter(predicate)
  .transform(transform_fn) 
  .limit(count)
  .to_dataframe()
  .apply_schema(schema)
  .execute()
```

## Error Handling

All functions return `Result[T, Error]` types:

```python
result = af.to_dataframe(documents)

if result.is_ok():
    df = result.unwrap()
    # Success path
else:
    error = result.unwrap_err()
    # Handle error
```

## Type Safety

AutoFrame is fully typed with mypy support:

```python
from autoframe.types import DataFrameResult, DocumentList

def process_data(docs: DocumentList) -> DataFrameResult:
    return af.to_dataframe(docs).map(af.apply_schema({"age": "int"}))
```

Browse the detailed API documentation for each module to learn more!