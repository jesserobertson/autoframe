#!/usr/bin/env python3
"""
MongoDB initialization script for integration tests.
This script loads test data from YAML files and initializes the test database.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("❌ PyYAML is required but not installed. Please install it with: pip install pyyaml")
    sys.exit(1)

from pymongo import MongoClient


def load_yaml_data(file_path: Path) -> dict[str, Any]:
    """Load data from a YAML file."""
    with open(file_path) as f:
        return yaml.safe_load(f)


def convert_dates(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert ISO date strings to datetime objects."""
    converted = []
    for item in data:
        converted_item = {}
        for key, value in item.items():
            if isinstance(value, str) and value.endswith('Z'):
                try:
                    # Parse ISO format date string
                    converted_item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    # If it's not a valid date, keep as string
                    converted_item[key] = value
            else:
                converted_item[key] = value
        converted.append(converted_item)
    return converted


def create_indexes(db: Any, indexes_config: dict[str, Any]) -> None:
    """Create database indexes."""
    for collection_name, indexes in indexes_config.items():
        collection = db[collection_name]
        for index_spec in indexes:
            collection.create_index(list(index_spec['fields'].items()))
            print(f"  ✓ Created index on {collection_name}: {index_spec['fields']}")


def init_database(connection_string: str = "mongodb://localhost:27017") -> None:
    """Initialize the test database with sample data."""
    print("🚀 Initializing MongoDB test database...")
    
    # Connect to MongoDB
    client = MongoClient(connection_string)
    db = client['autoframe_test']
    
    # Get the directory containing this script
    data_dir = Path(__file__).parent
    
    # Collection files to load
    collections = ['users', 'orders', 'products', 'analytics']
    
    print("📊 Loading test data...")
    for collection_name in collections:
        yaml_file = data_dir / f"{collection_name}.yaml"
        if not yaml_file.exists():
            print(f"⚠️  Warning: {yaml_file} not found, skipping {collection_name}")
            continue
            
        # Load data from YAML
        data_config = load_yaml_data(yaml_file)
        documents = data_config.get(collection_name, [])
        
        if not documents:
            print(f"⚠️  Warning: No data found for {collection_name}")
            continue
        
        # Convert date strings to datetime objects
        documents = convert_dates(documents)
        
        # Clear existing data and insert new data
        collection = db[collection_name]
        collection.drop()  # Clear existing data
        result = collection.insert_many(documents)
        
        print(f"  ✓ Inserted {len(result.inserted_ids)} documents into {collection_name}")
    
    # Create indexes
    print("🔍 Creating database indexes...")
    indexes_file = data_dir / "indexes.yaml"
    if indexes_file.exists():
        indexes_config = load_yaml_data(indexes_file)
        create_indexes(db, indexes_config.get('indexes', {}))
    else:
        print("⚠️  Warning: indexes.yaml not found, skipping index creation")
    
    # Verify setup
    print("\n📈 Database verification:")
    for collection_name in db.list_collection_names():
        count = db[collection_name].count_documents({})
        print(f"  {collection_name}: {count} documents")
    
    print("\n✅ Test database 'autoframe_test' initialized successfully!")
    print("🚀 Ready for integration testing!")
    
    client.close()


if __name__ == "__main__":
    # Allow connection string to be passed as argument
    connection_string = sys.argv[1] if len(sys.argv) > 1 else "mongodb://localhost:27017"
    init_database(connection_string)