# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autoframe is a Python library for automated dataframe creation from various data sources (starting with MongoDB) with integrated data quality reporting. It builds on the functional programming patterns from the `logerr` library, using Result/Option types for robust data processing pipelines.

**Key Features:**
- Automated dataframe creation from MongoDB (with plans for other data sources)
- Integrated data quality reporting and validation
- Functional API with pipeline-style chaining using logerr's Result/Option types
- Support for both pandas and polars dataframes
- Comprehensive logging integration via logerr

## Development Commands

Use `pixi` for all development tasks:

```bash
# Run tests with coverage
pixi run test

# Run all tests (including doctests)
pixi run test-all

# Type checking
pixi run typecheck

# Code quality (linting and formatting)
pixi run quality

# Run all quality checks
pixi run check-all

# Clean build artifacts
pixi run clean

# Build package
pixi run build

# Serve documentation locally
pixi run docs-serve

# Build documentation
pixi run docs-build
```

## Architecture

### Core Principles
- **Functional first**: Prefer functional API patterns with pipeline-style chaining
- **Type safety**: Full mypy type checking with Result<T, E> and Option<T> types from logerr
- **Error handling**: Use Result types instead of exceptions for expected failure cases
- **Logging**: Automatic logging of errors and data quality issues through logerr integration
- **Composability**: Small, composable functions that can be chained together

### Project Structure
```
autoframe/
├── autoframe/           # Main package
│   ├── sources/         # Data source adapters (mongodb, etc.)
│   ├── frames/          # Dataframe creation and manipulation
│   ├── quality/         # Data quality reporting and validation
│   └── utils/           # Utility functions and helpers
├── tests/               # Test suite
└── docs/                # Documentation
```

### Key Dependencies
- **logerr**: Functional Result/Option types and logging integration
- **pandas**: Primary dataframe library
- **polars**: Alternative high-performance dataframes (optional)
- **pymongo**: MongoDB connectivity
- **tenacity**: Retry logic for data source connections
- **loguru**: Logging backend (via logerr)

## Development Practices

### Code Quality
- Always run `pixi run check-all` before committing changes
- Use pre-commit hooks for automated quality checks
- Maintain 100% type coverage with mypy
- Write comprehensive tests with pytest and hypothesis

### API Design
- Use Result<T, E> for operations that can fail (database connections, data validation)
- Use Option<T> for operations that may return empty results
- Prefer method chaining and functional composition
- Avoid imperative try/catch patterns when functional alternatives exist

### Testing
- Unit tests for all core functionality
- Property-based testing with hypothesis for data validation
- Integration tests for database connectivity
- Doctests in all public functions

### Data Source Integration
- Start with MongoDB support, design for extensibility to other sources
- Use adapter pattern for different data source types
- Handle connection failures gracefully with Result types
- Implement retry logic with tenacity for resilient connections

## Environment Setup

This project uses AWS Bedrock for Claude Code integration. Ensure direnv is installed and run `direnv allow` to load the necessary environment variables from `.envrc`.

The project targets Python 3.12+ and uses pixi for dependency management with conda-forge packages.