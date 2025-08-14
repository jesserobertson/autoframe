# Quick Start

Get up and running with AutoFrame in minutes! This guide shows you the essential patterns for functional data processing.

## Your First DataFrame

Let's start with the basics - converting documents to a DataFrame:

```python
import autoframe as af

# Sample data
documents = [
    {"name": "Alice", "age": "30", "city": "NYC", "active": True},
    {"name": "Bob", "age": "25", "city": "LA", "active": True}, 
    {"name": "Charlie", "age": "35", "city": "Chicago", "active": False}
]

# Simple conversion
result = af.to_dataframe(documents)

if result.is_ok():
    df = result.unwrap()
    print(f"✅ Created DataFrame with {len(df)} rows")
    print(df.head())
else:
    print(f"❌ Error: {result.unwrap_err()}")
```

## Adding Schema Conversion

Apply type conversions for cleaner data:

```python
# Define schema for type conversion
schema = {
    "age": "int",
    "active": "bool"
}

# Chain operations with .map()
result = (
    af.to_dataframe(documents)
    .map(af.apply_schema(schema))
)

df = result.unwrap()
print(f"Age column type: {df['age'].dtype}")  # int64
print(f"Active column type: {df['active'].dtype}")  # bool
```

## Document Processing Pipeline

Use `pipe()` for composable document transformations:

```python
from autoframe.utils.functional import filter_documents, transform_documents

# Create a processing pipeline
process = af.pipe(
    filter_documents(lambda doc: doc["active"]),          # Only active users
    transform_documents(lambda doc: {                     # Add computed fields
        **doc, 
        "age_group": "adult" if int(doc["age"]) >= 18 else "minor",
        "processed_at": "2024-01-01"
    })
)

# Apply the pipeline
processed_docs = process(documents)
result = af.to_dataframe(processed_docs)

df = result.unwrap()
print(f"Processed {len(df)} active users")
print(df[["name", "age", "age_group"]].head())
```

## Method Chaining Interface

For complex workflows, use the fluent pipeline interface:

```python
# Mock fetch function (replace with real data source)
def fetch_users():
    return af.to_dataframe(documents)

# Create pipeline with method chaining
pipeline = (
    af.create_pipeline(fetch_users)
    .filter(lambda doc: doc["active"])
    .transform(lambda doc: {**doc, "status": "processed"})
    .to_dataframe()
    .apply_schema({"age": "int"})
)

result = pipeline.execute()
df = result.unwrap()
print(f"Pipeline result: {len(df)} rows")
```

## Error Handling

AutoFrame uses Result types for elegant error handling:

```python
# This will fail
bad_result = af.to_dataframe(documents, backend="invalid")

if bad_result.is_err():
    error = bad_result.unwrap_err()
    print(f"Expected error: {error}")

# Chain operations safely
safe_result = (
    af.to_dataframe([])  # Empty is OK
    .map(lambda df: df.assign(new_column="added"))
    .map(af.apply_schema({"new_column": "string"}))
)

print(f"Safe chaining: {safe_result.is_ok()}")  # True
```

## MongoDB Integration

Connect to MongoDB and create DataFrames:

!!! note "MongoDB Required"
    These examples require a running MongoDB instance. See [Installation](installation.md) for setup instructions.

```python
# Simple MongoDB to DataFrame
result = af.mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce", 
    "orders",
    query={"status": "completed"},
    limit=1000,
    schema={"total": "float", "created_at": "datetime"}
)

if result.is_ok():
    df = result.unwrap()
    print(f"Retrieved {len(df)} completed orders")
```

## Functional Composition

Combine everything with functional patterns:

```python
# Define reusable transformations
add_metadata = transform_documents(lambda doc: {
    **doc, 
    "source": "api",
    "processed_at": "2024-01-01"
})

adults_only = filter_documents(lambda doc: int(doc["age"]) >= 18)

clean_schema = af.apply_schema({
    "age": "int",
    "active": "bool"
})

# Compose the full pipeline
full_pipeline = af.pipe(adults_only, add_metadata)

# Execute with error handling
result = (
    af.to_dataframe(documents)
    .map(lambda df: full_pipeline([doc for _, doc in df.iterrows()]))  # Apply to docs
    .then(af.to_dataframe)  # Back to DataFrame
    .map(clean_schema)  # Apply schema
)

if result.is_ok():
    final_df = result.unwrap()
    print("✅ Full pipeline completed successfully!")
    print(final_df.info())
```

## Next Steps

Now that you've seen the basics:

- [Examples](examples.md) - More real-world patterns
- [Core Concepts](concepts.md) - Understanding the functional approach  
- [API Reference](api/index.md) - Complete documentation
- [Pipeline Guide](pipeline.md) - Advanced pipeline patterns