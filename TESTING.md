# Testing Guide

This document explains how to run tests for the autoframe library.

## Test Structure

Tests are organized into two main categories:

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and modules in isolation
- **Dependencies**: No external services required
- **Mocking**: Use mocked MongoDB connections and data
- **Speed**: Fast execution
- **Coverage**: Focus on code paths and error handling

**Files:**
- `test_basic.py` - Basic library functionality
- `test_functional.py` - Functional API and pipeline operations  
- `test_mongodb_mocked.py` - MongoDB functionality with mocked connections

### Integration Tests (`tests/integration/`)
- **Purpose**: Test end-to-end functionality with real MongoDB
- **Dependencies**: Requires running MongoDB instance
- **Data**: Uses real MongoDB with test data
- **Speed**: Slower execution
- **Coverage**: Focus on real-world scenarios

**Files:**
- `test_mongodb_integration.py` - MongoDB integration tests with real database

## Running Tests

### Unit Tests Only (Recommended for Development)
```bash
# Run unit tests with coverage
pixi run test

# Run unit tests quickly (fail fast)
pixi run test-fast
```

### Coverage Reporting
```bash
# Run unit tests with coverage (includes HTML and XML reports)
pixi run test

# Run integration tests with coverage (appends to existing coverage)
pixi run test-integration

# Generate coverage report in terminal
pixi run test-coverage

# Generate HTML coverage report
pixi run test-coverage-html

# Combined unit + integration tests with coverage
pixi run test-with-integration
```

### Integration Tests Only
```bash
# Start test database first (requires Docker)
pixi run test-db-start

# Run integration tests
pixi run test-integration

# Stop test database when done
pixi run test-db-stop
```

### All Tests
```bash
# Run all tests including doctests
pixi run test-all
```

## Test Database Setup

Integration tests require a MongoDB instance. Two options:

### Option 1: Docker Compose (Recommended)
```bash
# Start MongoDB with test data
pixi run test-db-start

# Check database status
pixi run test-db-status

# Reset database with fresh data
pixi run test-db-reset

# Stop database
pixi run test-db-stop
```

### Option 2: Local MongoDB
Set environment variable and ensure MongoDB is running:
```bash
export MONGODB_URI="mongodb://localhost:27017"
pixi run test-integration
```

## Test Database Management

The `scripts/test-db.sh` script provides convenient database management:

```bash
# Available commands
./scripts/test-db.sh start     # Start MongoDB container
./scripts/test-db.sh stop      # Stop MongoDB container  
./scripts/test-db.sh restart   # Restart MongoDB container
./scripts/test-db.sh reset     # Reset with fresh data
./scripts/test-db.sh status    # Show container status
./scripts/test-db.sh logs      # Show container logs
./scripts/test-db.sh shell     # Connect to MongoDB shell
./scripts/test-db.sh test      # Run integration tests
```

## Test Data

Integration tests use the following test collections:

### Users Collection
- Sample user records with various attributes (name, age, active status, etc.)
- Used for basic fetch, filter, and schema operations

### Orders Collection  
- Sample e-commerce orders linked to users
- Used for complex queries and aggregations

### Products Collection
- Sample product catalog
- Used for inventory and relationship testing

### Analytics Collection
- Time-series analytics data
- Used for date-based queries and reporting

## Continuous Integration

The test setup is designed for CI/CD pipelines:

1. **Unit tests**: Run in all CI builds (fast, no dependencies)
2. **Integration tests**: Run when MongoDB service is available
3. **Auto-skip**: Integration tests automatically skip if MongoDB unavailable

## Best Practices

### When Writing Unit Tests
- Mock external dependencies (MongoDB, network calls)
- Test error conditions and edge cases
- Focus on testing business logic
- Keep tests fast and isolated

### When Writing Integration Tests  
- Test real-world scenarios
- Use the provided test data fixtures
- Test actual MongoDB operations
- Verify data transformations work end-to-end

### Test Naming
- Unit tests: `test_<function_name>_<scenario>`
- Integration tests: `test_<feature>_<scenario>_integration`
- Mocked tests: `test_<function_name>_<scenario>_mocked`

## Coverage Analysis

### Current Coverage Status
The project maintains **44.30%** overall code coverage with:
- **Unit tests**: Focus on functional API and mocked operations
- **Integration tests**: Real MongoDB operations and DataFrame conversions
- **Combined coverage**: Unit + integration tests together

### Coverage Breakdown by Module
- `autoframe/mongodb.py`: **100%** - Full MongoDB interface coverage
- `autoframe/sources/simple.py`: **94%** - MongoDB operations well tested
- `autoframe/utils/functional.py`: **88%** - Functional utilities covered
- `autoframe/types.py`: **94%** - Type definitions covered
- Lower coverage areas: `config.py` (45%), `logging.py` (21%), `retry.py` (22%)

### Viewing Coverage Reports

**Terminal Report:**
```bash
pixi run test-coverage
```

**HTML Report** (detailed, interactive):
```bash
pixi run test-coverage-html
open htmlcov/index.html  # View in browser
```

**XML Report** (for CI/Codecov):
- Generated automatically during test runs
- Located at `coverage.xml`
- Used by GitHub Actions for Codecov uploads

### Coverage Configuration
Coverage settings in `pyproject.toml`:
- **Source tracking**: Only `autoframe/` package
- **Branch coverage**: Enabled for conditional logic
- **Exclusions**: Test files, generated files, debug code
- **Reports**: Terminal, HTML, and XML formats

### Improving Coverage
To increase coverage in low-coverage modules:

1. **Config module** (`autoframe/config.py` - 45%):
   - Add tests for configuration validation
   - Test error conditions and edge cases
   - Mock file system operations

2. **Logging module** (`autoframe/logging.py` - 21%):
   - Test logging decorators and context managers
   - Verify log message formatting
   - Test different log levels and outputs

3. **Retry module** (`autoframe/utils/retry.py` - 22%):
   - Test retry logic with different failure scenarios
   - Test timeout and backoff behaviors
   - Mock network and database failures

## Troubleshooting

### Common Issues

**Unit tests fail with connection errors:**
- Check if doctests are trying to connect to MongoDB
- Run `pixi run test` (unit tests only) instead of `pixi run test-all`

**Integration tests all skip:**
- Ensure MongoDB is running: `pixi run test-db-status`
- Check MongoDB URI: `echo $MONGODB_URI`
- Verify Docker is running if using Docker setup

**Mock tests fail:**
- Ensure you're using `unittest.mock.MagicMock` for MongoDB client mocks
- Check that all method chains are properly mocked

**Database connection issues:**
- Verify MongoDB is accessible: `mongosh $MONGODB_URI`
- Check firewall/network settings
- Ensure MongoDB is binding to correct interfaces