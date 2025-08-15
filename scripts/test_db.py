#!/usr/bin/env python3
"""
Test database management script for MongoDB integration tests.
Python replacement for test-db.sh using typer for CLI interface.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status
from rich.table import Table
from rich.text import Text
from tenacity import (
    retry,
    stop_after_delay,
    wait_fixed,
    retry_if_exception_type,
    RetryError,
)

app = typer.Typer(
    name="test-db",
    help="Test Database Management Script for MongoDB",
    add_completion=False,
)
console = Console()

# Configuration
COMPOSE_FILE = "docker-compose.test.yml"
DB_CONTAINER = "autoframe-test-mongodb"
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: list[str], capture_output: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command with proper error handling."""
    try:
        if capture_output:
            return subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=PROJECT_ROOT)
        else:
            return subprocess.run(cmd, check=check, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Command failed: {' '.join(cmd)}[/red]")
        if capture_output and e.stdout:
            console.print(f"[yellow]STDOUT: {e.stdout}[/yellow]")
        if capture_output and e.stderr:
            console.print(f"[red]STDERR: {e.stderr}[/red]")
        raise typer.Exit(1)


class MongoDBNotReadyError(Exception):
    """MongoDB is not ready to accept connections."""
    pass


@retry(
    stop=stop_after_delay(60),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(MongoDBNotReadyError),
)
def check_mongodb_ready() -> bool:
    """Check if MongoDB is ready to accept connections with retry logic."""
    try:
        result = run_command([
            "docker-compose", "-f", COMPOSE_FILE, "exec", "-T", "mongodb",
            "mongosh", "--eval", "db.adminCommand('ping')"
        ], capture_output=True, check=False)
        
        if result.returncode != 0:
            raise MongoDBNotReadyError("MongoDB ping failed")
        
        return True
    except subprocess.CalledProcessError:
        raise MongoDBNotReadyError("Failed to execute MongoDB ping command")


def is_mongodb_ready() -> bool:
    """Quick check if MongoDB is ready (no retry)."""
    try:
        result = run_command([
            "docker-compose", "-f", COMPOSE_FILE, "exec", "-T", "mongodb",
            "mongosh", "--eval", "db.adminCommand('ping')"
        ], capture_output=True, check=False)
        return result.returncode == 0
    except Exception:
        return False


def wait_for_mongodb() -> bool:
    """Wait for MongoDB to be ready using tenacity retry logic."""
    try:
        with Status("⏳ Waiting for MongoDB to be ready...", console=console, spinner="dots") as status:
            check_mongodb_ready()
            console.print("✅ MongoDB is ready!")
            return True
    except RetryError:
        console.print("[red]❌ MongoDB failed to start within the timeout period[/red]")
        return False


@retry(
    stop=stop_after_delay(30),
    wait=wait_fixed(1),
    retry=retry_if_exception_type((subprocess.CalledProcessError, FileNotFoundError)),
)
def run_init_script() -> None:
    """Run the Python MongoDB initialization script with retry logic."""
    console.print("📊 Initializing test database with sample data...")
    
    init_script = PROJECT_ROOT / "test-data" / "init_mongodb.py"
    if not init_script.exists():
        console.print(f"[red]❌ Init script not found: {init_script}[/red]")
        raise typer.Exit(1)
    
    # Try pixi first, fall back to python
    try:
        run_command(["pixi", "run", "python", str(init_script)])
    except FileNotFoundError:
        # Fall back to direct python if pixi is not available
        run_command(["python", str(init_script)])


@app.command()
def start() -> None:
    """Start MongoDB test container."""
    panel = Panel.fit("🚀 Starting MongoDB Test Environment", style="blue")
    console.print(panel)
    
    with Status("Starting container...", console=console, spinner="bouncingBar"):
        run_command(["docker-compose", "-f", COMPOSE_FILE, "up", "-d"])
    
    if wait_for_mongodb():
        try:
            run_init_script()
            
            success_panel = Panel.fit(
                "✅ MongoDB test environment ready!\n\n"
                "• Container: Started\n"
                "• Database: Initialized\n"
                "• Status: Ready for testing",
                style="green",
                title="Success"
            )
            console.print(success_panel)
        except RetryError:
            console.print("[red]❌ Failed to initialize database after multiple attempts[/red]")
            raise typer.Exit(1)
    else:
        raise typer.Exit(1)


@app.command()
def stop() -> None:
    """Stop MongoDB test container."""
    console.print("🛑 Stopping MongoDB test container...")
    run_command(["docker-compose", "-f", COMPOSE_FILE, "down"])
    console.print("[green]✅ MongoDB test container stopped[/green]")


@app.command()
def restart() -> None:
    """Restart MongoDB test container."""
    console.print("🔄 Restarting MongoDB test container...")
    stop()
    start()


@app.command()
def reset() -> None:
    """Reset database (stop, remove volumes, start fresh)."""
    console.print("🗑️  Resetting MongoDB test database...")
    run_command(["docker-compose", "-f", COMPOSE_FILE, "down", "-v"])
    console.print("🚀 Starting fresh MongoDB container...")
    start()


@app.command()
def init() -> None:
    """Initialize/reinitialize test data (without restarting)."""
    if not is_mongodb_ready():
        console.print("[red]❌ MongoDB is not running. Please start it first with: test-db start[/red]")
        raise typer.Exit(1)
    
    try:
        run_init_script()
        console.print("[green]✅ Database reinitialized successfully![/green]")
    except RetryError:
        console.print("[red]❌ Failed to initialize database after multiple attempts[/red]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """Show container status and database statistics."""
    panel = Panel.fit("📊 MongoDB Test Environment Status", style="cyan")
    console.print(panel)
    
    # Create status table
    status_table = Table(title="Container Status", show_header=True, header_style="bold magenta")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", justify="center")
    status_table.add_column("Details", style="dim")
    
    # Check container status
    try:
        result = run_command(["docker-compose", "-f", COMPOSE_FILE, "ps"], capture_output=True)
        if "autoframe-test-mongodb" in result.stdout and "Up" in result.stdout:
            status_table.add_row("Container", "🟢 Running", "autoframe-test-mongodb")
        else:
            status_table.add_row("Container", "🔴 Stopped", "autoframe-test-mongodb")
    except subprocess.CalledProcessError:
        status_table.add_row("Container", "❌ Error", "Failed to check status")
    
    # Check MongoDB connection and show database stats
    if is_mongodb_ready():
        status_table.add_row("MongoDB", "🟢 Ready", "Accepting connections")
        
        # Database statistics table
        db_table = Table(title="Database Collections", show_header=True, header_style="bold green")
        db_table.add_column("Collection", style="cyan")
        db_table.add_column("Documents", justify="right", style="green")
        
        try:
            result = run_command([
                "docker-compose", "-f", COMPOSE_FILE, "exec", "-T", "mongodb",
                "mongosh", "autoframe_test", "--quiet", "--eval",
                """
                db.getCollectionNames().forEach(function(name) {
                    var count = db[name].countDocuments();
                    print(name + ',' + count);
                });
                """
            ], capture_output=True, check=False)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if ',' in line and line.strip():
                        collection, count = line.strip().split(',')
                        db_table.add_row(collection, count)
            else:
                db_table.add_row("Error", "Could not retrieve statistics")
        except Exception:
            db_table.add_row("Error", "Could not retrieve statistics")
    else:
        status_table.add_row("MongoDB", "🔴 Not Ready", "Not responding to connections")
        db_table = Table(title="Database Collections")
        db_table.add_column("Status")
        db_table.add_row("[red]MongoDB not available[/red]")
    
    console.print(status_table)
    console.print()
    console.print(db_table)


@app.command()
def logs() -> None:
    """Show container logs."""
    console.print("📋 MongoDB container logs:")
    try:
        run_command(["docker-compose", "-f", COMPOSE_FILE, "logs", "-f", "mongodb"])
    except KeyboardInterrupt:
        console.print("\n[yellow]Log streaming stopped[/yellow]")


@app.command()
def shell() -> None:
    """Connect to MongoDB shell."""
    console.print("🔗 Connecting to MongoDB shell...")
    console.print("[yellow]Tip: Use 'use autoframe_test' to switch to the test database[/yellow]")
    
    try:
        run_command(["docker-compose", "-f", COMPOSE_FILE, "exec", "mongodb", "mongosh"])
    except KeyboardInterrupt:
        console.print("\n[yellow]Shell session ended[/yellow]")


@app.command()
def test() -> None:
    """Run integration tests."""
    console.print("🧪 Running integration tests...")
    
    # Check if MongoDB is running
    if not is_mongodb_ready():
        console.print("[red]❌ MongoDB is not running. Starting it now...[/red]")
        start()
    
    # Set environment variable for tests
    env = os.environ.copy()
    env["MONGODB_URI"] = "mongodb://localhost:27017"
    
    console.print(f"Running integration tests with MongoDB at {env['MONGODB_URI']}")
    
    # Try pixi first, fall back to pytest
    try:
        subprocess.run(["pixi", "run", "test-integration"], env=env, check=True, cwd=PROJECT_ROOT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(["pytest", "tests/integration/", "-v"], env=env, check=True, cwd=PROJECT_ROOT)
        except subprocess.CalledProcessError:
            console.print("[red]❌ Integration tests failed[/red]")
            raise typer.Exit(1)


if __name__ == "__main__":
    # Change to project root directory
    os.chdir(PROJECT_ROOT)
    app()