# Data Sources

AutoFrame provides modern Python 3.12+ interfaces for MongoDB integration with functional programming patterns, Result types, and pattern matching.

## MongoDB (Modern Functional Style)

### Direct Operations (Recommended)

The modern functional approach uses pattern matching and direct operations:

```python
import autoframe.mongodb as mongodb
from logerr import Ok, Err

# Modern Python 3.12+ style with pattern matching
result = mongodb.to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce",
    "orders", 
    query={"status": "completed"},
    limit=1000,
    schema={"amount": "float", "created_at": "datetime"}
)

# Handle with pattern matching
match result:
    case Ok(df):
        print(f"✅ Retrieved {len(df)} orders")
        print(df.head())
    case Err(error):
        print(f"❌ Error: {error}")
```

### Connection Management

#### Modern Connection API

```python
import autoframe.mongodb as mongodb
from logerr import Ok, Err

# Simple connection with automatic retry
result = mongodb.connect("mongodb://localhost:27017")

# Pattern matching for connection results
match result:
    case Ok(client):
        print("✅ Connected successfully")
        # Use client...
    case Err(error):
        print(f"❌ Connection failed: {error}")
```

### Document Fetching

#### Fetch with Functional Composition

```python
import autoframe.mongodb as mongodb
from autoframe.utils.functional import pipe, filter, transform

# Fetch documents and process functionally
result = mongodb.fetch(
    "mongodb://localhost:27017",
    "app", 
    "users",
    query={"active": True},
    limit=5000
)

# Process with pipeline
match result:
    case Ok(documents):
        # Define processing pipeline
        process_users = pipe(
            filter(lambda doc: doc.get("age", 0) >= 18),
            transform(lambda doc: {**doc, "category": "adult_user"})
        )
        
        processed = process_users(documents)
        print(f"✨ Processed {len(processed)} adult users")
    case Err(error):
        print(f"⚠️ Fetch failed: {error}")
```

#### Direct DataFrame Creation

```python
import autoframe.mongodb as mongodb

# Most common pattern - direct to DataFrame
result = mongodb.to_dataframe(
    "mongodb://localhost:27017",
    "sales",
    "transactions",
    query={"date": {"$gte": "2025-01-01"}},
    schema={
        "amount": "float",
        "date": "datetime", 
        "customer_id": "string"
    },
    backend="pandas"  # or "polars"
)

match result:
    case Ok(df):
        print(f"📊 DataFrame created: {len(df)} rows, {len(df.columns)} columns")
        print(df.dtypes)
    case Err(error):
        print(f"📉 DataFrame creation failed: {error}")
```

### Batch Processing

#### Large Dataset Handling

```python
import autoframe.mongodb as mongodb

# Handle large datasets with batching
result = mongodb.fetch_in_batches(
    "mongodb://localhost:27017",
    "analytics",
    "events", 
    batch_size=10000,
    query={"event_type": "purchase"}
)

match result:
    case Ok(batches):
        print(f"🔄 Retrieved {len(batches)} batches")
        
        # Process each batch
        for i, batch in enumerate(batches):
            print(f"Batch {i+1}: {len(batch)} documents")
            # Process batch...
            
    case Err(error):
        print(f"⚠️ Batch processing failed: {error}")
```

### Connection Strings

AutoFrame supports standard MongoDB connection strings:

```python
import autoframe.mongodb as mongodb

# Local connection
mongodb.connect("mongodb://localhost:27017")

# Remote with authentication  
mongodb.connect("mongodb://user:password@remote-server:27017/database")

# Replica set
mongodb.connect("mongodb://host1:27017,host2:27017/database?replicaSet=rs0")

# With options
mongodb.connect("mongodb://localhost:27017/db?maxPoolSize=50&connectTimeoutMS=5000")
```

## Alternative Approaches (Fallback)

### Traditional if/else Style

```python
import autoframe.mongodb as mongodb

# Traditional error handling (if you prefer)
result = mongodb.fetch(
    "mongodb://localhost:27017",
    "mydb",
    "users",
    query={"active": True},
    limit=500
)

# Traditional if/else handling
if result.is_ok():
    documents = result.unwrap()
    print(f"Retrieved {len(documents)} documents")
else:
    error = result.unwrap_err()
    print(f"Error: {error}")
```

### Imperative Style Connection

```python
import autoframe.mongodb as mongodb

# Direct client management (if needed)
client_result = mongodb.connect("mongodb://localhost:27017")

if client_result.is_ok():
    client = client_result.unwrap()
    # Use client directly for complex operations
    db = client["mydb"]
    collection = db["users"]
    # ... manual operations
    client.close()
```

## Best Practices

### Modern Functional Patterns (Recommended)

1. **Use pattern matching** for Result handling
2. **Prefer direct operations** like `mongodb.to_dataframe()`
3. **Compose with functional pipelines** using `pipe()`, `filter()`, `transform()`
4. **Chain operations** with `.map()`, `.then()` for error propagation

### Error Handling Guidelines

- **Always handle Results** - don't ignore potential errors
- **Use pattern matching** over if/else when possible  
- **Chain operations safely** with Result methods
- **Provide meaningful error context** in your error handling

This modern approach makes MongoDB integration both powerful and safe! 🚀

#### Query Examples

```python
# Date range queries
docs = fetch_documents(
    connection_string,
    "sales",
    "transactions", 
    query={
        "date": {
            "$gte": "2024-01-01",
            "$lt": "2024-02-01"
        }
    }
)

# Complex filters
docs = fetch_documents(
    connection_string,
    "users",
    "profiles",
    query={
        "$and": [
            {"active": True},
            {"age": {"$gte": 18}},
            {"tags": {"$in": ["premium", "vip"]}}
        ]
    }
)

# Text search
docs = fetch_documents(
    connection_string,
    "products",
    "catalog",
    query={"$text": {"$search": "laptop computer"}}
)
```

### Batch Processing

For large datasets, use batch processing to manage memory:

```python
from autoframe.sources.simple import fetch_in_batches

# Process large collection in batches
batches_result = fetch_in_batches(
    "mongodb://localhost:27017",
    "logs",
    "events",
    batch_size=10000,
    query={"level": "error"}
)

if batches_result.is_ok():
    batches = batches_result.unwrap()
    
    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}: {len(batch)} documents")
        
        # Process each batch
        df_result = to_dataframe(batch)
        if df_result.is_ok():
            df = df_result.unwrap()
            # ... process dataframe
```

### Counting Documents

```python
from autoframe.sources.simple import count_documents

# Count all documents
count_result = count_documents("mongodb://localhost:27017", "db", "collection")

# Count with query
count_result = count_documents(
    "mongodb://localhost:27017",
    "users", 
    "profiles",
    query={"active": True}
)

if count_result.is_ok():
    count = count_result.unwrap()
    print(f"Found {count} active users")
```

### Function Factories

Create specialized fetchers for common patterns:

```python
from autoframe.sources.simple import create_fetcher
from functools import partial

# Create specialized fetchers
fetch_users = create_fetcher(
    "mongodb://localhost:27017",
    "myapp",
    "users"
)

fetch_orders = create_fetcher(
    "mongodb://localhost:27017", 
    "myapp",
    "orders"
)

# Use them with different queries
active_users = fetch_users({"active": True}, 100)
recent_orders = fetch_orders({"date": {"$gte": "2024-01-01"}}, 500)
large_orders = fetch_orders({"amount": {"$gt": 1000}}, None)  # No limit
```

## Adapter Interface (Legacy)

For more complex scenarios requiring stateful connections:

### MongoDB Adapter

```python
from autoframe.sources.mongodb import MongoDBAdapter

# Create adapter
adapter = MongoDBAdapter("mongodb://localhost:27017")

# Connect with retry logic
connect_result = adapter.connect()
if connect_result.is_err():
    print(f"Connection failed: {connect_result.unwrap_err()}")
    exit(1)

# Query with the adapter
docs_result = adapter.query(
    database="ecommerce",
    collection="orders", 
    query={"status": "completed"},
    limit=1000
)

# Get schema information
schema_result = adapter.get_schema("ecommerce", "orders", sample_size=100)

# Clean up
adapter.disconnect()
```

### Context Manager Usage

```python
from autoframe.sources.mongodb import MongoDBAdapter

# Use as context manager for automatic cleanup
with MongoDBAdapter("mongodb://localhost:27017") as adapter:
    # Connection happens automatically
    
    # List databases
    dbs_result = adapter.list_databases()
    if dbs_result.is_ok():
        print(f"Databases: {dbs_result.unwrap()}")
    
    # List collections
    colls_result = adapter.list_collections("mydb")
    if colls_result.is_ok():
        print(f"Collections: {colls_result.unwrap()}")
    
    # Query data
    docs_result = adapter.query("mydb", "users", {"active": True})
    
    # Automatic disconnect when exiting context
```

### Query Builder

For complex query construction:

```python
from autoframe.sources.mongodb import MongoDBAdapter

adapter = MongoDBAdapter("mongodb://localhost:27017")
adapter.connect()

# Build complex queries
query_result = (
    adapter.query_builder("sales", "transactions")
    .filter(status="completed")
    .filter(amount__gt=100)  # MongoDB $gt operator
    .limit(1000)
    .execute()  # Returns Result[List[Dict], DataSourceError]
)

if query_result.is_ok():
    documents = query_result.unwrap()
```

## Retry and Error Handling

### Automatic Retries

All data source operations include automatic retry logic:

```python
from autoframe.sources.simple import fetch_documents

# Automatically retries on transient failures
docs_result = fetch_documents(
    "mongodb://unreliable-server:27017",
    "db",
    "collection"
)

# Retries happen automatically for:
# - Connection timeouts
# - Network errors  
# - Server unavailable errors
# - Lock contention
```

### Custom Retry Logic

```python
from autoframe.utils.retry import with_database_retry, retry_with_backoff

@with_database_retry
def custom_mongo_operation():
    # Your custom MongoDB operation
    client = pymongo.MongoClient("mongodb://localhost:27017")
    return list(client.db.collection.find({"complex": "query"}))

# Custom retry configuration
@retry_with_backoff(max_attempts=5, base_delay=2.0)
def resilient_fetch():
    return fetch_documents("mongodb://flaky-server:27017", "db", "coll")
```

### Error Recovery

```python
def fetch_with_fallback(primary_conn, fallback_conn, database, collection):
    """Try primary connection, fall back to secondary."""
    
    # Try primary
    result = fetch_documents(primary_conn, database, collection)
    if result.is_ok():
        return result
    
    # Try fallback
    print("Primary failed, trying fallback...")
    return fetch_documents(fallback_conn, database, collection)

# Usage
docs_result = fetch_with_fallback(
    "mongodb://primary:27017",
    "mongodb://secondary:27017", 
    "mydb",
    "important_data"
)
```

## Configuration

### Connection Settings

Configure MongoDB connections through the config system:

```python
from autoframe.config import get_config

config = get_config()

# Set MongoDB timeouts
config.set("data_sources", "mongodb", "connection_timeout", 10000)
config.set("data_sources", "mongodb", "server_selection_timeout", 5000)

# Set pool size
config.set("data_sources", "mongodb", "max_pool_size", 20)
```

### Environment Variables

Override settings with environment variables:

```bash
export AUTOFRAME_MONGODB_TIMEOUT=15000
export AUTOFRAME_DEFAULT_BACKEND=polars
export AUTOFRAME_CHUNK_SIZE=5000
```

## Performance Optimization

### Connection Pooling

```python
# MongoDB automatically pools connections
# Configure pool size in connection string
connection_string = "mongodb://localhost:27017/?maxPoolSize=50&minPoolSize=5"
```

### Batch Size Tuning

```python
# Adjust batch size based on document size and memory
small_docs_batches = fetch_in_batches(conn, db, coll, batch_size=50000)
large_docs_batches = fetch_in_batches(conn, db, coll, batch_size=1000)
```

### Query Optimization

```python
# Use projections to limit fields
docs = fetch_documents(
    connection_string,
    database,
    collection,
    query={"active": True},
    projection={"name": 1, "email": 1, "created_at": 1}  # Only these fields
)

# Use indexes for better performance
docs = fetch_documents(
    connection_string,
    database,
    collection,
    query={"indexed_field": "value"}  # Ensure indexed_field has an index
)
```

This comprehensive data source interface provides reliable, performant access to MongoDB while maintaining functional programming principles and comprehensive error handling.