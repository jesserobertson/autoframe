# Core Concepts

AutoFrame is built around several key concepts that enable reliable, composable data processing with functional programming principles.

## Functional Programming with Result Types

AutoFrame uses the [logerr](https://github.com/jesserobertson/logerr) library's `Result` and `Option` types to handle errors functionally, eliminating the need for try/catch blocks and making error handling explicit and composable.

### Result Types

All operations that might fail return a `Result[T, E]` type:

```python
from autoframe import fetch_documents

# Returns Result[List[Dict], DataSourceError]
result = fetch_documents("mongodb://localhost:27017", "db", "collection")

if result.is_ok():
    documents = result.unwrap()
    print(f"Got {len(documents)} documents")
else:
    error = result.unwrap_err()
    print(f"Error: {error}")
```

### Functional Composition

Results can be chained using functional methods:

```python
from autoframe import fetch_documents
from autoframe.utils.functional import to_dataframe, apply_schema

# Chain operations - errors propagate automatically
result = (
    fetch_documents("mongodb://localhost:27017", "shop", "orders")
    .then(to_dataframe)  # Convert to DataFrame
    .map(apply_schema({"price": "float", "date": "datetime"}))  # Apply schema
)

# Only succeeds if all steps succeed
if result.is_ok():
    df = result.unwrap()
```

## Data Sources

AutoFrame provides unified interfaces for different data sources while maintaining type safety and error handling.

### Simple Functions

The simplest approach uses standalone functions:

```python
from autoframe.sources.simple import fetch_documents, connect

# Direct function calls
client_result = connect("mongodb://localhost:27017")
docs_result = fetch_documents("mongodb://localhost:27017", "db", "coll")
```

### Adapters (Legacy)

For more complex scenarios, adapters provide stateful connections:

```python
from autoframe.sources.mongodb import MongoDBAdapter

adapter = MongoDBAdapter("mongodb://localhost:27017")
connect_result = adapter.connect()

if connect_result.is_ok():
    query_result = adapter.query("database", "collection", {"active": True})
```

## DataFrame Creation

AutoFrame supports both Pandas and Polars backends with a unified interface:

```python
from autoframe.utils.functional import to_dataframe

documents = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

# Create pandas DataFrame (default)
pandas_result = to_dataframe(documents, backend="pandas")

# Create polars DataFrame
polars_result = to_dataframe(documents, backend="polars")
```

### Schema Application

Type conversion is handled through schema specifications:

```python
schema = {
    "age": "int",
    "salary": "float", 
    "hire_date": "datetime",
    "active": "bool"
}

df_result = to_dataframe(documents).map(apply_schema(schema))
```

## Pipeline Processing

AutoFrame provides two approaches to data processing:

### Functional Composition

Use the `pipe` function to compose transformations:

```python
from autoframe.utils.functional import pipe, filter_documents, transform_documents

process_users = pipe(
    filter_documents(lambda doc: doc["active"]),
    transform_documents(lambda doc: {**doc, "processed": True}),
    lambda docs: to_dataframe(docs).unwrap()
)

result_docs = process_users(raw_documents)
```

### Fluent Interface

Use the pipeline builder for method chaining:

```python
from autoframe import pipeline

fetch_fn = lambda: fetch_documents("mongodb://localhost", "db", "users")

result = (
    pipeline(fetch_fn)
    .filter(lambda doc: doc["active"])
    .transform(lambda doc: {**doc, "category": "user"})
    .to_dataframe()
    .apply_schema({"age": "int"})
    .execute()
)
```

## Error Handling and Retry Logic

AutoFrame includes comprehensive retry logic for handling transient failures:

### Automatic Retries

Most database operations include automatic retry with exponential backoff:

```python
from autoframe import fetch_documents

# Automatically retries on connection failures
result = fetch_documents("mongodb://unreliable-server:27017", "db", "coll")
```

### Custom Retry Logic

Use retry decorators for custom operations:

```python
from autoframe import with_database_retry, with_network_retry

@with_database_retry
def custom_operation():
    # Your database operation here
    return some_db_call()

@with_network_retry  
def api_call():
    # Network operation with lighter retry
    return requests.get("https://api.example.com/data")
```

### Retry Conditions

Retries are triggered by specific error types:

- **Database errors**: Connection timeouts, server unavailable, deadlocks
- **Network errors**: Connection failures, timeouts, DNS issues
- **Transient errors**: Rate limiting, temporary overload

## Composability and Reusability

AutoFrame emphasizes composable, reusable functions:

### Function Factories

Create specialized functions for common operations:

```python
from autoframe.sources.simple import create_fetcher

# Create a specialized fetcher
fetch_orders = create_fetcher(
    "mongodb://localhost:27017", 
    "ecommerce", 
    "orders"
)

# Use it with different queries
recent_orders = fetch_orders({"date": {"$gte": "2024-01-01"}}, 100)
large_orders = fetch_orders({"amount": {"$gt": 1000}}, 50)
```

### Partial Application

Use `functools.partial` for customization:

```python
from functools import partial
from autoframe.utils.functional import apply_schema

# Create specialized schema appliers
apply_user_schema = partial(apply_schema, {
    "age": "int",
    "signup_date": "datetime"
})

apply_order_schema = partial(apply_schema, {
    "amount": "float", 
    "order_date": "datetime"
})
```

## Quality and Performance

### Batch Processing

Handle large datasets efficiently:

```python
from autoframe.sources.simple import fetch_in_batches

# Process in manageable chunks
batches_result = fetch_in_batches(
    "mongodb://localhost:27017",
    "logs", 
    "events",
    batch_size=10000
)

if batches_result.is_ok():
    for batch in batches_result.unwrap():
        # Process each batch individually
        df = to_dataframe(batch).unwrap()
        # ... process df
```

### Memory Management

Use streaming and lazy evaluation where possible:

```python
# Generator-based processing for large datasets
def process_large_collection(connection_string, db, collection):
    batches_result = fetch_in_batches(connection_string, db, collection, 5000)
    
    if batches_result.is_ok():
        for batch in batches_result.unwrap():
            df_result = to_dataframe(batch)
            if df_result.is_ok():
                yield df_result.unwrap()
```

These concepts work together to provide a robust, functional approach to data processing that handles errors gracefully and composes well for complex data workflows.