"""Authentication and credential management for autoframe.

This module provides secure authentication methods for data sources,
particularly MongoDB, following the functional programming patterns
established throughout the codebase.
"""

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from logerr import Err, Ok, Result

from autoframe.types import DataSourceError


@dataclass(frozen=True)
class MongoCredentials:
    """Immutable credentials for MongoDB authentication."""

    username: str
    password: str
    auth_database: str = "admin"
    auth_mechanism: str = "SCRAM-SHA-256"

    def to_connection_params(self) -> dict[str, Any]:
        """Convert to MongoDB connection parameters."""
        return {
            "username": self.username,
            "password": self.password,
            "authSource": self.auth_database,
            "authMechanism": self.auth_mechanism,
        }


@dataclass(frozen=True)
class MongoConnectionConfig:
    """Configuration for MongoDB connections with authentication."""

    host: str
    port: int = 27017
    database: str | None = None
    credentials: MongoCredentials | None = None
    ssl: bool = False
    ssl_cert_path: str | None = None
    connection_options: dict[str, Any] | None = None

    def build_connection_string(self) -> str:
        """Build a complete MongoDB connection string."""
        # Start with basic connection
        if self.credentials:
            # URL-encode credentials to handle special characters
            username = quote_plus(self.credentials.username)
            password = quote_plus(self.credentials.password)
            auth_part = f"{username}:{password}@"
        else:
            auth_part = ""

        # Build base URI
        uri = f"mongodb://{auth_part}{self.host}:{self.port}"

        # Add database if specified
        if self.database:
            uri += f"/{self.database}"

        # Build query parameters
        params = []

        if self.credentials:
            params.extend(
                [
                    f"authSource={self.credentials.auth_database}",
                    f"authMechanism={self.credentials.auth_mechanism}",
                ]
            )

        if self.ssl:
            params.append("ssl=true")
            if self.ssl_cert_path:
                params.append(f"sslCertificateKeyFile={self.ssl_cert_path}")

        # Add custom connection options
        if self.connection_options:
            for key, value in self.connection_options.items():
                params.append(f"{key}={value}")

        # Append parameters if any
        if params:
            uri += "?" + "&".join(params)

        return uri


def create_credentials_from_env(
    username_var: str = "MONGODB_USERNAME",
    password_var: str = "MONGODB_PASSWORD",
    auth_db_var: str = "MONGODB_AUTH_DB",
) -> Result[MongoCredentials, DataSourceError]:
    """Create MongoDB credentials from environment variables.

    Args:
        username_var: Environment variable name for username
        password_var: Environment variable name for password
        auth_db_var: Environment variable name for auth database

    Returns:
        Result[MongoCredentials, DataSourceError]

    Examples:
        >>> # Set environment variables first:
        >>> # export MONGODB_USERNAME=myuser
        >>> # export MONGODB_PASSWORD=mypass
        >>> creds_result = create_credentials_from_env()
        >>> match creds_result:
        ...     case Ok(creds):
        ...         print(f"Loaded credentials for {creds.username}")
        ...     case Err(error):
        ...         print(f"Failed to load credentials: {error}")
    """
    username = os.getenv(username_var)
    password = os.getenv(password_var)

    if not username:
        return Err(DataSourceError(f"Missing environment variable: {username_var}"))

    if not password:
        return Err(DataSourceError(f"Missing environment variable: {password_var}"))

    auth_db = os.getenv(auth_db_var, "admin")

    return Ok(
        MongoCredentials(username=username, password=password, auth_database=auth_db)
    )


def create_config_from_env(
    host_var: str = "MONGODB_HOST",
    port_var: str = "MONGODB_PORT",
    database_var: str = "MONGODB_DATABASE",
) -> Result[MongoConnectionConfig, DataSourceError]:
    """Create MongoDB connection config from environment variables.

    Args:
        host_var: Environment variable name for host
        port_var: Environment variable name for port
        database_var: Environment variable name for database

    Returns:
        Result[MongoConnectionConfig, DataSourceError]

    Examples:
        >>> # Set environment variables:
        >>> # export MONGODB_HOST=localhost
        >>> # export MONGODB_PORT=27017
        >>> # export MONGODB_DATABASE=mydb
        >>> config_result = create_config_from_env()
    """
    host = os.getenv(host_var, "localhost")

    # Parse port with validation
    port_str = os.getenv(port_var, "27017")
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            return Err(DataSourceError(f"Invalid port number: {port}"))
    except ValueError:
        return Err(DataSourceError(f"Invalid port value: {port_str}"))

    database = os.getenv(database_var)

    # Try to load credentials (optional)
    credentials_result = create_credentials_from_env()
    credentials = credentials_result.unwrap_or(None)

    return Ok(
        MongoConnectionConfig(
            host=host, port=port, database=database, credentials=credentials
        )
    )


def create_local_config(
    database: str | None = None, port: int = 27017
) -> MongoConnectionConfig:
    """Create configuration for local MongoDB instance (no authentication).

    Args:
        database: Optional database name
        port: MongoDB port (default 27017)

    Returns:
        MongoConnectionConfig for local instance

    Examples:
        >>> config = create_local_config("testdb")
        >>> connection_string = config.build_connection_string()
    """
    return MongoConnectionConfig(
        host="localhost", port=port, database=database, credentials=None
    )


def create_authenticated_config(
    host: str,
    username: str,
    password: str,
    database: str | None = None,
    port: int = 27017,
    auth_database: str = "admin",
    ssl: bool = False,
) -> MongoConnectionConfig:
    """Create configuration for authenticated MongoDB connection.

    Args:
        host: MongoDB host
        username: Username for authentication
        password: Password for authentication
        database: Optional database name
        port: MongoDB port (default 27017)
        auth_database: Authentication database (default "admin")
        ssl: Enable SSL/TLS (default False)

    Returns:
        MongoConnectionConfig with authentication

    Examples:
        >>> config = create_authenticated_config(
        ...     "remote-mongo.example.com",
        ...     "myuser",
        ...     "mypassword",
        ...     database="myapp",
        ...     ssl=True
        ... )
        >>> connection_string = config.build_connection_string()
    """
    credentials = MongoCredentials(
        username=username, password=password, auth_database=auth_database
    )

    return MongoConnectionConfig(
        host=host, port=port, database=database, credentials=credentials, ssl=ssl
    )


def validate_connection_string(connection_string: str) -> Result[bool, DataSourceError]:
    """Validate a MongoDB connection string format.

    Args:
        connection_string: Connection string to validate

    Returns:
        Result[bool, DataSourceError]: True if valid, error if invalid

    Examples:
        >>> result = validate_connection_string("mongodb://localhost:27017")
        >>> assert result.unwrap() is True
        >>>
        >>> result = validate_connection_string("invalid://string")
        >>> assert result.is_err()
    """
    if not connection_string:
        return Err(DataSourceError("Connection string cannot be empty"))

    if not connection_string.startswith(
        "mongodb://"
    ) and not connection_string.startswith("mongodb+srv://"):
        return Err(
            DataSourceError(
                "Connection string must start with 'mongodb://' or 'mongodb+srv://'"
            )
        )

    # Basic format validation - more comprehensive validation happens in pymongo
    if "://" not in connection_string:
        return Err(DataSourceError("Invalid connection string format"))

    # Security: prevent basic injection attempts
    dangerous_patterns = [
        ";",
        "javascript:",
        "file://",
        "<script",
        "DROP TABLE",
        "DELETE FROM",
    ]
    for pattern in dangerous_patterns:
        if pattern.lower() in connection_string.lower():
            return Err(
                DataSourceError("Invalid characters detected in connection string")
            )

    return Ok(True)
