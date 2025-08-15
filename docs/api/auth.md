# Authentication API Reference

This module provides secure authentication and credential management for autoframe data sources.

## Core Classes

### MongoCredentials

Immutable credentials for MongoDB authentication.

```python
@dataclass(frozen=True)
class MongoCredentials:
    username: str
    password: str
    auth_database: str = "admin"
    auth_mechanism: str = "SCRAM-SHA-256"
```

**Methods:**

- `to_connection_params() -> dict[str, Any]`: Convert to MongoDB connection parameters

**Example:**
```python
from autoframe.auth import MongoCredentials

creds = MongoCredentials(
    username="myuser",
    password="mypassword",
    auth_database="production"
)

params = creds.to_connection_params()
# Returns: {"username": "myuser", "password": "mypassword", "authSource": "production", "authMechanism": "SCRAM-SHA-256"}
```

### MongoConnectionConfig

Configuration for MongoDB connections with authentication.

```python
@dataclass(frozen=True)
class MongoConnectionConfig:
    host: str
    port: int = 27017
    database: str | None = None
    credentials: MongoCredentials | None = None
    ssl: bool = False
    ssl_cert_path: str | None = None
    connection_options: dict[str, Any] | None = None
```

**Methods:**

- `build_connection_string() -> str`: Build a complete MongoDB connection string

**Example:**
```python
from autoframe.auth import MongoConnectionConfig, MongoCredentials

creds = MongoCredentials(username="user", password="pass")
config = MongoConnectionConfig(
    host="remote.example.com",
    port=27017,
    database="myapp",
    credentials=creds,
    ssl=True
)

connection_string = config.build_connection_string()
# Returns: "mongodb://user:pass@remote.example.com:27017/myapp?authSource=admin&authMechanism=SCRAM-SHA-256&ssl=true"
```

## Factory Functions

### create_credentials_from_env

Create MongoDB credentials from environment variables.

```python
def create_credentials_from_env(
    username_var: str = "MONGODB_USERNAME",
    password_var: str = "MONGODB_PASSWORD", 
    auth_db_var: str = "MONGODB_AUTH_DB"
) -> Result[MongoCredentials, DataSourceError]
```

**Parameters:**
- `username_var`: Environment variable name for username (default: "MONGODB_USERNAME")
- `password_var`: Environment variable name for password (default: "MONGODB_PASSWORD")
- `auth_db_var`: Environment variable name for auth database (default: "MONGODB_AUTH_DB")

**Returns:**
- `Result[MongoCredentials, DataSourceError]`: Success contains credentials, failure contains error

**Example:**
```python
import os
from autoframe.auth import create_credentials_from_env

# Set environment variables
os.environ["MONGODB_USERNAME"] = "myuser"
os.environ["MONGODB_PASSWORD"] = "mypass"

result = create_credentials_from_env()

match result:
    case Ok(creds):
        print(f"Loaded credentials for {creds.username}")
    case Err(error):
        print(f"Failed: {error}")
```

### create_config_from_env

Create MongoDB connection config from environment variables.

```python
def create_config_from_env(
    host_var: str = "MONGODB_HOST",
    port_var: str = "MONGODB_PORT",
    database_var: str = "MONGODB_DATABASE"
) -> Result[MongoConnectionConfig, DataSourceError]
```

**Parameters:**
- `host_var`: Environment variable name for host (default: "MONGODB_HOST")
- `port_var`: Environment variable name for port (default: "MONGODB_PORT")
- `database_var`: Environment variable name for database (default: "MONGODB_DATABASE")

**Returns:**
- `Result[MongoConnectionConfig, DataSourceError]`: Success contains config, failure contains error

**Example:**
```python
import os
from autoframe.auth import create_config_from_env

# Set environment variables
os.environ["MONGODB_HOST"] = "mongo.example.com"
os.environ["MONGODB_PORT"] = "27017"
os.environ["MONGODB_DATABASE"] = "production"
os.environ["MONGODB_USERNAME"] = "api_user"
os.environ["MONGODB_PASSWORD"] = "secure_pass"

result = create_config_from_env()

match result:
    case Ok(config):
        print(f"Config: {config.host}:{config.port}/{config.database}")
    case Err(error):
        print(f"Configuration error: {error}")
```

### create_local_config

Create configuration for local MongoDB instance (no authentication).

```python
def create_local_config(
    database: str | None = None,
    port: int = 27017
) -> MongoConnectionConfig
```

**Parameters:**
- `database`: Optional database name
- `port`: MongoDB port (default: 27017)

**Returns:**
- `MongoConnectionConfig`: Configuration for local instance

**Example:**
```python
from autoframe.auth import create_local_config

# Local development configuration
config = create_local_config(database="dev_db", port=27018)
connection_string = config.build_connection_string()
# Returns: "mongodb://localhost:27018/dev_db"
```

### create_authenticated_config

Create configuration for authenticated MongoDB connection.

```python
def create_authenticated_config(
    host: str,
    username: str,
    password: str,
    database: str | None = None,
    port: int = 27017,
    auth_database: str = "admin",
    ssl: bool = False
) -> MongoConnectionConfig
```

**Parameters:**
- `host`: MongoDB host
- `username`: Username for authentication
- `password`: Password for authentication
- `database`: Optional database name
- `port`: MongoDB port (default: 27017)
- `auth_database`: Authentication database (default: "admin")
- `ssl`: Enable SSL/TLS (default: False)

**Returns:**
- `MongoConnectionConfig`: Configuration with authentication

**Example:**
```python
from autoframe.auth import create_authenticated_config

config = create_authenticated_config(
    host="secure-mongo.example.com",
    username="api_user",
    password="secure_password",
    database="production",
    ssl=True
)

connection_string = config.build_connection_string()
# Returns authenticated connection string with SSL
```

## Validation Functions

### validate_connection_string

Validate a MongoDB connection string format.

```python
def validate_connection_string(connection_string: str) -> Result[bool, DataSourceError]
```

**Parameters:**
- `connection_string`: Connection string to validate

**Returns:**
- `Result[bool, DataSourceError]`: True if valid, error if invalid

**Security Features:**
- Validates MongoDB URI format
- Prevents basic injection attacks
- Checks for dangerous patterns

**Example:**
```python
from autoframe.auth import validate_connection_string

# Valid connection string
result = validate_connection_string("mongodb://localhost:27017")
assert result.unwrap() is True

# Invalid connection string
result = validate_connection_string("invalid://host")
assert result.is_err()

# Potential injection attempt
result = validate_connection_string("mongodb://localhost:27017; DROP TABLE users;")
assert result.is_err()  # Blocked by security validation
```

## Usage Patterns

### Environment-Based Configuration (Recommended)

```python
from autoframe.auth import create_config_from_env
import autoframe.mongodb as mongodb

# Load configuration from environment
config_result = create_config_from_env()

match config_result:
    case Ok(config):
        # Use configuration
        df_result = mongodb.to_dataframe(config, "mydb", "mycoll")
        
        match df_result:
            case Ok(df):
                print(f"Success: {len(df)} rows")
            case Err(error):
                print(f"Database error: {error}")
                
    case Err(error):
        print(f"Configuration error: {error}")
```

### Explicit Configuration

```python
from autoframe.auth import create_authenticated_config
import autoframe.mongodb as mongodb

config = create_authenticated_config(
    host="prod-mongo.example.com",
    username="readonly_user",
    password="secure_password",
    database="analytics",
    ssl=True
)

result = mongodb.to_dataframe(config, "analytics", "events", limit=1000)

match result:
    case Ok(df):
        print(f"Loaded {len(df)} events securely")
    case Err(error):
        print(f"Failed to load events: {error}")
```

### Pipeline Integration

```python
from autoframe.auth import create_config_from_env
import autoframe as af

config_result = create_config_from_env()

match config_result:
    case Ok(config):
        result = (
            af.pipeline(lambda: af.mongodb.fetch(config, "app", "users"))
            .filter(lambda d: d["active"])
            .to_dataframe()
            .execute()
        )
        
        match result:
            case Ok(df):
                print(f"Pipeline success: {len(df)} active users")
            case Err(error):
                print(f"Pipeline failed: {error}")
                
    case Err(error):
        print(f"Configuration failed: {error}")
```

## Error Handling

All authentication functions return `Result` types for safe error handling:

```python
from autoframe.auth import create_credentials_from_env, DataSourceError

result = create_credentials_from_env()

match result:
    case Ok(credentials):
        # Use credentials
        print(f"Authenticated as: {credentials.username}")
        
    case Err(DataSourceError() as error):
        # Handle specific error types
        if "MONGODB_USERNAME" in str(error):
            print("Please set MONGODB_USERNAME environment variable")
        elif "MONGODB_PASSWORD" in str(error):
            print("Please set MONGODB_PASSWORD environment variable")
        else:
            print(f"Authentication error: {error}")
```

## Security Best Practices

1. **Use environment variables** for credentials (never hardcode)
2. **Enable SSL/TLS** for production connections
3. **Validate connection strings** to prevent injection
4. **Use minimal permissions** for database users
5. **Rotate credentials regularly**

See the [Authentication Guide](../authentication.md) for complete security guidance.