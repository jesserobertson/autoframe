#!/bin/bash

# Test database management script for MongoDB integration tests

set -e

COMPOSE_FILE="docker-compose.test.yml"
DB_CONTAINER="autoframe-test-mongodb"

show_help() {
    echo "Test Database Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start MongoDB test container"
    echo "  stop      Stop MongoDB test container"
    echo "  restart   Restart MongoDB test container"
    echo "  reset     Reset database (stop, remove, start fresh)"
    echo "  status    Show container status"
    echo "  logs      Show container logs"
    echo "  shell     Connect to MongoDB shell"
    echo "  test      Run integration tests"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start          # Start test database"
    echo "  $0 test           # Run integration tests"
    echo "  $0 reset          # Reset database with fresh data"
}

start_db() {
    echo "🚀 Starting MongoDB test container..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    echo "⏳ Waiting for MongoDB to be ready..."
    timeout=60
    count=0
    
    while [ $count -lt $timeout ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo "✅ MongoDB is ready!"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    
    echo ""
    echo "❌ MongoDB failed to start within ${timeout} seconds"
    return 1
}

stop_db() {
    echo "🛑 Stopping MongoDB test container..."
    docker-compose -f "$COMPOSE_FILE" down
    echo "✅ MongoDB test container stopped"
}

restart_db() {
    echo "🔄 Restarting MongoDB test container..."
    stop_db
    start_db
}

reset_db() {
    echo "🗑️  Resetting MongoDB test database..."
    docker-compose -f "$COMPOSE_FILE" down -v
    echo "🚀 Starting fresh MongoDB container..."
    start_db
}

show_status() {
    echo "📊 MongoDB test container status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    if docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "✅ MongoDB is responding to connections"
        
        # Show database info
        echo ""
        echo "📈 Database statistics:"
        docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh autoframe_test --eval "
            print('Collections:');
            db.getCollectionNames().forEach(function(name) {
                var count = db[name].countDocuments();
                print('  ' + name + ': ' + count + ' documents');
            });
        " 2>/dev/null || echo "Could not retrieve database statistics"
    else
        echo "❌ MongoDB is not responding"
    fi
}

show_logs() {
    echo "📋 MongoDB container logs:"
    docker-compose -f "$COMPOSE_FILE" logs -f mongodb
}

connect_shell() {
    echo "🔗 Connecting to MongoDB shell..."
    echo "Tip: Use 'use autoframe_test' to switch to the test database"
    docker-compose -f "$COMPOSE_FILE" exec mongodb mongosh
}

run_tests() {
    echo "🧪 Running integration tests..."
    
    # Check if MongoDB is running
    if ! docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "❌ MongoDB is not running. Starting it now..."
        start_db
    fi
    
    # Set environment variable for tests
    export MONGODB_URI="mongodb://localhost:27017"
    
    # Run integration tests
    echo "Running integration tests with MongoDB at $MONGODB_URI"
    if command -v pixi &> /dev/null; then
        pixi run test-integration
    else
        pytest tests/integration/ -v
    fi
}

case "${1:-help}" in
    start)
        start_db
        ;;
    stop)
        stop_db
        ;;
    restart)
        restart_db
        ;;
    reset)
        reset_db
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    shell)
        connect_shell
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac