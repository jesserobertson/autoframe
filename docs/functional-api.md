# Functional API

AutoFrame's functional API provides composable, pure functions that follow functional programming principles. All operations use Result types for error handling and avoid side effects.

## Core Functions

### Document Fetching

```python
from autoframe.sources.simple import fetch_documents, connect_mongodb

# Basic document fetching
result = fetch_documents(
    connection_string="mongodb://localhost:27017",
    database="mydb", 
    collection="users",
    query={"active": True},
    limit=100
)
```

### DataFrame Creation

```python
from autoframe.utils.functional import to_dataframe

documents = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

# Create DataFrame with backend choice
pandas_result = to_dataframe(documents, backend="pandas")
polars_result = to_dataframe(documents, backend="polars")
```

## Function Composition

### Using pipe()

The `pipe` function enables left-to-right function composition:

```python
from autoframe.utils.functional import (
    pipe, 
    filter_documents, 
    transform_documents,
    limit_documents
)

# Compose a processing pipeline
process_data = pipe(
    filter_documents(lambda doc: doc["active"]),
    transform_documents(lambda doc: {**doc, "processed_at": "2024-01-01"}),
    limit_documents(1000)
)

# Apply to documents
processed_docs = process_data(raw_documents)
```

### Chaining with Result Types

Chain operations using Result methods:

```python
from autoframe import fetch_documents
from autoframe.utils.functional import to_dataframe, apply_schema

result = (
    fetch_documents("mongodb://localhost:27017", "db", "collection")
    .then(lambda docs: to_dataframe(docs, backend="pandas"))
    .map(apply_schema({"age": "int", "salary": "float"}))
    .map(lambda df: df.head(100))
)

# Handle the result
result.match(
    ok=lambda df: print(f"Success: {len(df)} rows"),
    err=lambda error: print(f"Error: {error}")
)
```

## Document Transformations

### Filtering Documents

```python
from autoframe.utils.functional import filter_documents

# Create filter functions
active_users = filter_documents(lambda doc: doc.get("active", False))
adults = filter_documents(lambda doc: doc.get("age", 0) >= 18)
recent = filter_documents(lambda doc: doc.get("created_at", "") > "2024-01-01")

# Compose filters
adult_active_users = pipe(active_users, adults)
```

### Transforming Documents

```python
from autoframe.utils.functional import transform_documents

# Add computed fields
add_full_name = transform_documents(
    lambda doc: {
        **doc,
        "full_name": f"{doc.get('first_name', '')} {doc.get('last_name', '')}"
    }
)

# Normalize data
normalize_email = transform_documents(
    lambda doc: {**doc, "email": doc.get("email", "").lower()}
)

# Chain transformations
normalize_users = pipe(add_full_name, normalize_email)
```

### Limiting Results

```python
from autoframe.utils.functional import limit_documents

# Create limit functions
top_100 = limit_documents(100)
sample_10 = limit_documents(10)

# Use in pipelines
get_sample = pipe(
    filter_documents(lambda doc: doc["active"]),
    sample_10
)
```

## Schema Application

### Defining Schemas

```python
from autoframe.utils.functional import apply_schema

# Define type schemas
user_schema = {
    "id": "int",
    "age": "int", 
    "salary": "float",
    "hire_date": "datetime",
    "active": "bool",
    "name": "string"
}

order_schema = {
    "order_id": "int",
    "amount": "float",
    "order_date": "datetime", 
    "customer_id": "int"
}
```

### Applying Schemas

```python
# Create schema application functions
apply_user_schema = apply_schema(user_schema)
apply_order_schema = apply_schema(order_schema)

# Use in functional chains
result = (
    to_dataframe(documents)
    .map(apply_user_schema)
    .map(lambda df: df.dropna())  # Clean after type conversion
)
```

## Validation

### Column Validation

```python
from autoframe.utils.functional import validate_columns

# Create validators
require_user_fields = validate_columns(["id", "name", "email"])
require_order_fields = validate_columns(["order_id", "amount", "customer_id"])

# Use in pipelines
safe_processing = lambda df_result: (
    df_result
    .then(require_user_fields)
    .map(apply_user_schema)
)
```

## Error Handling Patterns

### Graceful Degradation

```python
from autoframe.utils.functional import to_dataframe

def safe_dataframe_creation(documents, preferred_backend="polars"):
    """Try preferred backend, fall back to pandas."""
    result = to_dataframe(documents, backend=preferred_backend)
    
    if result.is_err() and preferred_backend == "polars":
        # Fall back to pandas
        return to_dataframe(documents, backend="pandas")
    
    return result
```

### Error Recovery

```python
def process_with_fallback(documents):
    """Process documents with multiple fallback strategies."""
    
    # Try full processing
    full_result = (
        to_dataframe(documents)
        .map(apply_schema(complex_schema))
        .then(validate_columns(required_fields))
    )
    
    if full_result.is_ok():
        return full_result
    
    # Fallback: simple processing
    return (
        to_dataframe(documents)
        .map(lambda df: df.select_dtypes(include=[np.number, object]))
    )
```

## Advanced Composition

### Conditional Processing

```python
def conditional_transform(condition_fn, transform_fn):
    """Apply transformation only if condition is met."""
    def transformer(documents):
        if condition_fn(documents):
            return transform_documents(transform_fn)(documents)
        return documents
    return transformer

# Usage
process_large_datasets = conditional_transform(
    lambda docs: len(docs) > 1000,
    lambda doc: {**doc, "batch_processed": True}
)
```

### Branching Logic

```python
def branch_processing(documents, condition_fn, true_pipeline, false_pipeline):
    """Branch processing based on condition."""
    if condition_fn(documents):
        return true_pipeline(documents)
    else:
        return false_pipeline(documents)

# Usage
result = branch_processing(
    documents,
    lambda docs: len(docs) > 10000,
    true_pipeline=pipe(
        limit_documents(10000),
        transform_documents(lambda d: {**d, "sampled": True})
    ),
    false_pipeline=pipe(
        transform_documents(lambda d: {**d, "full_dataset": True})
    )
)
```

## Partial Application

### Creating Specialized Functions

```python
from functools import partial

# Create specialized fetchers
fetch_users = partial(
    fetch_documents,
    "mongodb://localhost:27017",
    "mydb", 
    "users"
)

fetch_orders = partial(
    fetch_documents,
    "mongodb://localhost:27017",
    "mydb",
    "orders"
)

# Create specialized transformers
add_timestamp = partial(
    transform_documents,
    lambda doc: {**doc, "processed_at": datetime.now().isoformat()}
)

# Create specialized validators
validate_user_data = partial(validate_columns, ["id", "name", "email"])
validate_order_data = partial(validate_columns, ["order_id", "amount"])
```

### Function Factories

```python
def create_processor(filters, transforms, schema=None):
    """Factory for creating document processors."""
    pipeline_steps = []
    
    # Add filters
    for filter_fn in filters:
        pipeline_steps.append(filter_documents(filter_fn))
    
    # Add transforms
    for transform_fn in transforms:
        pipeline_steps.append(transform_documents(transform_fn))
    
    # Create pipeline
    process_docs = pipe(*pipeline_steps)
    
    def processor(documents):
        # Process documents
        processed = process_docs(documents)
        
        # Convert to DataFrame
        df_result = to_dataframe(processed)
        
        # Apply schema if provided
        if schema and df_result.is_ok():
            df_result = df_result.map(apply_schema(schema))
        
        return df_result
    
    return processor

# Usage
user_processor = create_processor(
    filters=[
        lambda doc: doc.get("active", False),
        lambda doc: doc.get("age", 0) >= 18
    ],
    transforms=[
        lambda doc: {**doc, "category": "adult_user"}
    ],
    schema={"age": "int", "signup_date": "datetime"}
)
```

This functional API provides the building blocks for creating robust, composable data processing pipelines that handle errors gracefully and maintain referential transparency.