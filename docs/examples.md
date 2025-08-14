# Examples

This section provides practical examples for using AutoFrame in real-world scenarios.

## Basic MongoDB to DataFrame

```python
from autoframe import mongodb_to_dataframe

# Simple connection to local MongoDB
result = mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce", 
    "orders"
)

if result.is_ok():
    df = result.unwrap()
    print(f"Retrieved {len(df)} orders")
else:
    print(f"Error: {result.unwrap_err()}")
```

## Filtering and Schema Application

```python
from autoframe import mongodb_to_dataframe

# Query with filters and type conversion
result = mongodb_to_dataframe(
    connection_string="mongodb://localhost:27017",
    database="analytics",
    collection="events",
    query={"event_type": "purchase", "amount": {"$gt": 50}},
    limit=1000,
    schema={
        "amount": "float",
        "timestamp": "datetime",
        "user_id": "int"
    }
)

df = result.unwrap()
print(df.dtypes)
```

## Functional Pipeline Processing

```python
from autoframe import create_pipeline, fetch_documents
from autoframe.utils.functional import pipe, filter_documents, transform_documents

# Create a data fetcher
fetch_users = lambda: fetch_documents(
    "mongodb://localhost:27017", 
    "users", 
    "profiles"
)

# Build a processing pipeline
result = (
    create_pipeline(fetch_users)
    .filter(lambda doc: doc.get("active", False))
    .filter(lambda doc: doc.get("age", 0) >= 18)
    .transform(lambda doc: {**doc, "category": "adult_user"})
    .to_dataframe(backend="pandas")
    .apply_schema({"age": "int", "signup_date": "datetime"})
    .execute()
)

if result.is_ok():
    df = result.unwrap()
    print(f"Processed {len(df)} adult users")
```

## Batch Processing Large Datasets

```python
from autoframe.sources.simple import fetch_in_batches
from autoframe.utils.functional import to_dataframe

# Process large collections in batches
batches_result = fetch_in_batches(
    "mongodb://localhost:27017",
    "logs",
    "events", 
    batch_size=5000
)

if batches_result.is_ok():
    batches = batches_result.unwrap()
    
    for i, batch in enumerate(batches):
        df_result = to_dataframe(batch)
        if df_result.is_ok():
            df = df_result.unwrap()
            print(f"Batch {i+1}: {len(df)} records")
            # Process each batch...
```

## Error Handling with Result Types

```python
from autoframe import mongodb_to_dataframe

def safe_data_processing(connection_string: str, db: str, collection: str):
    """Example of functional error handling."""
    return (
        mongodb_to_dataframe(connection_string, db, collection)
        .map(lambda df: df.dropna())  # Clean data if successful
        .map(lambda df: df.head(100))  # Limit results
        .map_err(lambda err: f"Data processing failed: {err}")
    )

# Usage
result = safe_data_processing("mongodb://localhost:27017", "analytics", "events")

# Functional handling
result.match(
    ok=lambda df: print(f"Success: {len(df)} clean records"),
    err=lambda error: print(f"Error: {error}")
)
```

## Retry Logic for Unreliable Connections

```python
from autoframe import with_database_retry, fetch_documents

@with_database_retry
def fetch_remote_data():
    """Fetch with automatic retry on connection failures."""
    return fetch_documents(
        "mongodb://remote-server:27017",
        "production",
        "metrics",
        limit=1000
    )

# This will retry up to 3 times with exponential backoff
result = fetch_remote_data()
```

## Custom Data Transformations

```python
from autoframe.utils.functional import pipe, transform_documents, filter_documents
from autoframe import fetch_documents, to_dataframe

# Define transformations
add_computed_fields = transform_documents(
    lambda doc: {
        **doc,
        "total_value": doc.get("quantity", 0) * doc.get("price", 0),
        "is_premium": doc.get("price", 0) > 100
    }
)

filter_valid = filter_documents(
    lambda doc: doc.get("quantity", 0) > 0 and doc.get("price", 0) > 0
)

# Compose pipeline
process_orders = pipe(
    filter_valid,
    add_computed_fields
)

# Execute
docs_result = fetch_documents("mongodb://localhost:27017", "shop", "orders")
processed_result = docs_result.map(process_orders)
df_result = processed_result.then(to_dataframe)

if df_result.is_ok():
    df = df_result.unwrap()
    print(f"Processed {len(df)} valid orders")
    print(f"Premium orders: {df['is_premium'].sum()}")
```

## Working with Different Backends

```python
from autoframe import mongodb_to_dataframe

# Using Pandas (default)
pandas_result = mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "data", 
    "events",
    backend="pandas"
)

# Using Polars for better performance
polars_result = mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "data", 
    "events", 
    backend="polars"
)

# Both return Result types with the respective DataFrame type
if pandas_result.is_ok():
    pdf = pandas_result.unwrap()  # pandas.DataFrame
    
if polars_result.is_ok():
    plf = polars_result.unwrap()  # polars.DataFrame
```