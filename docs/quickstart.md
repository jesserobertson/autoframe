# Quick Start

Get up and running with AutoFrame using modern Python 3.12+ functional patterns! This guide showcases the recommended functional-first approach with match statements and Result types.

## Modern Functional Style (Recommended)

### Your First DataFrame with Pattern Matching

```python
import autoframe.mongodb as mongodb
from logerr import Ok, Err

# Modern Python 3.12+ approach with Result types
result = mongodb.to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce",
    "orders", 
    query={"status": "completed"},
    schema={"amount": "float", "date": "datetime"}
)

# Handle results with pattern matching (modern Python!)
match result:
    case Ok(df):
        print(f"✅ Success: {len(df)} orders loaded")
        print(df.head())
        # Continue processing...
    case Err(error):
        print(f"❌ Error: {error}")
        # Handle error appropriately...
```

### Functional Pipeline Composition

```python
import autoframe as af
import autoframe.mongodb as mongodb

# Build functional pipeline with automatic error handling
result = (
    af.pipeline(lambda: mongodb.fetch("mongodb://localhost:27017", "app", "users"))
    .filter(lambda doc: doc.get("active", False))
    .filter(lambda doc: doc.get("age", 0) >= 18)  # Adults only
    .transform(lambda doc: {**doc, "category": "adult_user"})
    .to_dataframe(backend="pandas")
    .apply_schema({
        "age": "int",
        "created_at": "datetime", 
        "last_login": "datetime"
    })
    .execute()
)

# Pattern match the pipeline result
match result:
    case Ok(df):
        print(f"🎉 Pipeline success: {len(df)} users processed")
        print(df.dtypes)  # Check applied schema
    case Err(error):
        print(f"💥 Pipeline failed: {error}")
```

### Pure Functional Composition 

```python
from autoframe.utils.functional import pipe, filter, transform, to_dataframe, apply_schema
import autoframe.mongodb as mongodb

# Define reusable transformation pipeline
process_users = pipe(
    filter(lambda doc: doc.get("active", True)),
    transform(lambda doc: {**doc, "processed_at": "2025-01-15"}),
    to_dataframe,
    lambda df_result: df_result.map(apply_schema({"age": "int"}))
)

# Execute with automatic error propagation
final_result = (
    mongodb.fetch("mongodb://localhost:27017", "myapp", "users")
    .then(process_users)
)

# Modern error handling
match final_result:
    case Ok(df):
        print(f"✨ Processed {len(df)} users successfully")
    case Err(error):
        print(f"⚠️  Processing failed: {error}")
```

### Advanced Result Chaining

```python
import autoframe.mongodb as mongodb

# Chain operations with automatic error propagation
result = (
    mongodb.to_dataframe("mongodb://localhost:27017", "sales", "transactions")
    .map(lambda df: df.dropna())  # Clean data if successful
    .map(lambda df: df.head(1000))  # Limit if successful  
    .map(lambda df: df.assign(processed=True))  # Add flag if successful
)

# Handle with modern pattern matching
match result:
    case Ok(df):
        print(f"🔥 Success: {len(df)} clean transactions")
        # Continue with analysis...
    case Err(error):
        print(f"🚨 Chain failed: {error}")
        # Handle error...
```

## Alternative Approaches (Fallback)

### Traditional if/else Style (if you prefer)

```python
import autoframe.mongodb as mongodb

# Traditional approach with explicit checks
result = mongodb.to_dataframe(
    "mongodb://localhost:27017",
    "shop",
    "products",
    query={"in_stock": True}
)

if result.is_ok():
    df = result.unwrap()
    print(f"Loaded {len(df)} products")
    # Process DataFrame...
else:
    error = result.unwrap_err()
    print(f"Error loading products: {error}")
```

### Method Chaining Style

```python
import autoframe as af
import autoframe.mongodb as mongodb

# Fluent interface for those who prefer method chaining
result = (
    af.pipeline(lambda: mongodb.fetch("mongodb://localhost:27017", "crm", "contacts"))
    .filter(lambda doc: doc.get("active", True))
    .transform(lambda doc: {**doc, "updated": True})
    .to_dataframe()
    .execute()
)

# Still use modern error handling
match result:
    case Ok(df): print(f"Processed {len(df)} contacts")
    case Err(error): print(f"Failed: {error}")
```

## Authentication & Security

For production use, manage credentials securely with environment variables:

```python
from autoframe.auth import create_config_from_env
import autoframe.mongodb as mongodb

# Set environment variables:
# export MONGODB_HOST=your-mongo-host.com
# export MONGODB_USERNAME=your-username
# export MONGODB_PASSWORD=your-password
# export MONGODB_DATABASE=your-database

config_result = create_config_from_env()

match config_result:
    case Ok(config):
        # Use secure configuration
        result = mongodb.to_dataframe(config, "mydb", "users", limit=100)
        
        match result:
            case Ok(df):
                print(f"🔐 Securely loaded {len(df)} users")
            case Err(error):
                print(f"💥 Database error: {error}")
                
    case Err(error):
        print(f"🔧 Configuration error: {error}")
        # Handle missing environment variables
```

Or create authenticated connections explicitly:

```python
from autoframe.auth import create_authenticated_config
import autoframe.mongodb as mongodb

# For production with SSL
config = create_authenticated_config(
    host="secure-mongo.example.com",
    username="api_user", 
    password="secure_password",
    database="production",
    ssl=True
)

result = mongodb.to_dataframe(config, "production", "analytics")

match result:
    case Ok(df):
        print(f"🔒 Secure connection: {len(df)} records")
    case Err(error):
        print(f"🚨 Secure connection failed: {error}")
```

## Working with Local Data

Start with local data before connecting to MongoDB:

```python
from autoframe.utils.functional import to_dataframe, apply_schema
from logerr import Ok, Err

# Sample data
documents = [
    {"name": "Alice", "age": "30", "city": "NYC", "active": True},
    {"name": "Bob", "age": "25", "city": "LA", "active": True},
    {"name": "Charlie", "age": "35", "city": "Chicago", "active": False}
]

# Convert with schema application
result = (
    to_dataframe(documents)
    .map(apply_schema({"age": "int", "active": "bool"}))
)

# Modern pattern matching
match result:
    case Ok(df):
        print(f"✅ Created DataFrame: {len(df)} rows")
        print(f"Age type: {df['age'].dtype}")  # int64  
        print(f"Active type: {df['active'].dtype}")  # bool
    case Err(error):
        print(f"❌ Conversion failed: {error}")
```

## Error Handling Best Practices

AutoFrame uses Result types for composable error handling:

```python
import autoframe.mongodb as mongodb

# This will fail gracefully
result = mongodb.to_dataframe(
    "mongodb://invalid-host:27017",
    "db", 
    "collection"
)

# Always use pattern matching for errors
match result:
    case Ok(df):
        print("This won't execute")
    case Err(error):
        print(f"Expected connection error: {error}")
        # Handle error gracefully - maybe try fallback data source
```

## Key Modern Python Features Used

AutoFrame leverages Python 3.12+ features:

- **Union types**: `str | None` instead of `Optional[str]`
- **Built-in generics**: `list[dict[str, Any]]` instead of `List[Dict[str, Any]]`
- **Pattern matching**: `match`/`case` for Result handling
- **Type statements**: `type UserId = int | str`
- **Function composition**: Pure functions with `.map()`, `.then()`

## Next Steps

Now that you've seen the modern functional approach:

- [Authentication Guide](authentication.md) - Complete security and credential management guide
- [Functional API Reference](functional-api.md) - Deep dive into function composition
- [Examples](examples.md) - Real-world patterns and recipes
- [Data Sources](data-sources.md) - MongoDB integration details
- [Pipeline Guide](pipeline.md) - Advanced pipeline patterns