# AutoFrame

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AutoFrame is a Python library for functional dataframe creation from MongoDB with integrated quality logging. It leverages functional programming patterns with Result/Option types from [logerr](https://github.com/jesserobertson/logerr) for robust, composable data processing pipelines.

## Features

- 🔧 **Functional MongoDB integration** with automatic retry logic
- 📊 **Simple quality logging** for Result failures and data completeness tracking
- 🔗 **Composable pipelines** using functional programming with Result/Option types
- 🐼 **Multi-backend support** for both pandas and polars dataframes with duck typing
- 📝 **Comprehensive logging** integration via loguru and logerr
- ⚡ **Type-safe** with full mypy support and no exceptions for expected failures
- 🔄 **Automatic retry patterns** for database operations with exponential backoff

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

### Basic Usage

#### Simple MongoDB to DataFrame

```python
from autoframe import mongodb_to_dataframe

# One-function approach with automatic retry and quality logging
result = mongodb_to_dataframe(
    "mongodb://localhost:27017",
    "ecommerce",
    "orders",
    query={"status": "completed"},
    limit=1000,
    schema={"amount": "float", "date": "datetime"},
    backend="pandas"
)

# Handle the result functionally
if result.is_ok():
    df = result.unwrap()
    print(f"Created DataFrame with {len(df)} orders")
else:
    print(f"Error: {result.unwrap_err()}")
```

#### Functional Pipeline Composition

```python
from autoframe import create_pipeline, fetch_documents
from autoframe.utils.functional import pipe, filter_documents, transform_documents

# Define data source
fetch_users = lambda: fetch_documents(
    "mongodb://localhost:27017", 
    "app", 
    "users"
)

# Build composable pipeline with automatic quality logging
result = (
    create_pipeline(fetch_users)
    .filter(lambda doc: doc.get("active", False))
    .filter(lambda doc: doc.get("age", 0) >= 18)
    .transform(lambda doc: {**doc, "category": "adult_user"})
    .limit(5000)
    .to_dataframe(backend="pandas")
    .apply_schema({
        "age": "int",
        "created_at": "datetime",
        "last_login": "datetime"
    })
    .validate(["id", "email", "name"])
    .execute()
)

# Quality information is automatically logged at each step
df = result.unwrap()
```

#### Pure Functional Composition

```python
from autoframe.utils.functional import pipe, filter_documents, transform_documents, to_dataframe
from autoframe import fetch_documents

# Compose functions directly
process_data = pipe(
    filter_documents(lambda doc: doc["active"]),
    transform_documents(lambda doc: {**doc, "processed": True}),
    lambda docs: to_dataframe(docs).map(apply_schema({"age": "int"}))
)

# Execute pipeline
docs_result = fetch_documents("mongodb://localhost:27017", "db", "users")
final_result = docs_result.then(process_data)
```

### Quality Logging

AutoFrame includes simple quality logging that tracks Result failures and data completeness:

```python
from autoframe import log_document_completeness, log_result_failure

# Track document completeness
documents = [
    {"name": "Alice", "age": 30, "email": "alice@example.com"},
    {"name": "Bob", "age": 25},  # Missing email
]

logged_docs = log_document_completeness(
    documents, 
    expected_fields=["name", "email", "age"],
    operation="user_processing"
)

# Result failure logging (automatic in pipelines)
result = fetch_documents("mongodb://server:27017", "db", "collection")
logged_result = log_result_failure(result, "data_fetch", {"source": "mongodb"})
```

### Error Handling with Result Types

All operations return `Result[T, Error]` types for composable error handling:

```python
from autoframe import mongodb_to_dataframe

result = (
    mongodb_to_dataframe("mongodb://localhost:27017", "db", "collection")
    .map(lambda df: df.dropna())  # Clean data if successful
    .map(lambda df: df.head(100))  # Limit results
    .map_err(lambda err: f"Processing failed: {err}")
)

# Functional error handling
result.match(
    ok=lambda df: print(f"Success: {len(df)} clean records"),
    err=lambda error: print(f"Error: {error}")
)
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

AutoFrame follows functional programming principles with a clean, composable architecture:

#### Core Modules

- **`sources/simple.py`**: Simple functions for MongoDB data fetching with retry logic
- **`utils/functional.py`**: Composable functions for data transformation and schema application
- **`pipeline.py`**: High-level pipeline interfaces with method chaining
- **`quality.py`**: Simple quality logging for Result failures and data completeness
- **`utils/retry.py`**: Comprehensive retry patterns for database operations

#### Key Principles

- **Pure functional programming** with Result/Option types from logerr
- **No exceptions** for expected failures - all errors are values
- **Duck typing** for pandas/polars compatibility without isinstance checks
- **"Ask for forgiveness not permission"** (EAFP) Python philosophy
- **Composable functions** that chain naturally with `.then()`, `.map()`, `.unwrap_or()`
- **Automatic retry logic** for transient failures with exponential backoff

#### Design Philosophy

AutoFrame emphasizes:
- **High composability** over enterprise complexity
- **Simple functions** over class hierarchies  
- **Result-driven error handling** over try/catch blocks
- **Functional composition** over imperative programming
- **Quality logging** over complex data quality frameworks

## API Overview

### Essential Imports

```python
# Main API
from autoframe import (
    mongodb_to_dataframe,    # One-function MongoDB → DataFrame
    create_pipeline,         # Fluent pipeline builder
    fetch_documents,         # Simple document fetching
    to_dataframe,           # Document → DataFrame conversion
    apply_schema,           # Schema application function
    pipe,                   # Function composition
)

# Quality logging
from autoframe import (
    log_result_failure,           # Log Result[Err] with context
    log_document_completeness,    # Track missing fields
    track_pipeline_operation,     # Operation tracking decorator
)

# Retry utilities  
from autoframe import (
    with_database_retry,     # Database retry decorator
    with_network_retry,      # Network retry decorator
    retry_with_backoff,      # Custom retry patterns
)
```

### Function Composition Patterns

```python
# Document processing functions
from autoframe.utils.functional import (
    filter_documents,        # λ predicate → λ docs → filtered_docs
    transform_documents,     # λ transform → λ docs → transformed_docs
    limit_documents,         # λ count → λ docs → limited_docs
    validate_columns,        # λ required → λ df_result → validated_result
)

# Composable schema application
apply_user_schema = apply_schema({
    "age": "int",
    "created_at": "datetime", 
    "email": "string"
})

# Pipeline composition
user_pipeline = pipe(
    filter_documents(lambda doc: doc["active"]),
    transform_documents(add_computed_fields),
    lambda docs: to_dataframe(docs).map(apply_user_schema)
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