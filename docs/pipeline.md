# Pipeline Interface

AutoFrame provides high-level pipeline interfaces for creating data processing workflows. These combine the power of functional composition with an intuitive API.

## Quick Start Functions

### One-Function Solutions

For simple use cases, use the all-in-one functions:

```python
from autoframe import mongodb_to_dataframe

# Simple MongoDB to DataFrame conversion
result = mongodb_to_dataframe(
    connection_string="mongodb://localhost:27017",
    database="ecommerce",
    collection="orders",
    query={"status": "completed"},
    limit=1000,
    schema={"amount": "float", "date": "datetime"},
    backend="pandas"
)

if result.is_ok():
    df = result.unwrap()
    print(f"Retrieved {len(df)} orders")
```

### Quick DataFrame Creation

```python
from autoframe import quick_dataframe

# Minimal setup for rapid prototyping
result = quick_dataframe(
    "mongodb://localhost:27017",
    "analytics", 
    "events"
)

df = result.unwrap()  # Gets all data with default settings
```

## Fluent Pipeline Builder

### Creating Pipelines

The pipeline builder provides method chaining for complex workflows:

```python
from autoframe import pipeline, fetch_documents

# Define data source
fetch_users = lambda: fetch_documents(
    "mongodb://localhost:27017",
    "userdb",
    "profiles"
)

# Build processing pipeline
result = (
    pipeline(fetch_users)
    .filter(lambda doc: doc.get("active", False))
    .filter(lambda doc: doc.get("age", 0) >= 18)
    .transform(lambda doc: {
        **doc,
        "category": "adult_user",
        "processed_at": "2024-01-01"
    })
    .limit(5000)
    .to_dataframe(backend="pandas")
    .apply_schema({
        "age": "int",
        "signup_date": "datetime",
        "last_login": "datetime"
    })
    .validate(["id", "name", "email"])
    .execute()
)

if result.is_ok():
    df = result.unwrap()
    print(f"Pipeline produced {len(df)} records")
```

### Pipeline Methods

#### Document Filtering

```python
pipeline = (
    pipeline(data_source)
    .filter(lambda doc: doc["active"])                    # Simple boolean
    .filter(lambda doc: doc.get("age", 0) >= 21)          # Age filter
    .filter(lambda doc: "premium" in doc.get("tags", [])) # List membership
)
```

#### Document Transformation

```python
pipeline = (
    pipeline(data_source)
    .transform(lambda doc: {**doc, "processed": True})
    .transform(lambda doc: {
        **doc,
        "full_name": f"{doc.get('first', '')} {doc.get('last', '')}"
    })
    .transform(lambda doc: {
        **doc,
        "email": doc.get("email", "").lower()
    })
)
```

#### Limiting Results

```python
pipeline = (
    pipeline(data_source)
    .limit(1000)  # Take first 1000 after filters/transforms
)
```

#### DataFrame Configuration

```python
pipeline = (
    pipeline(data_source)
    .to_dataframe(backend="polars")  # Choose backend
    .apply_schema({
        "id": "int",
        "price": "float",
        "created_at": "datetime"
    })
)
```

#### Validation

```python
pipeline = (
    pipeline(data_source)
    .to_dataframe()
    .validate(["id", "name", "email"])  # Ensure required columns exist
)
```

## Functional Composition Style

### Using fetch_and_process

For those who prefer function calls over method chaining:

```python
from autoframe import fetch_and_process

result = fetch_and_process(
    connection_string="mongodb://localhost:27017",
    database="sales",
    collection="transactions",
    query={"amount": {"$gt": 100}},
    limit=5000,
    filter_fn=lambda doc: doc.get("status") == "completed",
    transform_fn=lambda doc: {
        **doc,
        "profit_margin": doc.get("revenue", 0) - doc.get("cost", 0)
    },
    schema={
        "amount": "float",
        "revenue": "float", 
        "cost": "float",
        "date": "datetime"
    },
    backend="pandas"
)
```

### Manual Composition

For maximum control, compose functions manually:

```python
from autoframe.sources.simple import fetch_documents
from autoframe.utils.functional import (
    pipe, filter_documents, transform_documents, 
    to_dataframe, apply_schema
)

# Define individual transformations
filter_active = filter_documents(lambda doc: doc["active"])
add_category = transform_documents(lambda doc: {**doc, "type": "user"})
clean_email = transform_documents(
    lambda doc: {**doc, "email": doc.get("email", "").lower()}
)

# Compose processing pipeline
process_users = pipe(
    filter_active,
    add_category, 
    clean_email
)

# Execute
docs_result = fetch_documents("mongodb://localhost:27017", "db", "users")
processed_result = docs_result.map(process_users)
df_result = processed_result.then(
    lambda docs: to_dataframe(docs).map(
        apply_schema({"age": "int", "created_at": "datetime"})
    )
)
```

## Advanced Pipeline Patterns

### Conditional Processing

```python
def create_conditional_pipeline(data_source, use_polars=True):
    """Create pipeline with conditional backend selection."""
    pipeline = (
        pipeline(data_source)
        .filter(lambda doc: doc.get("active", False))
    )
    
    if use_polars:
        pipeline = pipeline.to_dataframe(backend="polars")
    else:
        pipeline = pipeline.to_dataframe(backend="pandas")
    
    return pipeline.execute()
```

### Pipeline Reuse

```python
def create_user_pipeline(data_source, adult_only=True):
    """Reusable user processing pipeline."""
    pipeline = pipeline(data_source)
    
    if adult_only:
        pipeline = pipeline.filter(lambda doc: doc.get("age", 0) >= 18)
    
    return (
        pipeline
        .transform(lambda doc: {**doc, "processed_at": datetime.now().isoformat()})
        .to_dataframe()
        .apply_schema({
            "age": "int",
            "email": "string",
            "created_at": "datetime"
        })
        .validate(["id", "email"])
    )

# Use with different sources
users_result = create_user_pipeline(fetch_users).execute()
admins_result = create_user_pipeline(fetch_admins, adult_only=False).execute()
```

### Error Recovery

```python
def robust_pipeline(data_source):
    """Pipeline with error recovery."""
    try:
        # Try full processing
        result = (
            pipeline(data_source)
            .filter(lambda doc: doc["active"])
            .transform(lambda doc: {**doc, "processed": True})
            .to_dataframe(backend="polars")
            .apply_schema(complex_schema)
            .execute()
        )
        
        if result.is_ok():
            return result
    except Exception:
        pass
    
    # Fallback: minimal processing
    return (
        pipeline(data_source)
        .to_dataframe(backend="pandas")  # More reliable
        .execute()
    )
```

## Performance Optimization

### Batch Processing Pipelines

```python
from autoframe.sources.simple import fetch_in_batches

def create_batch_pipeline(connection_string, database, collection, batch_size=5000):
    """Process large collections in batches."""
    batches_result = fetch_in_batches(
        connection_string, database, collection, batch_size
    )
    
    if batches_result.is_err():
        return batches_result
    
    results = []
    for batch in batches_result.unwrap():
        # Process each batch with pipeline
        batch_result = (
            pipeline(lambda: Ok(batch))  # Wrap batch as source
            .filter(lambda doc: doc.get("active", False))
            .to_dataframe()
            .execute()
        )
        
        if batch_result.is_ok():
            results.append(batch_result.unwrap())
    
    # Combine results
    if results:
        combined_df = pd.concat(results, ignore_index=True)
        return Ok(combined_df)
    else:
        return Err(DataFrameCreationError("No successful batches"))
```

### Memory-Efficient Processing

```python
def streaming_pipeline(data_source, chunk_size=1000):
    """Generator-based pipeline for large datasets."""
    
    def process_chunk(docs):
        return (
            pipeline(lambda: Ok(docs))
            .filter(lambda doc: doc["active"])
            .transform(lambda doc: {**doc, "processed": True})
            .to_dataframe()
            .execute()
        )
    
    # Get all documents
    docs_result = data_source()
    if docs_result.is_err():
        yield docs_result
        return
    
    docs = docs_result.unwrap()
    
    # Process in chunks
    for i in range(0, len(docs), chunk_size):
        chunk = docs[i:i + chunk_size]
        yield process_chunk(chunk)
```

## Integration with External Systems

### Custom Data Sources

```python
def create_api_pipeline(api_client):
    """Pipeline that works with API data."""
    def fetch_api_data():
        try:
            data = api_client.get_data()
            return Ok(data)
        except Exception as e:
            return Err(DataSourceError(f"API error: {e}"))
    
    return (
        pipeline(fetch_api_data)
        .transform(lambda doc: {**doc, "source": "api"})
        .to_dataframe()
    )
```

### Multi-Source Pipelines

```python
def create_multi_source_pipeline(sources):
    """Combine data from multiple sources."""
    all_results = []
    
    for source_name, source_fn in sources.items():
        result = (
            pipeline(source_fn)
            .transform(lambda doc: {**doc, "source": source_name})
            .to_dataframe()
            .execute()
        )
        
        if result.is_ok():
            all_results.append(result.unwrap())
    
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        return Ok(combined)
    else:
        return Err(DataFrameCreationError("No successful sources"))
```

The pipeline interface provides flexibility for both simple and complex data processing workflows while maintaining the functional programming principles and error handling guarantees of the underlying AutoFrame library.