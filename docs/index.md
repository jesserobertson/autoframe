# AutoFrame

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/jesserobertson/autoframe/blob/main/LICENSE)

**AutoFrame** is a Python library for automated dataframe creation from various data sources with integrated data quality reporting. It leverages functional programming patterns with Rust-like Result/Option types for robust, composable data processing pipelines.

## Features

🔧 **Simple & Composable** - Built around small, composable functions that work together beautifully  
📊 **Functional First** - Uses Result/Option types from [logerr](https://github.com/jesserobertson/logerr) for robust error handling  
🐼 **Multi-backend** - Supports both pandas and polars dataframes  
🗄️ **MongoDB Integration** - Easy data fetching from MongoDB with functional query building  
⚡ **Type Safe** - Full mypy support with comprehensive type annotations  

## Philosophy

AutoFrame follows the **logerr philosophy** of functional programming:

- **High composability** over enterprise complexity
- **Simple functions** over class hierarchies  
- **Functional composition** with `pipe()`, `.map()`, `.then()`
- **Result types** for elegant error handling

## Quick Example

```python
import autoframe as af

# Simple composition
docs = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
result = af.to_dataframe(docs).map(af.apply_schema({"age": "int"}))

if result.is_ok():
    df = result.unwrap()
    print(f"Created DataFrame with {len(df)} rows")
```

## Pipeline Style

```python
# Function composition with pipe
from autoframe.utils.functional import filter_documents, transform_documents

process = af.pipe(
    filter_documents(lambda d: d["active"]),
    transform_documents(lambda d: {**d, "processed": True}),
)

result = (
    af.fetch_documents("mongodb://localhost", "mydb", "users")
    .map(process)
    .then(af.to_dataframe)
)
```

## Fluent Interface

```python
# Method chaining pipeline
result = (
    af.create_pipeline(lambda: af.fetch_documents(conn, db, coll))
    .filter(lambda d: d["active"])
    .transform(lambda d: {**d, "category": "user"})
    .limit(1000)
    .to_dataframe()
    .apply_schema({"age": "int", "created_at": "datetime"})
    .execute()
)
```

## Getting Started

Ready to dive in? Check out our:

- [Installation Guide](installation.md) - Get AutoFrame installed
- [Quick Start](quickstart.md) - Your first AutoFrame pipeline  
- [Examples](examples.md) - Real-world usage patterns
- [API Reference](api/index.md) - Complete function documentation

## Related Projects

- [logerr](https://github.com/jesserobertson/logerr) - Rust-like Result/Option types with logging integration