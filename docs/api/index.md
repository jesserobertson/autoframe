# API Reference

AutoFrame provides a modern Python 3.12+ functional API built around simple, composable functions with Result types and pattern matching. The API is organized into several modules:

## Core Modules (Modern Python 3.12+)

### [MongoDB Integration](sources.md)
Direct MongoDB operations with Result types and pattern matching:

- `mongodb.to_dataframe()` - Direct MongoDB to DataFrame conversion
- `mongodb.fetch()` - Document fetching with Result types  
- `mongodb.connect()` - Connection handling with automatic retry
- `mongodb.fetch_in_batches()` - Large dataset processing

### [Functional Utilities](functional.md)
Pure functions for composable data processing:

- `to_dataframe()` - Convert documents to DataFrames
- `apply_schema()` - Type conversion with modern syntax
- `pipe()` - Function composition for pipelines
- `filter()`, `transform()` - Document processing functions

### [Pipeline Interface](pipeline.md)  
Fluent interfaces for complex workflows:

- `pipeline()` - Method chaining with Result types
- Composable transformations with automatic error propagation
- Modern error handling with pattern matching

### [Quality Logging](quality.md)
Simple quality logging for Result failures and data completeness:

- `log_result_failure()` - Log when Results contain errors
- `log_document_completeness()` - Track missing fields in documents
- Pipeline operation tracking and automatic logging

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
af.pipeline(fetch_fn)
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