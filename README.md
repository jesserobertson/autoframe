# AutoFrame

[![CI](https://github.com/jesserobertson/autoframe/workflows/CI/badge.svg)](https://github.com/jesserobertson/autoframe/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/jesserobertson/autoframe/branch/main/graph/badge.svg)](https://codecov.io/gh/jesserobertson/autoframe)

AutoFrame is a modern Python 3.12+ library for functional dataframe creation from MongoDB with integrated quality logging. It embraces modern Python features (match statements, union types, built-in generics) and functional programming patterns with Result/Option types from [logerr](https://github.com/jesserobertson/logerr) for robust, composable data processing pipelines.

## Features

- 🔧 **Modern Python 3.12+** with union types, match statements, and built-in generics
- 🔗 **Functional-first design** using Result/Option types and pure function composition
- 📊 **MongoDB integration** with automatic retry logic and transparent error handling
- 🐼 **Multi-backend support** for pandas and polars with duck typing
- ⚡ **Type-safe pipelines** with full mypy support and no exceptions for expected failures  
- 📝 **Transparent quality logging** via Result types and logerr integration
- 🔄 **Composable operations** that chain naturally with `.map()`, `.then()`, and match statements

## Quick Start

### Installation

AutoFrame uses [pixi](https://pixi.sh) for dependency management. First, ensure you have pixi installed:

```bash
# Install pixi (macOS/Linux)
curl -fsSL https://pixi.sh/install.sh | bash

# Or using conda/mamba
conda install -c conda-forge pixi
```

Then clone and set up the project:

```bash
git clone https://github.com/jesserobertson/autoframe.git
cd autoframe
pixi install
```

### Modern Functional Style (Recommended)

#### MongoDB to DataFrame with Match Statements

```python
import autoframe.mongodb as mongodb
from logerr import Ok, Err

# Modern Python 3.12+ style with Result types
result = mongodb.to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce", 
    "orders",
    query={"status": "completed"},
    schema={"amount": "float", "date": "datetime"}
)

# Handle results with pattern matching (modern Python)
match result:
    case Ok(df):
        print(f"✅ Success: {len(df)} orders loaded")
        # Continue processing...
    case Err(error):
        print(f"❌ Error: {error}")
        # Handle error appropriately...
```

#### Functional Pipeline Composition

```python
import autoframe as af
import autoframe.mongodb as mongodb

# Functional pipeline with automatic error handling and quality logging
result = (
    af.create_pipeline(lambda: mongodb.fetch("mongodb://localhost:27017", "app", "users"))
    .filter(lambda doc: doc.get("active", False))
    .filter(lambda doc: doc.get("age", 0) >= 18)
    .transform(lambda doc: {**doc, "category": "adult_user"})
    .to_dataframe(backend="pandas")
    .apply_schema({
        "age": "int", 
        "created_at": "datetime",
        "last_login": "datetime"
    })
    .execute()
)

# Pattern match the final result
match result:
    case Ok(df):
        print(f"Pipeline success: {len(df)} adult users processed")
    case Err(error):
        print(f"Pipeline failed at: {error}")
```

#### Pure Functional Composition with Result Chaining

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

# Handle the result functionally
match final_result:
    case Ok(df):
        print(f"Processed {len(df)} users successfully")
    case Err(error):
        print(f"Processing failed: {error}")
```

#### Advanced Result Chaining and Error Handling

```python
import autoframe.mongodb as mongodb
from autoframe.utils.functional import apply_schema

# Chain operations with automatic error propagation
result = (
    mongodb.to_dataframe("mongodb://localhost:27017", "sales", "transactions")
    .map(lambda df: df.dropna())  # Clean data if successful
    .map(lambda df: df.head(1000))  # Limit results if successful
    .then(lambda df: apply_schema({"amount": "float", "date": "datetime"})(df))
)

# Modern error handling with match
match result:
    case Ok(df):
        print(f"✅ Processed {len(df)} clean transactions")
        # Continue with analysis...
    case Err(error):
        print(f"❌ Pipeline failed: {error}")
        # Handle error appropriately...
```

### Alternative Approaches (Fallback)

#### Traditional if/else Style (if you prefer)

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
    # Handle error...
```

#### Method Chaining Style

```python
import autoframe as af
import autoframe.mongodb as mongodb

# Fluent interface for those who prefer method chaining
result = (
    af.create_pipeline(lambda: mongodb.fetch("mongodb://localhost:27017", "crm", "contacts"))
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

## Development

### Development Commands

```bash
# Run tests with coverage
pixi run test

# Type checking  
pixi run typecheck

# Code quality checks
pixi run quality

# Run all quality checks
pixi run check-all

# Format code
pixi run format

# Serve documentation
pixi run docs-serve

# Build documentation
pixi run docs-build
```

### Architecture

AutoFrame follows modern Python 3.12+ functional programming principles:

#### Core Modules

- **`mongodb.py`**: Modern MongoDB integration with `connect()`, `fetch()`, `to_dataframe()`
- **`utils/functional.py`**: Pure functions for data transformation and schema application  
- **`pipeline.py`**: Fluent pipeline interface with method chaining
- **`quality.py`**: Transparent quality logging through Result types
- **`utils/retry.py`**: Robust retry patterns with exponential backoff
- **`types.py`**: Modern type definitions using `type` statements and union syntax

#### Modern Python Features

- **Python 3.12+ syntax**: Union types (`A | B`), built-in generics (`list[T]`, `dict[K, V]`)
- **Pattern matching**: `match`/`case` statements for Result handling
- **Type safety**: Full mypy coverage with modern typing
- **Function composition**: Pure functions that chain with `.map()`, `.then()`, `.unwrap_or()`
- **Result types**: No exceptions for expected failures - all errors are values

#### Design Philosophy

AutoFrame prioritizes:
- **Modern Python first** - leveraging 3.12+ features for cleaner code
- **Functional composition** over imperative programming and classes
- **Pattern matching** over if/else chains for Result handling
- **Transparent error handling** through Result types and automatic logging
- **Simple, composable functions** over complex enterprise patterns
- **Duck typing** for pandas/polars compatibility without runtime checks

## API Overview

### Modern Functional API (Python 3.12+)

```python
# Core MongoDB operations
import autoframe.mongodb as mongodb
from logerr import Ok, Err

# Direct MongoDB operations (recommended)  
result = mongodb.to_dataframe("mongodb://localhost:27017", "db", "collection")
documents = mongodb.fetch("mongodb://localhost:27017", "db", "collection")
client = mongodb.connect("mongodb://localhost:27017")

# Pattern matching for results
match result:
    case Ok(df): print(f"Success: {len(df)} rows")
    case Err(error): print(f"Error: {error}")
```

### Functional Composition Patterns

```python
# Composable data processing
from autoframe.utils.functional import pipe, filter, transform, to_dataframe, apply_schema

# Build reusable transformation pipelines
process_users = pipe(
    filter(lambda doc: doc.get("active", True)),           # Filter active users
    transform(lambda doc: {**doc, "processed": True}),     # Add processing flag
    to_dataframe,                                          # Convert to DataFrame
    lambda df_result: df_result.map(apply_schema({"age": "int"}))  # Apply schema
)

# Use pipeline with automatic error propagation
result = mongodb.fetch("mongodb://localhost:27017", "app", "users").then(process_users)

# Handle with modern pattern matching
match result:
    case Ok(df): print(f"Processed {len(df)} users")
    case Err(error): print(f"Failed: {error}")
```

### Pipeline Interface (Alternative)

```python  
# Method chaining style (if preferred)
import autoframe as af

result = (
    af.create_pipeline(lambda: mongodb.fetch("mongodb://localhost:27017", "db", "users"))
    .filter(lambda doc: doc["active"])
    .transform(lambda doc: {**doc, "category": "active_user"})
    .to_dataframe(backend="pandas")
    .execute()
)
```

## Documentation

Full documentation is available at the [documentation site](https://jesserobertson.github.io/autoframe/) and includes:

- **[Getting Started Guide](docs/quickstart.md)** - Basic usage and concepts
- **[Functional API Reference](docs/functional-api.md)** - Composable functions and patterns
- **[Pipeline Interface](docs/pipeline.md)** - Method chaining and fluent APIs
- **[Data Sources](docs/data-sources.md)** - MongoDB integration and connection management
- **[Quality Logging](docs/quality.md)** - Result failure logging and completeness tracking
- **[Examples](docs/examples.md)** - Real-world usage patterns and recipes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the functional programming patterns
4. Run `pixi run check-all` to ensure quality
5. Submit a pull request

Please follow the existing patterns:
- Use Result types instead of exceptions for expected failures
- Prefer functional composition over imperative programming
- Write pure functions that compose naturally
- Include comprehensive docstring examples

## Project Status

AutoFrame is in active development (v0.1.0) with a stable functional API. The library is production-ready for MongoDB data processing with comprehensive error handling and quality logging.

**Current capabilities:**
- ✅ Complete MongoDB integration with retry logic
- ✅ Functional pipeline composition with Result types
- ✅ Quality logging for failures and data completeness  
- ✅ Pandas and Polars support with duck typing
- ✅ Comprehensive documentation with examples
- ✅ Full type safety with mypy

**Planned features:**
- 🔄 Additional data sources (PostgreSQL, REST APIs)
- 🔄 Enhanced batch processing capabilities  
- 🔄 Integration with data catalog systems

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- **[logerr](https://github.com/jesserobertson/logerr)** - Rust-like Result/Option types with logging integration (core dependency)
- **[sonde](https://github.com/jesserobertson/sonde)** - Scientific data quality analysis (recommended for advanced quality workflows)

---

*AutoFrame: Functional dataframe creation with quality logging* 🚀