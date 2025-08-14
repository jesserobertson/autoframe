# Continuous Integration

This document describes the CI/CD pipeline setup for the autoframe library.

## Overview

The project uses GitHub Actions for continuous integration with multiple workflows designed for different purposes:

### 🔄 Main CI Workflow (`ci.yml`)
**Triggers**: Push to main/master, Pull Requests, Manual dispatch

**Jobs:**
1. **Test Job** - Runs on Ubuntu and macOS
   - Sets up MongoDB 7.0 as a service
   - Runs unit tests (mocked, fast)
   - Sets up test data and runs integration tests (real MongoDB)
   - Runs all tests including doctests
   
2. **Quality Job** - Code quality checks
   - Type checking with mypy
   - Linting and formatting with ruff
   - Code style validation
   
3. **Docs Job** - Documentation
   - Builds documentation with MkDocs
   - Uploads documentation artifacts

### 🚀 Release Workflow (`release.yml`)
**Triggers**: GitHub releases, Manual dispatch

**Features:**
- Comprehensive testing before release
- Automated PyPI publishing using trusted publishing
- No API keys required (uses OIDC)

### 🔒 Security Workflow (`security.yml`)
**Triggers**: Weekly schedule, Dependency file changes, Manual dispatch

**Features:**
- Security auditing of dependencies
- Automated dependency updates via PR
- Vulnerability scanning

### 🛠️ Development Tools (`dev-tools.yml`)
**Triggers**: Pull requests, Manual dispatch

**Features:**
- Pre-commit hook validation
- Cross-platform testing matrix (Ubuntu, macOS, Windows)
- Coverage reporting to Codecov
- Separate unit and integration test runs

## Integration Tests in CI

### MongoDB Service Setup
GitHub Actions automatically provisions MongoDB 7.0 as a service container:

```yaml
services:
  mongodb:
    image: mongo:7.0
    env:
      MONGO_INITDB_DATABASE: autoframe_test
    ports:
      - 27017:27017
    options: >-
      --health-cmd "mongosh --eval 'db.adminCommand(\"ping\")'"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### Test Data Setup
CI automatically creates test data before running integration tests:

```bash
mongosh autoframe_test --eval "
  db.users.insertMany([
    {_id: 'user1', name: 'Alice', age: 30, active: true, email: 'alice@example.com'},
    {_id: 'user2', name: 'Bob', age: 25, active: true, email: 'bob@example.com'},
    // ... more test data
  ]);
"
```

### Environment Variables
Integration tests use the standard MongoDB connection:
```bash
MONGODB_URI=mongodb://localhost:27017
```

## Test Execution Strategy

### 1. **Unit Tests** (Always Run)
- **Purpose**: Fast feedback, no dependencies
- **Runtime**: ~2-3 seconds
- **Coverage**: Mocked MongoDB operations, functional API
- **Command**: `pixi run test`

### 2. **Integration Tests** (MongoDB Required)
- **Purpose**: End-to-end validation with real database
- **Runtime**: ~10-15 seconds  
- **Coverage**: Real MongoDB operations, DataFrame conversion
- **Command**: `pixi run test-integration`

### 3. **All Tests** (Comprehensive)
- **Purpose**: Complete validation including doctests
- **Runtime**: ~15-20 seconds
- **Coverage**: All tests + embedded doctests
- **Command**: `pixi run test-all`

## Platform Support

| Platform | Unit Tests | Integration Tests | Status |
|----------|------------|-------------------|--------|
| Ubuntu   | ✅ | ✅ | Full support |
| macOS    | ✅ | ✅ | Full support |
| Windows  | ✅ | ⏸️ | Unit tests only* |

*Integration tests on Windows require additional MongoDB service setup.

## Quality Gates

All CI jobs must pass before merging:

### ✅ **Required Checks**
- Unit tests pass on Ubuntu and macOS
- Integration tests pass with MongoDB
- Type checking passes (mypy)
- Code formatting is correct (ruff)
- Documentation builds successfully

### 📊 **Optional Checks**
- Integration tests on macOS (informational)
- Coverage reporting (doesn't block)
- Cross-platform unit tests (informational)

## Local Development

### Running CI Locally
You can run the same checks locally:

```bash
# Unit tests (fast)
pixi run test

# Start local MongoDB for integration tests
pixi run test-db-start

# Integration tests  
pixi run test-integration

# All tests
pixi run test-all

# Quality checks
pixi run typecheck
pixi run quality

# Stop test database
pixi run test-db-stop
```

### Pre-commit Hooks
Install pre-commit hooks to run checks before each commit:

```bash
pixi run install-pre-commit
```

## Coverage Reporting

- **Unit test coverage** is tracked and reported to Codecov
- **Minimum coverage**: No strict minimum (informational)
- **Coverage badge** shows current coverage percentage
- **Pull requests** show coverage changes

## Troubleshooting CI Issues

### Common Issues

**MongoDB Connection Timeouts:**
- CI waits for MongoDB health checks before running tests
- Tests include additional connection retry logic

**Dependency Installation Failures:**
- Pixi caching is enabled to speed up builds
- Dependencies are pinned to avoid version conflicts

**Platform-Specific Test Failures:**
- Tests are designed to be platform-agnostic
- Integration tests skip gracefully if MongoDB unavailable

### Debugging Failed Builds

1. **Check the workflow logs** in GitHub Actions
2. **Run the same commands locally** using pixi
3. **Test with the same Python version** as CI (3.12)
4. **Verify test database setup** if integration tests fail

## Security Considerations

- **No secrets in workflows** - Uses trusted publishing for PyPI
- **Dependency scanning** runs weekly
- **Automated security updates** via pull requests
- **Container security** - Uses official MongoDB Docker image

The CI pipeline is designed to provide fast feedback while ensuring comprehensive testing and high code quality standards.