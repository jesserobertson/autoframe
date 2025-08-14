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

## Architecture & Philosophy

### Core Principles (Following logerr Patterns)
- **Functional composition over classes**: Prefer simple, composable functions over complex class hierarchies
- **High composability**: Small functions that compose well using `pipe()`, `.map()`, `.and_then()`
- **Low complexity**: Avoid enterprise patterns - keep it simple and focused
- **Type safety**: Full mypy type checking with Result<T, E> and Option<T> types from logerr
- **Error handling**: Use Result types instead of exceptions for expected failure cases
- **Logging**: Automatic logging of errors through logerr integration

### Project Structure
```
autoframe/
├── autoframe/           # Main package
│   ├── sources/         # Data source functions (simple.py for MongoDB)
│   ├── utils/           # Functional utilities (functional.py - composable functions)
│   ├── pipeline.py      # Fluent pipeline interface
│   ├── quality/         # Data quality reporting and validation
│   └── config.py        # Configuration management
├── tests/               # Test suite (test_functional.py for functional API)
└── docs/                # Documentation
```

### API Usage
**Functional API:**
```python
import autoframe as af
import autoframe.mongodb as mongodb

# MongoDB to DataFrame - structured by data source
result = mongodb.to_dataframe(
    "mongodb://localhost:27017", "mydb", "users",
    query={"active": True}, 
    schema={"age": "int"}
)

# Function composition with pipe
process = af.pipe(
    filter(lambda d: d["active"]),  
    transform(lambda d: {**d, "processed": True})
)
result = af.fetch(conn, db, coll).map(process).then(af.to_dataframe)

# Fluent pipeline interface
result = (
    af.create_pipeline(fetch_fn)
    .filter(lambda d: d["active"])
    .transform(lambda d: {**d, "processed": True})
    .to_dataframe()
    .execute()
)
```


### Key Dependencies
- **logerr**: Functional Result/Option types and logging integration
- **pandas**: Primary dataframe library  
- **polars**: Alternative high-performance dataframes (optional)
- **pymongo**: MongoDB connectivity
- **tenacity**: Retry logic for data source connections

## Development Practices

### Code Style & Design Philosophy
- **Prefer functions over classes**: Use simple functions that compose well
- **Avoid complex abstractions**: Don't create enterprise patterns when simple functions suffice
- **Embrace functional composition**: Use `pipe()`, `.map()`, `.then()` for chaining operations
- **Keep functions small and focused**: Each function should do one thing well
- **Use Result types consistently**: For operations that can fail, always return Result<T, E>
- **Avoid imperative patterns**: Prefer functional alternatives to try/catch blocks

### Code Quality
- Always run `pixi run check-all` before committing changes
- Use pre-commit hooks for automated quality checks
- Maintain 100% type coverage with mypy
- Write comprehensive tests with pytest (focus on test_functional.py for new API)

### API Design Principles
- **Simple over complex**: Choose the simplest approach that works
- **Composable over monolithic**: Small functions that work together
- **Functional over object-oriented**: Prefer function composition to class inheritance
- **Result types for errors**: Use Result<T, E> for operations that can fail
- **Option types for nullable**: Use Option<T> for operations that may return empty results

### Testing Strategy
- **Focus on functional API**: Write tests for the new functional interface first
- **Property-based testing**: Use hypothesis for data validation and edge cases
- **Simple unit tests**: Test individual functions in isolation
- **Integration tests**: Test composed pipelines end-to-end
- **Avoid complex mocking**: Prefer simple test data over complex mocks

### Adding New Functionality
- **Start with simple functions**: Don't immediately reach for classes
- **Make it composable**: Ensure new functions work well with `pipe()`, `.map()`, `.then()` and other Result methods
- **Follow logerr patterns**: Look at logerr for inspiration on functional design
- **Test composability**: Verify that new functions compose well with existing ones

## Security Guidelines

### Critical Security Rules
- **NEVER commit credentials**: API keys, tokens, passwords, or connection strings must never be committed to git
- **Environment variables**: Use `.envrc` for local development (excluded from git via `.gitignore`)
- **Dependency security**: Regularly check dependencies for vulnerabilities
- **Input validation**: Sanitize all user inputs, especially database queries to prevent injection attacks

### Database Security
- **Connection strings**: Never hardcode database connection strings in code
- **Query sanitization**: Use parameterized queries and validate input to prevent MongoDB injection
- **Authentication**: Implement proper database authentication and connection pooling
- **Error handling**: Use Result types to handle database errors without exposing sensitive information

### Code Security Practices
- **Type safety**: Full mypy coverage helps prevent security bugs
- **Logging safety**: Ensure credentials are never logged (logerr integration helps with this)
- **Dependency pinning**: Pin dependency versions to prevent supply chain attacks
- **Pre-commit hooks**: Use automated security scanning before commits

### Security Tools (Optional but Recommended)
Add these to your development environment:
```bash
# Security scanning tools
pixi add bandit safety --feature dev

# Run security checks
pixi run security-scan    # Static analysis with bandit
pixi run dependency-check # Check for vulnerable dependencies
```

### Data Handling Security
- **Data validation**: Validate all incoming data using Result types
- **Sanitization**: Clean data before processing to prevent code injection
- **Privacy**: Be mindful of PII and sensitive data in dataframes and logs
- **Quality reports**: Ensure quality reports don't expose sensitive information

## Environment Setup

This project uses AWS Bedrock for Claude Code integration. Ensure direnv is installed and run `direnv allow` to load the necessary environment variables from `.envrc`.

The project targets Python 3.12+ and uses pixi for dependency management with conda-forge packages.