# Authentication and Security

This guide covers secure authentication and credential management for autoframe, particularly for MongoDB connections.

## Overview

Autoframe provides a comprehensive authentication system that supports:

- **Secure credential management** with environment variables
- **Flexible connection configurations** supporting various authentication methods
- **Connection string validation** to prevent injection attacks  
- **URL encoding** for special characters in credentials
- **SSL/TLS support** for encrypted connections

## Quick Start

### Basic Local Connection (No Authentication)

For local development with no authentication:

```python
import autoframe.mongodb as mongodb

# Simple connection string
result = mongodb.to_dataframe(
    "mongodb://localhost:27017",
    "mydb", 
    "mycollection"
)

match result:
    case Ok(df):
        print(f"Loaded {len(df)} rows")
    case Err(error):
        print(f"Error: {error}")
```

### Environment-Based Authentication (Recommended)

Set environment variables for secure credential management:

```bash
export MONGODB_HOST=remote-mongo.example.com
export MONGODB_USERNAME=myuser
export MONGODB_PASSWORD=mypassword
export MONGODB_DATABASE=myapp
export MONGODB_AUTH_DB=admin  # Optional, defaults to "admin"
```

Then use in your code:

```python
from autoframe.auth import create_config_from_env
import autoframe.mongodb as mongodb

# Load configuration from environment
config_result = create_config_from_env()

match config_result:
    case Ok(config):
        # Use the configuration
        df_result = mongodb.to_dataframe(config, "mydb", "mycollection")
        match df_result:
            case Ok(df):
                print(f"Successfully loaded {len(df)} rows")
            case Err(error):
                print(f"Database error: {error}")
    case Err(error):
        print(f"Configuration error: {error}")
```

## Authentication Methods

### 1. Connection Strings

Direct connection strings with embedded credentials:

```python
import autoframe.mongodb as mongodb

# With authentication
connection_string = "mongodb://username:password@host:27017/database?authSource=admin"

result = mongodb.to_dataframe(
    connection_string,
    "database",
    "collection"
)
```

### 2. Configuration Objects

Use configuration objects for more control:

```python
from autoframe.auth import create_authenticated_config
import autoframe.mongodb as mongodb

# Create authenticated configuration
config = create_authenticated_config(
    host="remote-mongo.example.com",
    username="myuser",
    password="mypassword",
    database="myapp",
    port=27017,
    auth_database="admin",  # Database to authenticate against
    ssl=True  # Enable SSL/TLS
)

# Use configuration
result = mongodb.to_dataframe(config, "myapp", "users")
```

### 3. Environment Variables

The most secure approach for production:

```python
from autoframe.auth import create_config_from_env, create_credentials_from_env
import autoframe.mongodb as mongodb

# Load full configuration from environment
config_result = create_config_from_env()

# Or load just credentials
creds_result = create_credentials_from_env()
```

## Configuration Options

### MongoCredentials

```python
from autoframe.auth import MongoCredentials

creds = MongoCredentials(
    username="myuser",
    password="mypassword",
    auth_database="admin",  # Database to authenticate against
    auth_mechanism="SCRAM-SHA-256"  # Authentication mechanism
)
```

### MongoConnectionConfig

```python
from autoframe.auth import MongoConnectionConfig, MongoCredentials

creds = MongoCredentials(username="user", password="pass")

config = MongoConnectionConfig(
    host="localhost",
    port=27017,
    database="mydb",  # Optional default database
    credentials=creds,  # Optional for authenticated connections
    ssl=True,  # Enable SSL/TLS
    ssl_cert_path="/path/to/cert.pem",  # Optional SSL certificate
    connection_options={"maxPoolSize": "50"}  # Additional MongoDB options
)

# Build connection string
connection_string = config.build_connection_string()
```

## Security Best Practices

### 1. Environment Variables

Never hardcode credentials in your source code. Use environment variables:

```bash
# .envrc (for direnv)
export MONGODB_USERNAME=myuser
export MONGODB_PASSWORD=mypassword
export MONGODB_HOST=prod-mongo.example.com
export MONGODB_DATABASE=production
```

### 2. SSL/TLS Encryption

Always use SSL/TLS for production connections:

```python
from autoframe.auth import create_authenticated_config

config = create_authenticated_config(
    host="secure-mongo.example.com",
    username="user",
    password="pass",
    ssl=True,  # Enable SSL/TLS
    ssl_cert_path="/path/to/client-cert.pem"  # Optional client certificate
)
```

### 3. Credential Validation

Autoframe automatically validates connection strings to prevent injection attacks:

```python
from autoframe.auth import validate_connection_string

# Valid connection strings
result = validate_connection_string("mongodb://localhost:27017")
assert result.is_ok()

# Invalid connection strings are rejected
result = validate_connection_string("mongodb://localhost:27017; DROP TABLE users;")
assert result.is_err()
```

### 4. Special Characters

Credentials with special characters are automatically URL-encoded:

```python
from autoframe.auth import create_authenticated_config

# Special characters in password are handled automatically
config = create_authenticated_config(
    host="localhost",
    username="user@domain.com",
    password="p@ss:w0rd!"  # Will be URL-encoded in connection string
)
```

## Error Handling

All authentication operations return `Result` types for safe error handling:

```python
from autoframe.auth import create_credentials_from_env

result = create_credentials_from_env()

match result:
    case Ok(credentials):
        print(f"Loaded credentials for user: {credentials.username}")
    case Err(error):
        print(f"Failed to load credentials: {error}")
        # Handle missing environment variables, etc.
```

Common error scenarios:

- **Missing environment variables**: When required variables like `MONGODB_USERNAME` are not set
- **Invalid connection strings**: When connection strings don't match expected formats
- **Authentication failures**: When credentials are invalid or database is unreachable

## Advanced Usage

### Custom Authentication Mechanisms

```python
from autoframe.auth import MongoCredentials, MongoConnectionConfig

# Use different authentication mechanisms
creds = MongoCredentials(
    username="myuser",
    password="mypassword",
    auth_database="myapp",
    auth_mechanism="MONGODB-X509"  # For certificate-based auth
)
```

### Connection Pooling

```python
from autoframe.auth import MongoConnectionConfig

config = MongoConnectionConfig(
    host="localhost",
    port=27017,
    connection_options={
        "maxPoolSize": "50",
        "minPoolSize": "5",
        "maxIdleTimeMS": "30000",
        "serverSelectionTimeoutMS": "5000"
    }
)
```

### Atlas Cloud Connections

For MongoDB Atlas:

```python
from autoframe.auth import create_authenticated_config

config = create_authenticated_config(
    host="cluster0.mongodb.net",
    username="atlas_user",
    password="atlas_password",
    database="myapp",
    ssl=True
)

# Or use mongodb+srv:// connection string directly
connection_string = "mongodb+srv://user:pass@cluster0.mongodb.net/myapp?retryWrites=true&w=majority"
```

## Pipeline Integration

Authentication configurations work seamlessly with autoframe pipelines:

```python
from autoframe.auth import create_config_from_env
import autoframe as af

# Load config from environment
config_result = create_config_from_env()

match config_result:
    case Ok(config):
        # Use in pipeline
        result = (
            af.pipeline(lambda: af.mongodb.fetch(config, "mydb", "users"))
            .filter(lambda d: d["active"])
            .to_dataframe(backend="pandas")
            .execute()
        )
        
        match result:
            case Ok(df):
                print(f"Pipeline processed {len(df)} active users")
            case Err(error):
                print(f"Pipeline failed: {error}")
    case Err(error):
        print(f"Configuration error: {error}")
```

## Testing with Authentication

For testing with authentication:

```python
import pytest
from autoframe.auth import create_local_config
import autoframe.mongodb as mongodb

def test_with_local_mongo():
    """Test with local MongoDB instance (no auth)."""
    config = create_local_config(database="testdb")
    
    result = mongodb.to_dataframe(config, "testdb", "testcoll", limit=10)
    
    assert result.is_ok()
    df = result.unwrap()
    assert len(df) <= 10

@pytest.mark.integration
def test_with_auth_from_env():
    """Integration test requiring environment credentials."""
    pytest.skip("Requires MONGODB_* environment variables")
    
    from autoframe.auth import create_config_from_env
    
    config_result = create_config_from_env()
    assert config_result.is_ok()
    
    config = config_result.unwrap()
    result = mongodb.to_dataframe(config, "mydb", "mycoll", limit=5)
    
    assert result.is_ok()
```

## Troubleshooting

### Common Issues

1. **"Missing environment variable" errors**
   - Ensure all required environment variables are set
   - Use `direnv` or similar tools for consistent environment management

2. **"Invalid connection string" errors**
   - Check that connection strings start with `mongodb://` or `mongodb+srv://`
   - Verify that special characters in passwords are not causing issues

3. **Authentication failures**
   - Verify credentials are correct
   - Check that the authentication database is correct (usually `admin`)
   - Ensure the user has appropriate permissions

4. **SSL/TLS connection issues**
   - Verify SSL certificates are valid and accessible
   - Check that the MongoDB server supports SSL/TLS

### Debug Mode

Enable debug logging to troubleshoot connection issues:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Authentication operations will now log detailed information
from autoframe.auth import create_config_from_env
config_result = create_config_from_env()
```

Note: Debug logs automatically sanitize sensitive information like passwords to prevent credential leakage.