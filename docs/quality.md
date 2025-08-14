# Quality Logging

AutoFrame provides simple quality logging utilities that integrate with Result types to capture basic information about data processing failures and missing data during pipeline operations.

## Overview

Quality logging in AutoFrame focuses on:

- **Result Failures**: Logging when operations return Err results
- **Document Completeness**: Tracking missing fields in document collections  
- **Pipeline Operations**: Monitoring data transformations and conversions
- **Basic Statistics**: Capturing simple metrics about data processing

This approach complements the functional Result-type architecture and leaves advanced scientific data quality analysis to specialized libraries like `sonde`.

## Automatic Quality Logging

### Pipeline Integration

Quality logging is automatically integrated into pipeline operations:

```python
from autoframe import mongodb_to_dataframe

# Quality logging happens automatically
result = mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce", 
    "orders"
)

# Logs will include:
# - Document fetch results
# - DataFrame conversion statistics  
# - Schema application results (if used)
# - Any failures with context
```

### Result Failure Logging

All Result failures are automatically logged with context:

```python
from autoframe import fetch_documents
from autoframe.quality import log_result_failure

# Manual logging for custom operations
result = fetch_documents("mongodb://bad-server:27017", "db", "collection")
logged_result = log_result_failure(result, "custom_fetch", {
    "retry_attempt": 1,
    "timeout": 5000
})

# If result is Err, logs:
# WARNING - Operation failed: custom_fetch
# {
#   "operation": "custom_fetch",
#   "error_type": "DataSourceError", 
#   "error_message": "Connection failed: ...",
#   "retry_attempt": 1,
#   "timeout": 5000
# }
```

## Document Completeness Logging

### Basic Completeness Checking

Track missing fields in document collections:

```python
from autoframe.quality import log_document_completeness

documents = [
    {"name": "Alice", "age": 30, "email": "alice@example.com"},
    {"name": "Bob", "age": 25},  # Missing email
    {"name": "Charlie", "email": "charlie@example.com"}  # Missing age
]

# Check completeness for expected fields
logged_docs = log_document_completeness(
    documents, 
    expected_fields=["name", "email", "age"],
    operation="user_processing"
)

# Logs:
# WARNING - Document completeness below 95% for user_processing
# {
#   "operation": "user_processing",
#   "total_documents": 3,
#   "overall_completeness_pct": 77.8,
#   "field_completeness": {
#     "name": 100.0,
#     "email": 66.7, 
#     "age": 66.7
#   }
# }
```

### Decorator-Based Logging

Use functions with automatic completeness logging:

```python
from autoframe.quality import with_document_quality_logging

@with_document_quality_logging(["name", "email", "age"], "user_filtering")
def filter_active_users(documents):
    return [doc for doc in documents if doc.get("active", True)]

# Automatically logs input and output completeness
filtered_docs = filter_active_users(user_documents)
```

## Pipeline Operation Tracking

### Operation Decorators

Track custom operations:

```python
from autoframe.quality import track_pipeline_operation

@track_pipeline_operation("complex_data_fetch", {"source": "external_api"})
def fetch_external_data():
    # Your data fetching logic
    return fetch_documents("mongodb://external:27017", "api_cache", "data")

# Logs start and completion of operation with timing
result = fetch_external_data()
```

### DataFrame Creation Statistics

Automatic logging of DataFrame creation:

```python
from autoframe.utils.functional import to_dataframe
from autoframe.quality import log_conversion_operation

documents = [{"id": 1, "value": "test"}, {"id": 2, "value": None}]
df_result = to_dataframe(documents)

# Log conversion statistics
logged_result = log_conversion_operation(df_result, "pandas", len(documents))

# Logs:
# INFO - DataFrame created successfully
# {
#   "operation": "dataframe_creation",
#   "rows": 2,
#   "columns": 2, 
#   "column_names": ["id", "value"],
#   "memory_usage_mb": 0.01,
#   "null_counts": {"value": 1},
#   "total_nulls": 1
# }
```

## Batch Processing Logging

### Batch Statistics

Log statistics about batch operations:

```python
from autoframe.sources.simple import fetch_in_batches
from autoframe.quality import log_batch_processing_stats

batches_result = fetch_in_batches(
    "mongodb://localhost:27017",
    "logs",
    "events", 
    batch_size=1000
)

if batches_result.is_ok():
    batches = batches_result.unwrap()
    logged_batches = log_batch_processing_stats(batches, "event_processing")
    
    # Logs:
    # INFO - Batch processing stats for event_processing
    # {
    #   "batch_count": 15,
    #   "total_documents": 14500,
    #   "avg_batch_size": 966.7,
    #   "min_batch_size": 500,
    #   "max_batch_size": 1000
    # }
```

## Custom Quality Functions

### Wrapping Existing Functions

Add quality logging to any Result-returning function:

```python
from autoframe.quality import with_quality_logging
from autoframe.sources.simple import fetch_documents

# Wrap existing function with logging
logged_fetch = with_quality_logging(
    fetch_documents,
    operation="monitored_fetch",
    context={"monitoring": True, "priority": "high"}
)

# Use wrapped function
result = logged_fetch("mongodb://localhost:27017", "db", "important_data")
```

### Integration with Pipelines

Quality logging works seamlessly with functional composition:

```python
from autoframe.utils.functional import pipe, filter_documents, transform_documents
from autoframe.quality import log_document_completeness

# Create pipeline with quality checkpoints
process_users = pipe(
    lambda docs: log_document_completeness(docs, ["name", "email"], "input"),
    filter_documents(lambda doc: doc.get("active", False)),
    transform_documents(lambda doc: {**doc, "processed": True}),
    lambda docs: log_document_completeness(docs, ["name", "email"], "output")
)

# Execute with automatic logging at each stage
processed = process_users(raw_documents)
```

## Configuration

### Logging Levels

Quality logging respects standard logging configuration:

```python
from loguru import logger

# Set quality logging level
logger.configure(extra={"quality_logging": True})

# Adjust levels for different operations
logger.configure(handlers=[{
    "sink": "quality.log",
    "level": "INFO",
    "filter": lambda record: "operation" in record["extra"]
}])
```

### Integration with AutoFrame Config

```python
from autoframe.config import get_config

config = get_config()

# Enable detailed quality logging
config.set("logging", "log_query_details", True)
config.set("logging", "enable_performance_logging", True)
```

## Practical Examples

### Complete Pipeline with Quality Logging

```python
from autoframe import create_pipeline, fetch_documents
from autoframe.quality import log_document_completeness

# Define data source with quality logging
def fetch_users_with_logging():
    result = fetch_documents("mongodb://localhost:27017", "app", "users")
    return result.map(lambda docs: log_document_completeness(
        docs, 
        ["id", "name", "email", "created_at"],
        "user_fetch"
    ))

# Create pipeline (quality logging is automatic)
result = (
    create_pipeline(fetch_users_with_logging)
    .filter(lambda doc: doc.get("active", False))  
    .transform(lambda doc: {**doc, "processed_at": "2024-01-01"})
    .to_dataframe()
    .apply_schema({"id": "int", "created_at": "datetime"})
    .execute()
)

# Quality information is logged at each step:
# - Document fetch completeness
# - Filter transformation counts
# - DataFrame conversion statistics
# - Schema application results
```

### Error Monitoring

```python
from autoframe import mongodb_to_dataframe
from loguru import logger

# Set up error monitoring
@logger.catch
def monitored_data_processing():
    result = mongodb_to_dataframe(
        "mongodb://production-server:27017",
        "analytics",
        "events",
        query={"date": {"$gte": "2024-01-01"}},
        schema={"event_id": "int", "timestamp": "datetime"}
    )
    
    if result.is_err():
        # Error details are already logged by quality system
        # Just handle the business logic
        return handle_fallback_data()
    
    return result.unwrap()

# All failures and quality issues are automatically logged
df = monitored_data_processing()
```

This simple quality logging approach provides visibility into data processing operations while maintaining the functional programming philosophy and allowing specialized libraries to handle complex data quality analysis.