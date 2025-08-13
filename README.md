# AutoFrame

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AutoFrame is a Python library for automated dataframe creation from various data sources with integrated data quality reporting. It leverages functional programming patterns with Rust-like Result/Option types for robust, composable data processing pipelines.

## Features

- 🔧 **Automated dataframe creation** from MongoDB (with plans for other data sources) 
- 📊 **Integrated data quality reporting** and validation
- 🔗 **Functional API** with pipeline-style chaining using Result/Option types
- 🐼 **Multi-backend support** for both pandas and polars dataframes
- 📝 **Comprehensive logging** integration via logerr
- ⚡ **Type-safe** with full mypy support

## Quick Start

### Installation

AutoFrame uses [pixi](https://pixi.sh) for dependency management. First, ensure you have pixi installed:

```bash
# Install pixi (macOS)
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

```python
import autoframe as af
from logerr import Result

# Create a dataframe from MongoDB
result: Result[pd.DataFrame, str] = (
    af.DataSource.mongodb("mongodb://localhost:27017/mydb")
    .collection("users")
    .query({"active": True})
    .limit(1000)
    .create_dataframe()
)

# Handle the result functionally
df = result.map(
    lambda df: df.assign(processed_at=pd.Timestamp.now())
).unwrap_or_else(
    lambda error: print(f"Failed to create dataframe: {error}")
)

# Generate quality report
quality_report = af.QualityReport.from_dataframe(df)
print(quality_report.summary())
```

## Development

AutoFrame follows the same development practices as [logerr](https://github.com/jesserobertson/logerr), emphasizing functional programming patterns and comprehensive testing.

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
```

### Architecture

AutoFrame is built around three core modules:

- **`sources/`**: Data source adapters (MongoDB, PostgreSQL, etc.)
- **`frames/`**: Dataframe creation and manipulation utilities  
- **`quality/`**: Data quality assessment and reporting

The library emphasizes:
- **Functional composition** with Result/Option types
- **Type safety** with comprehensive mypy coverage
- **Error handling** without exceptions for expected failures
- **Composable pipelines** for complex data processing workflows

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the existing code style
4. Run `pixi run check-all` to ensure quality
5. Submit a pull request

## Project Status

AutoFrame is currently in early development (v0.1.0). The API may change as we refine the design based on user feedback.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [logerr](https://github.com/jesserobertson/logerr) - Rust-like Result/Option types with logging integration