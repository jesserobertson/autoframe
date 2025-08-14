// MongoDB initialization script for integration tests
// This script runs when the MongoDB container starts up

// Switch to the test database
db = db.getSiblingDB('autoframe_test');

// Create test users collection with sample data
db.users.insertMany([
    {
        "_id": "user1",
        "name": "Alice Johnson",
        "age": 30,
        "active": true,
        "email": "alice@example.com",
        "department": "Engineering",
        "salary": 75000,
        "joined_date": new Date("2022-01-15")
    },
    {
        "_id": "user2", 
        "name": "Bob Smith",
        "age": 25,
        "active": true,
        "email": "bob@example.com",
        "department": "Marketing",
        "salary": 55000,
        "joined_date": new Date("2023-03-20")
    },
    {
        "_id": "user3",
        "name": "Charlie Brown",
        "age": 35,
        "active": false,
        "email": "charlie@example.com",
        "department": "Engineering", 
        "salary": 85000,
        "joined_date": new Date("2021-08-10")
    },
    {
        "_id": "user4",
        "name": "Diana Prince",
        "age": 28,
        "active": true,
        "email": "diana@example.com",
        "department": "Sales",
        "salary": 62000,
        "joined_date": new Date("2022-11-05")
    },
    {
        "_id": "user5",
        "name": "Eve Adams",
        "age": 22,
        "active": false,
        "email": "eve@example.com",
        "department": "HR",
        "salary": 45000,
        "joined_date": new Date("2024-01-12")
    }
]);

// Create test orders collection with sample data
db.orders.insertMany([
    {
        "_id": "order1",
        "user_id": "user1",
        "total": 129.99,
        "status": "completed",
        "items": 3,
        "order_date": new Date("2024-07-15"),
        "products": ["laptop_stand", "wireless_mouse", "usb_hub"]
    },
    {
        "_id": "order2",
        "user_id": "user2", 
        "total": 75.25,
        "status": "pending",
        "items": 2,
        "order_date": new Date("2024-07-20"),
        "products": ["notebook", "pen_set"]
    },
    {
        "_id": "order3",
        "user_id": "user1",
        "total": 245.00,
        "status": "completed", 
        "items": 5,
        "order_date": new Date("2024-07-18"),
        "products": ["monitor", "keyboard", "mouse_pad", "cable_organizer", "webcam"]
    },
    {
        "_id": "order4",
        "user_id": "user3",
        "total": 89.50,
        "status": "cancelled",
        "items": 1,
        "order_date": new Date("2024-07-12"),
        "products": ["headphones"]
    },
    {
        "_id": "order5",
        "user_id": "user4",
        "total": 156.75,
        "status": "completed",
        "items": 4,
        "order_date": new Date("2024-07-22"),
        "products": ["desk_lamp", "phone_stand", "charging_cable", "bluetooth_speaker"]
    },
    {
        "_id": "order6",
        "user_id": "user2",
        "total": 42.00,
        "status": "shipped",
        "items": 2,
        "order_date": new Date("2024-07-25"),
        "products": ["coffee_mug", "stress_ball"]
    }
]);

// Create test products collection
db.products.insertMany([
    {
        "_id": "prod1",
        "name": "Laptop Stand",
        "category": "Accessories",
        "price": 39.99,
        "in_stock": true,
        "stock_quantity": 150,
        "supplier": "TechCorp"
    },
    {
        "_id": "prod2",
        "name": "Wireless Mouse",
        "category": "Peripherals",
        "price": 29.99,
        "in_stock": true,
        "stock_quantity": 200,
        "supplier": "MouseCorp"
    },
    {
        "_id": "prod3",
        "name": "Monitor 27inch",
        "category": "Displays",
        "price": 199.99,
        "in_stock": false,
        "stock_quantity": 0,
        "supplier": "DisplayTech"
    },
    {
        "_id": "prod4",
        "name": "Mechanical Keyboard",
        "category": "Peripherals",
        "price": 89.99,
        "in_stock": true,
        "stock_quantity": 75,
        "supplier": "KeyCorp"
    },
    {
        "_id": "prod5",
        "name": "USB Hub",
        "category": "Accessories",
        "price": 24.99,
        "in_stock": true,
        "stock_quantity": 300,
        "supplier": "TechCorp"
    }
]);

// Create test analytics collection with time-series data
db.analytics.insertMany([
    {
        "_id": "analytics1",
        "date": new Date("2024-07-01"),
        "page_views": 1250,
        "unique_visitors": 350,
        "bounce_rate": 0.45,
        "conversion_rate": 0.023
    },
    {
        "_id": "analytics2", 
        "date": new Date("2024-07-02"),
        "page_views": 1180,
        "unique_visitors": 320,
        "bounce_rate": 0.48,
        "conversion_rate": 0.019
    },
    {
        "_id": "analytics3",
        "date": new Date("2024-07-03"),
        "page_views": 1420,
        "unique_visitors": 410,
        "bounce_rate": 0.42,
        "conversion_rate": 0.031
    },
    {
        "_id": "analytics4",
        "date": new Date("2024-07-04"),
        "page_views": 980,
        "unique_visitors": 280,
        "bounce_rate": 0.52,
        "conversion_rate": 0.015
    },
    {
        "_id": "analytics5",
        "date": new Date("2024-07-05"),
        "page_views": 1350,
        "unique_visitors": 385,
        "bounce_rate": 0.46,
        "conversion_rate": 0.027
    }
]);

// Create indexes for better query performance
db.users.createIndex({ "active": 1 });
db.users.createIndex({ "department": 1 });
db.orders.createIndex({ "user_id": 1 });
db.orders.createIndex({ "status": 1 });
db.orders.createIndex({ "order_date": 1 });
db.products.createIndex({ "category": 1 });
db.products.createIndex({ "in_stock": 1 });
db.analytics.createIndex({ "date": 1 });

print("✅ Test database 'autoframe_test' initialized with sample data");
print("📊 Collections created: users, orders, products, analytics");
print("🔍 Indexes created for optimal query performance");
print("🚀 Ready for integration testing!");