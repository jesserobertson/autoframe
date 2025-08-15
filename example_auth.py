#!/usr/bin/env python3
"""Example demonstrating autoframe authentication capabilities.

This example shows different ways to authenticate with MongoDB using autoframe's
secure authentication system.
"""

import os
from logerr import Ok, Err

from autoframe.auth import (
    create_local_config,
    create_authenticated_config,
    create_config_from_env,
    validate_connection_string
)
import autoframe.mongodb as mongodb


def example_local_connection():
    """Example: Local MongoDB connection (no authentication)."""
    print("=== Local Connection Example ===")
    
    # Create local configuration
    config = create_local_config(database="testdb")
    print(f"Local config: {config.build_connection_string()}")
    
    # Use with MongoDB functions (would work with a running local MongoDB)
    # result = mongodb.to_dataframe(config, "testdb", "testcoll", limit=10)


def example_explicit_authentication():
    """Example: Explicit authentication configuration."""
    print("\n=== Explicit Authentication Example ===")
    
    # Create authenticated configuration
    config = create_authenticated_config(
        host="mongo.example.com",
        username="readonly_user",
        password="secure_password",
        database="analytics",
        ssl=True
    )
    
    connection_string = config.build_connection_string()
    print(f"Authenticated config: {connection_string[:50]}...")  # Don't print full credentials
    
    # Validate the connection string
    validation_result = validate_connection_string(connection_string)
    match validation_result:
        case Ok(_):
            print("✅ Connection string validated successfully")
        case Err(error):
            print(f"❌ Validation failed: {error}")


def example_environment_configuration():
    """Example: Environment-based configuration."""
    print("\n=== Environment Configuration Example ===")
    
    # Set example environment variables
    os.environ.update({
        "MONGODB_HOST": "secure-mongo.example.com",
        "MONGODB_PORT": "27017",
        "MONGODB_USERNAME": "api_user",
        "MONGODB_PASSWORD": "env_password",
        "MONGODB_DATABASE": "production",
        "MONGODB_AUTH_DB": "admin"
    })
    
    # Load configuration from environment
    config_result = create_config_from_env()
    
    match config_result:
        case Ok(config):
            print(f"✅ Environment config loaded: {config.host}:{config.port}")
            print(f"   Database: {config.database}")
            print(f"   Username: {config.credentials.username if config.credentials else 'None'}")
            print(f"   SSL: {config.ssl}")
            
            # Build connection string
            connection_string = config.build_connection_string()
            print(f"   Connection string: {connection_string[:60]}...")
            
        case Err(error):
            print(f"❌ Environment configuration failed: {error}")


def example_security_validation():
    """Example: Security validation features."""
    print("\n=== Security Validation Example ===")
    
    test_connections = [
        # Valid connections
        ("mongodb://localhost:27017", True),
        ("mongodb+srv://cluster.mongodb.net", True),
        ("mongodb://user:pass@host:27017/db", True),
        
        # Invalid connections (should be rejected)
        ("invalid://host", False),
        ("mongodb://host; DROP TABLE users;", False),
        ("javascript:alert('xss')", False),
        ("", False)
    ]
    
    for conn_str, should_be_valid in test_connections:
        result = validate_connection_string(conn_str)
        
        match result:
            case Ok(_):
                status = "✅ VALID" if should_be_valid else "❌ SHOULD BE INVALID"
                print(f"{status}: {conn_str[:50]}")
            case Err(error):
                status = "❌ INVALID" if not should_be_valid else "✅ SHOULD BE VALID"
                print(f"{status}: {conn_str[:50]} - {error}")


def example_pipeline_integration():
    """Example: Using authentication with pipelines."""
    print("\n=== Pipeline Integration Example ===")
    
    # Create a configuration
    config = create_local_config(database="example")
    
    # This would work with an actual MongoDB connection:
    print("Pipeline example (would execute with real MongoDB):")
    print("""
    import autoframe as af
    
    config = create_local_config(database="mydb")
    
    result = (
        af.pipeline(lambda: af.mongodb.fetch(config, "mydb", "users"))
        .filter(lambda d: d.get("active", True))
        .to_dataframe()
        .execute()
    )
    
    match result:
        case Ok(df):
            print(f"Pipeline success: {len(df)} users")
        case Err(error):
            print(f"Pipeline failed: {error}")
    """)


if __name__ == "__main__":
    print("AutoFrame Authentication Examples")
    print("=" * 50)
    
    example_local_connection()
    example_explicit_authentication()
    example_environment_configuration()
    example_security_validation()
    example_pipeline_integration()
    
    print("\n✨ All examples completed!")
    print("\nFor production use:")
    print("1. Set environment variables for credentials")
    print("2. Use SSL/TLS for remote connections")
    print("3. Never hardcode credentials in source code")
    print("4. Use minimal database permissions")