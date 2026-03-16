"""Main CLI application"""

import typer
from pathlib import Path
from typing_extensions import Annotated
import os
import questionary
import sys
import warnings
import logging
import asyncio
import json
from contextlib import redirect_stderr
from io import StringIO

# Configure CLI logger
logger = logging.getLogger("mongodb_manager.cli")

# Suppress asyncio and prompt_toolkit warnings from questionary in WebSocket context
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*coroutine.*')
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*Input is not a terminal.*')

# Suppress prompt_toolkit input warnings
logging.getLogger('prompt_toolkit').setLevel(logging.CRITICAL)

# Patch questionary to work in WebSocket/non-TTY environments
# In WebSocket terminals, interactive prompts don't work, so we gracefully skip them
_original_ask = questionary.Question.ask

def _patched_ask(self, patch_stdout=False, kbi_msg="Cancelled", **kwargs):
    """Patched ask() that gracefully handles WebSocket/non-TTY environments"""
    try:
        # Check if we have a TTY - WebSocket terminals return False
        if not sys.stdin.isatty():
            # WebSocket context - interactive prompts won't work
            return None
        # Normal TTY environment - suppress stderr warnings during execution
        stderr_capture = StringIO()
        with redirect_stderr(stderr_capture):
            return _original_ask(self, patch_stdout=patch_stdout, kbi_msg=kbi_msg, **kwargs)
    except Exception:
        # Any error - return None to skip the prompt
        return None

questionary.Question.ask = _patched_ask

from .connection_ops import ConnectionManager
from .backup_ops import BackupManager
from .auth import AuthManager
from .utils import show_tip, TipKey
from .utils.uri_builder import build_mongodb_uri, build_mongodb_uri_masked
from .ui import (
    select_connection,
    select_backup,
    display_connections_table,
    display_connection_tests,
    display_backups_table,
    confirm_action,
    console
)


app = typer.Typer(
    name="mongodb-manager",
    help="MongoDB backup/restore manager for Docker volumes",
    no_args_is_help=True
)
connect_app = typer.Typer(help="Manage MongoDB connections")
auth_app = typer.Typer(help="Authentication management")
app.add_typer(connect_app, name="connect")
app.add_typer(auth_app, name="auth")

DEFAULT_BACKUP_PATH = Path("/backups_mongodb_manager")

# Global auth manager instance
_auth_manager = AuthManager()


def require_auth():
    """Check authentication and prompt login if needed"""
    # Skip auth in non-TTY environments (WebSocket, pipes, automated scripts)
    # In WebSocket context, authentication is already handled via JWT token verification
    if not sys.stdin.isatty():
        return
    
    if _auth_manager.check_session():
        return  # Session valid
    
    # Session invalid/expired - prompt login
    console.print("[yellow]Authentication required[/yellow]")
    if not _auth_manager.prompt_login():
        console.print("[red]Authentication failed[/red]")
        raise typer.Exit(1)


# --- Connection Commands ---

@connect_app.command("add")
def connect_add(
    ctx: typer.Context,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Connection name")] = None,
    host: Annotated[str | None, typer.Option("--host", "-h", help="MongoDB server hostname")] = None,
    port: Annotated[int, typer.Option("--port", "-p", help="MongoDB server port")] = 27017,
    username: Annotated[str | None, typer.Option("--username", "-u", help="Username for authentication")] = None,
    password: Annotated[str | None, typer.Option("--password", help="Password for authentication")] = None,
    database: Annotated[str | None, typer.Option("--database", "-db", help="Default database")] = None,
    auth_source: Annotated[str, typer.Option("--auth-source", "-a", help="Authentication database")] = "admin",
    description: Annotated[str, typer.Option("--description", "-d", help="Description")] = "",
):
    """Add a new MongoDB connection (component-based)
    
    Usage:
        # Via HTTP API with form (frontend handles this)
        connect add --name my-db --host localhost --port 27017 --username admin --password secret --description "My DB"
        
        # Via terminal (interactive wizard for non-WebSocket terminals)
        connect add
    """
    require_auth()
    conn_mgr = ConnectionManager()
    
    # Direct mode: if name and host provided, add immediately
    # This is used when called via HTTP API with form data
    if name and host:
        if conn_mgr.add_connection(
            name=name,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            auth_source=auth_source,
            description=description
        ):
            console.print(f"[green]✓[/green] Connection '{name}' added successfully")
        else:
            console.print(f"[red]✗[/red] Connection '{name}' already exists")
            raise typer.Exit(1)
        return
    
    # Interactive mode: show wizard (for non-WebSocket terminal use)
    # Note: WebSocket terminal will use HTTP API + forms instead
    _show_add_connection_wizard(conn_mgr)


@connect_app.command("list")
def connect_list():
    """List all configured connections"""
    require_auth()
    conn_mgr = ConnectionManager()
    connections = conn_mgr.list_connections()
    
    if not connections:
        console.print("[yellow]No connections configured[/yellow]")
        show_tip(TipKey.NO_CONNECTIONS_ADD, console)
        return
    
    display_connections_table(connections)
    console.print(f"\n[green]Found {len(connections)} connections[/green]")


@connect_app.command("test")
def _test_connections_direct(conn_mgr, connection_names: list[str], skip_confirm: bool = False, json_output: bool = False):
    """Test multiple connections in direct mode (used by form submission)
    
    Args:
        conn_mgr: ConnectionManager instance
        connection_names: List of connection names to test
        skip_confirm: Skip confirmation prompt
        json_output: Output results as JSON instead of formatted text
    """
    if not connection_names:
        if json_output:
            print(json.dumps({"error": "No connections selected", "results": []}))
        else:
            console.print("[yellow]No connections selected[/yellow]")
        return
    
    if not json_output:
        console.print(f"\n[bold]Testing {len(connection_names)} connection(s)...[/bold]\n")
    
    results = []
    for name in connection_names:
        try:
            success, message = conn_mgr.test_connection(name)
            results.append({
                "name": name,
                "success": success,
                "message": message
            })
            
            if not json_output:
                if success:
                    console.print(f"[green]✓[/green] {name}: {message}")
                else:
                    console.print(f"[red]✗[/red] {name}: {message}")
        except Exception as e:
            results.append({
                "name": name,
                "success": False,
                "message": str(e)
            })
            if not json_output:
                console.print(f"[red]✗[/red] {name}: {str(e)}")
    
    # Output results
    if json_output:
        # Output as JSON for programmatic parsing
        success_count = sum(1 for r in results if r["success"])
        failure_count = len(results) - success_count
        print(json.dumps({
            "results": results,
            "summary": {
                "total": len(results),
                "success": success_count,
                "failure": failure_count
            }
        }))
    else:
        # Summary for human-readable output
        success_count = sum(1 for r in results if r["success"])
        failure_count = len(results) - success_count
        console.print(f"\n[bold]Summary:[/bold] {success_count} successful, {failure_count} failed\n")


@connect_app.command("test")
def connect_test(
    name: Annotated[str | None, typer.Option("--name", "-n", help="Connection name (single)")] = None,
    names: Annotated[str | None, typer.Option("--names", help="Connection names (comma-separated for multiple)")] = None,
    all_connections: Annotated[bool, typer.Option("--all", help="Test all connections")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output results as JSON")] = False,
):
    """Test MongoDB connection(s)
    
    Modes:
        1. Direct (single): connect test --name <connection-name>
        2. Direct (multiple): connect test --names <name1,name2,name3> --yes
        3. Direct (all): connect test --all
        4. Interactive: connect test (shows selection menu - native terminal only)
    
    Use --yes to skip confirmation when testing multiple connections.
    Use --json to get structured JSON output (useful for WebSocket terminal).
    """
    require_auth()
    conn_mgr = ConnectionManager()
    
    if all_connections:
        # Test all connections
        results = conn_mgr.test_all_connections()
        display_connection_tests(results)
    elif names:
        # Direct mode: test multiple specific connections (from form)
        connection_list = [n.strip() for n in names.split(',')]
        _test_connections_direct(conn_mgr, connection_list, skip_confirm=yes, json_output=json_output)
    elif name:
        # Direct mode: test single connection
        success, message = conn_mgr.test_connection(name)
        if success:
            console.print(f"[green]OK[/green] {message}")
        else:
            console.print(f"[red]ERROR[/red] {message}")
            raise typer.Exit(1)
    else:
        # Interactive selection (questionary - native terminal only)
        connections = conn_mgr.list_connections()
        selected = select_connection(connections)
        if not selected:
            return
        
        success, message = conn_mgr.test_connection(selected["name"])
        if success:
            console.print(f"[green]OK[/green] {message}")
        else:
            console.print(f"[red]ERROR[/red] {message}")
            raise typer.Exit(1)


@connect_app.command("remove")
def connect_remove(
    name: Annotated[str | None, typer.Option("--name", "-n", help="Connection name")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
):
    """Remove a MongoDB connection
    
    Modes:
        1. Direct: connect remove --name <connection-name> [--yes]
        2. Interactive: connect remove (shows selection menu)
    
    Use --yes to skip confirmation (useful for scripting/API calls).
    """
    require_auth()
    conn_mgr = ConnectionManager()
    
    # Get all connections first
    connections = conn_mgr.list_connections()
    
    if not connections:
        console.print("[yellow]No connections configured[/yellow]")
        show_tip(TipKey.NO_CONNECTIONS_ADD, console)
        return
    
    # MODE 1: Direct removal with --name option
    if name is not None:
        _remove_connection_direct(conn_mgr, connections, name, skip_confirm=yes)
        return
    
    # MODE 2: Interactive removal wizard
    _show_remove_connection_wizard(conn_mgr, connections)


def _remove_connection_direct(conn_mgr: ConnectionManager, connections: list[dict], name: str, skip_confirm: bool = False) -> None:
    """Direct removal with optional confirmation
    
    Args:
        conn_mgr: ConnectionManager instance
        connections: List of all connections
        name: Name of the connection to remove
        skip_confirm: If True, skip confirmation prompt (for API/scripting)
    """
    # Verify connection exists
    conn = conn_mgr.get_connection(name)
    if not conn:
        console.print(f"[red]✗[/red] Connection '{name}' not found")
        console.print()
        console.print("[yellow]Available connections:[/yellow]")
        display_connections_table(connections)
        return
    
    # Show what will be deleted (unless skipping confirmation)
    if not skip_confirm:
        console.print(f"\n[yellow]Connection to remove:[/yellow]")
        console.print(f"  Name: {conn['name']}")
        masked_uri = build_mongodb_uri_masked(
            host=conn.get('host', 'localhost'),
            port=conn.get('port', 27017),
            username=conn.get('username'),
            database=conn.get('database'),
            auth_source=conn.get('auth_source', 'admin')
        )
        console.print(f"  URI: {masked_uri}")
        console.print(f"  Description: {conn.get('description', 'N/A')}")
        console.print()
    
    # Confirm (unless --yes flag used)
    if not skip_confirm:
        if not confirm_action(f"Remove connection '{name}'? This cannot be undone."):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Remove
    if conn_mgr.remove_connection(name):
        console.print(f"[green]✓[/green] Connection '{name}' removed successfully")
        
        # Show remaining connections count
        remaining = len(connections) - 1
        if remaining > 0:
            console.print(f"[dim]You have {remaining} connection(s) remaining[/dim]")
        else:
            console.print("[dim]No connections remaining[/dim]")
            show_tip(TipKey.NO_CONNECTIONS_ADD, console)
    else:
        console.print(f"[red]✗[/red] Failed to remove connection '{name}'")


def _show_remove_connection_wizard(conn_mgr: ConnectionManager, connections: list[dict]) -> None:
    """Interactive wizard for removing connection(s)
    
    Uses questionary for terminal selection (single connection at a time)
    
    Args:
        conn_mgr: ConnectionManager instance
        connections: List of all connections
    """
    # Terminal mode: Use questionary (single selection only)
    _show_remove_form_terminal(conn_mgr, connections)


def _show_remove_form_terminal(conn_mgr: ConnectionManager, connections: list[dict]) -> None:
    """Show removal form in terminal (single selection with questionary)
    
    Args:
        conn_mgr: ConnectionManager instance
        connections: List of all connections
    """
    console.print("\n[bold red]Remove MongoDB Connection[/bold red]")
    console.print("[yellow]Warning: This action cannot be undone[/yellow]")
    console.print()
    
    # Display connections table first
    display_connections_table(connections)
    console.print()
    
    # Selection menu with formatted choices
    choices = []
    for conn in connections:
        uri_display = build_mongodb_uri_masked(
            host=conn.get('host', 'localhost'),
            port=conn.get('port', 27017),
            username=conn.get('username'),
            database=conn.get('database'),
            auth_source=conn.get('auth_source', 'admin')
        )
        desc = conn.get("description", "")
        if desc:
            choices.append(f"{conn['name']} - {desc}")
        else:
            # Show masked URI if no description
            host_part = uri_display.split("@")[-1].split("/")[0] if "@" in uri_display else uri_display.split("://")[-1].split("/")[0]
            choices.append(f"{conn['name']} - {host_part}")
    
    choices.append("Cancel")
    
    selected = questionary.select(
        "Select connection to remove:",
        choices=choices
    ).ask()
    
    if not selected or selected == "Cancel":
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Find selected connection
    idx = choices.index(selected)
    connection = connections[idx]
    
    # Double confirmation for safety
    console.print()
    console.print("[yellow]You are about to remove:[/yellow]")
    console.print(f"  Name: {connection['name']}")
    masked_uri = build_mongodb_uri_masked(
        host=connection.get('host', 'localhost'),
        port=connection.get('port', 27017),
        username=connection.get('username'),
        database=connection.get('database'),
        auth_source=connection.get('auth_source', 'admin')
    )
    console.print(f"  URI: {masked_uri}")
    console.print(f"  Description: {connection.get('description', 'N/A')}")
    console.print()
    
    if not confirm_action(f"Are you sure you want to remove '{connection['name']}'? This cannot be undone."):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Remove connection
    if conn_mgr.remove_connection(connection['name']):
        console.print(f"\n[green]✓[/green] Connection '{connection['name']}' removed successfully")
        
        # Show remaining connections count
        remaining = len(connections) - 1
        if remaining > 0:
            console.print(f"[dim]You have {remaining} connection(s) remaining[/dim]")
        else:
            console.print("[dim]No connections remaining[/dim]")
            show_tip(TipKey.NO_CONNECTIONS_ADD, console)
    else:
        console.print(f"\n[red]✗[/red] Failed to remove connection '{connection['name']}'")


def _show_add_connection_wizard(conn_mgr: ConnectionManager) -> None:
    """Interactive wizard for adding connection with 3 options"""
    console.print("\n[bold cyan]Add MongoDB Connection[/bold cyan]")
    console.print()
    
    choice = questionary.select(
        "How would you like to add a connection?",
        choices=[
            "Discover from network (recommended)",
            "Enter connection details manually",
            "Quick connect (host:port)",
            "Cancel"
        ]
    ).ask()
    
    if not choice or choice == "Cancel":
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    if choice == "Discover from network (recommended)":
        # Call mongodb discover
        console.print()
        console.print("[cyan]Launching discovery...[/cyan]")
        console.print()
        mongodb_discover()
    elif choice == "Enter connection details manually":
        _add_connection_manual(conn_mgr)
    elif choice == "Quick connect (host:port)":
        _add_connection_quick(conn_mgr)


def _add_connection_manual(conn_mgr: ConnectionManager) -> None:
    """Manual connection entry flow"""
    console.print("\n[cyan]Manual Connection Entry[/cyan]")
    console.print()
    
    # Prompt for connection name
    name = questionary.text(
        "Connection name:",
        validate=lambda x: len(x) > 0 if x else "Name cannot be empty"
    ).ask()
    
    if not name:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Prompt for MongoDB URI
    uri = questionary.text(
        "MongoDB connection URI:",
        default="mongodb://localhost:27017",
        validate=lambda x: (len(x) > 0 and x.startswith("mongodb://")) if x else "Invalid URI format"
    ).ask()
    
    if not uri:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Prompt for description (optional)
    description = questionary.text(
        "Description (optional):"
    ).ask()
    
    # Test connection
    console.print()
    console.print("[dim]Testing connection...[/dim]")
    
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        client.close()
        console.print("[green]✓ Connection test successful[/green]")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        console.print(f"[yellow]⚠ Connection test failed: {e}[/yellow]")
        console.print("[yellow]Connection will be added anyway. Verify credentials and network access.[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠ Could not test connection: {e}[/yellow]")
    
    console.print()
    
    # Add connection
    if conn_mgr.add_connection(name, uri, description or ""):
        console.print(f"[green]✓ Connection '{name}' added successfully[/green]")
        console.print()
        show_tip(TipKey.CONNECTION_ADDED_BACKUP_TIP, console)
    else:
        console.print(f"[red]✗ Connection '{name}' already exists[/red]")


def _add_connection_quick(conn_mgr: ConnectionManager) -> None:
    """Quick connect flow for simple host:port connections"""
    console.print("\n[cyan]Quick Connect[/cyan]")
    console.print()
    
    # Prompt for host
    host = questionary.text(
        "MongoDB host:",
        default="localhost"
    ).ask()
    
    if not host:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Prompt for port
    port_str = questionary.text(
        "MongoDB port:",
        default="27017",
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 65535 if x else "Invalid port number"
    ).ask()
    
    if not port_str:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    port = int(port_str)
    
    # Test connection without auth
    console.print()
    console.print("[dim]Testing connection...[/dim]")
    
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
    from urllib.parse import quote_plus
    
    username = ""
    password = ""
    auth_required = False
    
    # Try connection without auth first
    test_uri = f"mongodb://{host}:{port}/?serverSelectionTimeoutMS=3000"
    try:
        client = MongoClient(test_uri, serverSelectionTimeoutMS=3000)
        client.server_info()
        client.close()
        console.print("[green]✓ Connection successful (no auth required)[/green]")
    except OperationFailure:
        # Authentication required
        auth_required = True
        console.print("[yellow]✗ Authentication required[/yellow]")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        console.print("[yellow]Connection setup cancelled[/yellow]")
        return
    except Exception as e:
        console.print(f"[yellow]⚠ Could not test connection: {e}[/yellow]")
    
    # If auth required, prompt for credentials
    if auth_required:
        console.print()
        
        # Prompt for credentials
        username = questionary.text(
            "MongoDB username:",
            default="admin"
        ).ask()
        
        if not username:
            console.print("[yellow]Connection setup cancelled[/yellow]")
            return
        
        password = questionary.password(
            "MongoDB password:"
        ).ask()
        
        if not password:
            console.print("[yellow]Connection setup cancelled[/yellow]")
            return
        
        # Test with credentials
        console.print("[dim]Testing connection with credentials...[/dim]")
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        auth_uri = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/?authSource=admin&serverSelectionTimeoutMS=3000"
        
        try:
            client = MongoClient(auth_uri, serverSelectionTimeoutMS=3000)
            client.server_info()
            client.close()
            console.print("[green]✓ Connection successful with credentials[/green]")
        except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            
            # Ask if they want to add anyway
            add_anyway = questionary.confirm(
                "Add connection anyway?",
                default=False
            ).ask()
            
            if not add_anyway:
                console.print("[yellow]Connection setup cancelled[/yellow]")
                return
        except Exception as e:
            console.print(f"[yellow]⚠ Could not test connection: {e}[/yellow]")
    
    console.print()
    
    # Prompt for connection name
    default_name = f"{host}-{port}"
    connection_name = questionary.text(
        "Connection name:",
        default=default_name
    ).ask()
    
    if not connection_name:
        console.print("[yellow]Connection setup cancelled[/yellow]")
        return
    
    # Prompt for description (optional)
    description = questionary.text(
        "Description (optional):",
        default=f"Quick connect to {host}:{port}"
    ).ask()
    
    # Build connection URI
    if username and password:
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        connection_uri = f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/?authSource=admin"
    else:
        connection_uri = f"mongodb://{host}:{port}/"
    
    # Add connection
    if conn_mgr.add_connection(connection_name, connection_uri, description or ""):
        console.print(f"\n[green]✓ Connection '{connection_name}' added successfully[/green]")
        console.print()
        show_tip(TipKey.CONNECTION_ADDED_BACKUP_TIP, console)
    else:
        console.print(f"\n[red]✗ Connection '{connection_name}' already exists[/red]")


# --- Backup Commands ---

@app.command()
def init_backup(
    path: Annotated[Path, typer.Option("--path", "-p", help="Backup folder path")] = DEFAULT_BACKUP_PATH
):
    """Initialize backup folder with _mongodb_manager suffix"""
    require_auth()
    if not str(path).endswith("_mongodb_manager"):
        console.print("[red]Error: Backup path must end with '_mongodb_manager'[/red]")
        console.print(f"Example: {path}_mongodb_manager")
        raise typer.Exit(1)
    
    backup_mgr = BackupManager(path)
    created_path = backup_mgr.init_backup_folder()
    console.print(f"[green]OK[/green] Backup folder initialized: {created_path}")


@app.command()
def backup(
    connection: Annotated[str | None, typer.Option("--connection", "-c", help="Connection name")] = None,
    backup_path: Annotated[Path | None, typer.Option("--backup-path", "-p", help="Backup folder path")] = None,
):
    """Backup a MongoDB connection using mongodump"""
    require_auth()
    conn_mgr = ConnectionManager()
    
    # Select connection
    if connection is None:
        connections = conn_mgr.list_connections()
        selected = select_connection(connections)
        if not selected:
            return
        connection_name = selected["name"]
    else:
        connection_name = connection
    
    # Get connection details
    conn = conn_mgr.get_connection(connection_name)
    if not conn:
        console.print(f"[red]Connection '{connection_name}' not found[/red]")
        show_tip(TipKey.CONNECTION_NOT_FOUND_LIST, console)
        raise typer.Exit(1)
    
    # Determine backup path
    if backup_path is None:
        # Check if connection has active backup path
        active_path = conn_mgr.get_active_backup_path(connection_name)
        
        if not active_path:
            # AUTO-PROMPT: No backup folder configured
            console.print(f"[yellow]No backup folder configured for connection '{connection_name}'[/yellow]")
            console.print("Let's set one up now...\n")
            
            # Call interactive backup folder setup
            _add_backup_folder(conn_mgr, connection_name)
            
            # Re-check after interactive flow
            active_path = conn_mgr.get_active_backup_path(connection_name)
            if not active_path:
                console.print("[red]Backup cancelled. No folder configured.[/red]")
                return
        
        backup_path = Path(active_path)
    
    backup_mgr = BackupManager(backup_path)
    
    # Create backup
    console.print(f"[yellow]Backing up '{connection_name}'...[/yellow]")
    
    try:
        # Build URI from connection components
        connection_uri = build_mongodb_uri(
            host=conn.get('host', 'localhost'),
            port=conn.get('port', 27017),
            username=conn.get('username'),
            password=conn.get('password'),
            database=conn.get('database'),
            auth_source=conn.get('auth_source', 'admin')
        )
        backup_folder = backup_mgr.create_backup(connection_uri, connection_name)
        console.print(f"[green]OK[/green] Backup created: {backup_folder.name}")
    except Exception as e:
        console.print(f"[red]ERROR[/red] Backup failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def list_backups(
    backup_path: Annotated[Path | None, typer.Option("--backup-path", "-p", help="Backup folder path")] = None,
    connection: Annotated[str | None, typer.Option("--connection", "-c", help="Filter by connection name")] = None,
):
    """List all backups in backup folder"""
    require_auth()
    conn_mgr = ConnectionManager()
    
    # Determine backup path
    if backup_path is None and connection:
        # Use connection's active backup path
        active_path = conn_mgr.get_active_backup_path(connection)
        if active_path:
            backup_path = Path(active_path)
        else:
            backup_path = DEFAULT_BACKUP_PATH
    elif backup_path is None:
        backup_path = DEFAULT_BACKUP_PATH
    
    backup_mgr = BackupManager(backup_path)
    backups = backup_mgr.list_backups()
    
    if not backups:
        console.print(f"[yellow]No backups found in {backup_path}[/yellow]")
        return
    
    display_backups_table(backups)
    console.print(f"\n[green]Found {len(backups)} backups[/green]")


@app.command()
def restore(
    backup_name: Annotated[str | None, typer.Option("--backup", "-b", help="Backup name")] = None,
    connection: Annotated[str | None, typer.Option("--connection", "-c", help="Connection name")] = None,
    drop: Annotated[bool, typer.Option("--drop", help="Drop existing collections")] = False,
    backup_path: Annotated[Path, typer.Option("--backup-path", "-p", help="Backup folder path")] = DEFAULT_BACKUP_PATH,
):
    """Restore from backup using mongorestore"""
    require_auth()
    conn_mgr = ConnectionManager()
    backup_mgr = BackupManager(backup_path)
    
    # Select backup
    if backup_name is None:
        backups = backup_mgr.list_backups()
        selected_backup = select_backup(backups)
        if not selected_backup:
            return
        backup_folder = selected_backup["path"]
        suggested_connection = selected_backup["connection_name"]
    else:
        backup_folder = backup_path / backup_name
        if not backup_folder.exists():
            console.print(f"[red]Backup '{backup_name}' not found[/red]")
            raise typer.Exit(1)
        suggested_connection = None
    
    # Select connection
    if connection is None:
        connections = conn_mgr.list_connections()
        selected = select_connection(connections)
        if not selected:
            return
        connection_name = selected["name"]
    else:
        connection_name = connection
    
    # Get connection details
    conn = conn_mgr.get_connection(connection_name)
    if not conn:
        console.print(f"[red]Connection '{connection_name}' not found[/red]")
        raise typer.Exit(1)
    
    # Confirm
    drop_msg = " (with --drop)" if drop else ""
    if not confirm_action(f"Restore to '{connection_name}'{drop_msg}? This may overwrite data."):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Restore
    console.print(f"[yellow]Restoring to '{connection_name}'...[/yellow]")
    
    try:
        # Build URI from connection components
        connection_uri = build_mongodb_uri(
            host=conn.get('host', 'localhost'),
            port=conn.get('port', 27017),
            username=conn.get('username'),
            password=conn.get('password'),
            database=conn.get('database'),
            auth_source=conn.get('auth_source', 'admin')
        )
        backup_mgr.restore_backup(backup_folder, connection_uri, drop=drop)
        console.print(f"[green]OK[/green] Restore completed successfully")
    except Exception as e:
        console.print(f"[red]ERROR[/red] Restore failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def clear(
    backup_name: Annotated[str | None, typer.Option("--backup", "-b", help="Backup name")] = None,
    all_backups: Annotated[bool, typer.Option("--all", help="Delete all backups")] = False,
    backup_path: Annotated[Path, typer.Option("--backup-path", "-p", help="Backup folder path")] = DEFAULT_BACKUP_PATH,
):
    """Delete backups from _mongodb_manager folder"""
    require_auth()
    backup_mgr = BackupManager(backup_path)
    
    if all_backups:
        backups = backup_mgr.list_backups()
        if not backups:
            console.print("[yellow]No backups to delete[/yellow]")
            return
            
        if not confirm_action(f"Delete ALL {len(backups)} backups? This cannot be undone."):
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        backup_mgr.delete_all_backups()
        console.print(f"[green]OK[/green] Deleted all {len(backups)} backups")
    
    elif backup_name is None:
        # Interactive selection
        backups = backup_mgr.list_backups()
        selected = select_backup(backups)
        if not selected:
            return
        
        if not confirm_action(f"Delete '{selected['name']}'? This cannot be undone."):
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        backup_mgr.delete_backup(selected["name"])
        console.print(f"[green]OK[/green] Deleted: {selected['name']}")
    
    else:
        # Direct deletion
        if not confirm_action(f"Delete '{backup_name}'? This cannot be undone."):
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        backup_mgr.delete_backup(backup_name)
        console.print(f"[green]OK[/green] Deleted: {backup_name}")


@app.command("create-backup-folder")
def create_backup_folder(
    connection: Annotated[str | None, typer.Option("--connection", "-c", help="Connection name")] = None,
):
    """Interactively manage backup folders for a connection"""
    require_auth()
    conn_mgr = ConnectionManager()
    
    # Select connection
    if connection is None:
        connections = conn_mgr.list_connections()
        if not connections:
            console.print("[yellow]No connections configured[/yellow]")
            show_tip(TipKey.NO_CONNECTIONS_ADD, console)
            return
        selected = select_connection(connections)
        if not selected:
            return
        connection_name = selected["name"]
    else:
        connection_name = connection
    
    # Verify connection exists
    conn = conn_mgr.get_connection(connection_name)
    if not conn:
        console.print(f"[red]Connection '{connection_name}' not found[/red]")
        raise typer.Exit(1)
    
    # Get existing backup paths
    backup_paths = conn_mgr.get_backup_paths(connection_name)
    active_path = conn_mgr.get_active_backup_path(connection_name)
    
    while True:
        console.print(f"\n[cyan]Backup Folders for connection '{connection_name}':[/cyan]")
        
        if not backup_paths:
            console.print("[yellow]No backup folders configured[/yellow]")
        else:
            for i, path in enumerate(backup_paths, 1):
                active_marker = " [green](active)[/green]" if path == active_path else ""
                console.print(f"  {i}. {path}{active_marker}")
        
        # Show menu
        choices = []
        if backup_paths:
            choices.extend([
                "View details",
                "Set active folder",
                "Edit folder path",
                "Delete folder",
            ])
        choices.extend([
            "Add new folder",
            "Exit"
        ])
        
        action = questionary.select(
            "What would you like to do?",
            choices=choices
        ).ask()
        
        if not action or action == "Exit":
            console.print("[cyan]Done[/cyan]")
            break
        
        if action == "Add new folder":
            _add_backup_folder(conn_mgr, connection_name)
        
        elif action == "View details":
            _view_backup_folder_details(backup_paths, active_path)
        
        elif action == "Set active folder":
            _set_active_backup_folder(conn_mgr, connection_name, backup_paths)
        
        elif action == "Edit folder path":
            _edit_backup_folder(conn_mgr, connection_name, backup_paths, active_path)
        
        elif action == "Delete folder":
            _delete_backup_folder(conn_mgr, connection_name, backup_paths)
        
        # Refresh backup paths for next iteration
        backup_paths = conn_mgr.get_backup_paths(connection_name)
        active_path = conn_mgr.get_active_backup_path(connection_name)


def _add_backup_folder(conn_mgr: ConnectionManager, connection_name: str):
    """Add a new backup folder"""
    from app.core.utils.config import BACKUP_BASE_DIR, BACKUP_FOLDER_SUFFIX
    
    console.print("\n[cyan]Add New Backup Folder[/cyan]")
    console.print(f"[dim]All backup folders are automatically created under '{BACKUP_BASE_DIR}/'[/dim]")
    
    path_input = questionary.text(
        "Enter backup folder name (without prefix):",
        validate=lambda text: True if text.strip() else "Name cannot be empty"
    ).ask()
    
    if not path_input:
        return
    
    # Clean the input path
    clean_path = path_input.strip().strip('/')
    
    # Enforce base directory prefix
    if clean_path.startswith(BACKUP_BASE_DIR):
        # Remove the base dir prefix temporarily for processing
        clean_path = clean_path[len(BACKUP_BASE_DIR):].strip('/')
    
    # Construct full path: mongodb-manager-backups/user-input_mongodb_manager
    folder_path_base = f"{BACKUP_BASE_DIR}/{clean_path}"
    
    # Automatically append suffix if not already present
    if not folder_path_base.endswith(BACKUP_FOLDER_SUFFIX):
        path = f"{folder_path_base}{BACKUP_FOLDER_SUFFIX}"
    else:
        path = folder_path_base
    
    console.print(f"[dim]Full path: {path}[/dim]")
    path_obj = Path(path)
    
    # Check if path exists
    if not path_obj.exists():
        create = questionary.confirm(
            f"Path '{path}' does not exist. Create it?",
            default=True
        ).ask()
        
        if create:
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]OK[/green] Created directory: {path}")
            except Exception as e:
                console.print(f"[red]ERROR[/red] Failed to create directory: {str(e)}")
                return
        else:
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Check if writable
    if not os.access(path, os.W_OK):
        console.print(f"[red]ERROR[/red] Path is not writable: {path}")
        return
    
    # Add to connection
    if conn_mgr.add_backup_path(connection_name, path):
        console.print(f"[green]OK[/green] Added backup folder: {path}")
        
        # Set as active if it's the first one
        backup_paths = conn_mgr.get_backup_paths(connection_name)
        if len(backup_paths) == 1:
            conn_mgr.set_active_backup_path(connection_name, path)
            console.print(f"[green]OK[/green] Set as active backup folder")
    else:
        console.print(f"[yellow]Folder already exists in list[/yellow]")


def _view_backup_folder_details(backup_paths: list[str], active_path: str | None):
    """View details of backup folders"""
    console.print("\n[cyan]Backup Folder Details:[/cyan]")
    for i, path in enumerate(backup_paths, 1):
        path_obj = Path(path)
        exists = path_obj.exists()
        writable = os.access(path, os.W_OK) if exists else False
        active_marker = " [green](active)[/green]" if path == active_path else ""
        
        console.print(f"\n{i}. {path}{active_marker}")
        console.print(f"   Exists: {'Yes' if exists else '[red]No[/red]'}")
        console.print(f"   Writable: {'Yes' if writable else '[red]No[/red]'}")
        
        if exists:
            try:
                # Count backup folders in this path
                backup_count = len([d for d in path_obj.iterdir() if d.is_dir()])
                console.print(f"   Backups: {backup_count}")
            except:
                console.print(f"   Backups: [yellow]Unable to read[/yellow]")


def _set_active_backup_folder(conn_mgr: ConnectionManager, connection_name: str, backup_paths: list[str]):
    """Set active backup folder"""
    if not backup_paths:
        console.print("[yellow]No backup folders available[/yellow]")
        return
    
    console.print("\n[cyan]Select Active Backup Folder:[/cyan]")
    selected = questionary.select(
        "Choose folder:",
        choices=backup_paths
    ).ask()
    
    if not selected:
        return
    
    if conn_mgr.set_active_backup_path(connection_name, selected):
        console.print(f"[green]OK[/green] Active backup folder set to: {selected}")
    else:
        console.print(f"[red]ERROR[/red] Failed to set active folder")


def _edit_backup_folder(conn_mgr: ConnectionManager, connection_name: str, backup_paths: list[str], active_path: str | None):
    """Edit a backup folder path"""
    if not backup_paths:
        console.print("[yellow]No backup folders to edit[/yellow]")
        return
    
    console.print("\n[cyan]Edit Backup Folder:[/cyan]")
    old_path = questionary.select(
        "Select folder to edit:",
        choices=backup_paths
    ).ask()
    
    if not old_path:
        return
    
    new_path = questionary.text(
        "Enter new path:",
        default=old_path,
        validate=lambda text: True if text.strip() else "Path cannot be empty"
    ).ask()
    
    if not new_path or new_path == old_path:
        console.print("[yellow]No changes made[/yellow]")
        return
    
    new_path = new_path.strip()
    new_path_obj = Path(new_path)
    
    # Check if new path exists
    if not new_path_obj.exists():
        create = questionary.confirm(
            f"Path '{new_path}' does not exist. Create it?",
            default=True
        ).ask()
        
        if create:
            try:
                new_path_obj.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]OK[/green] Created directory: {new_path}")
            except Exception as e:
                console.print(f"[red]ERROR[/red] Failed to create directory: {str(e)}")
                return
        else:
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Update path
    if conn_mgr.update_backup_path(connection_name, old_path, new_path):
        console.print(f"[green]OK[/green] Updated backup folder path")
    else:
        console.print(f"[red]ERROR[/red] Failed to update path")


def _delete_backup_folder(conn_mgr: ConnectionManager, connection_name: str, backup_paths: list[str]):
    """Delete a backup folder from configuration"""
    if not backup_paths:
        console.print("[yellow]No backup folders to delete[/yellow]")
        return
    
    console.print("\n[cyan]Delete Backup Folder:[/cyan]")
    console.print("[yellow]Note: This only removes the path from configuration, not the actual folder[/yellow]")
    
    path_to_delete = questionary.select(
        "Select folder to remove:",
        choices=backup_paths
    ).ask()
    
    if not path_to_delete:
        return
    
    if not confirm_action(f"Remove '{path_to_delete}' from configuration?"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    if conn_mgr.remove_backup_path(connection_name, path_to_delete):
        console.print(f"[green]OK[/green] Removed backup folder from configuration")
    else:
        console.print(f"[red]ERROR[/red] Failed to remove folder")


# --- Authentication Commands ---

@auth_app.command("change")
def auth_change():
    """Change password manually"""
    new_hash = _auth_manager.prompt_password_change()
    
    if new_hash:
        _auth_manager._show_hash_instructions(new_hash)
        console.print("\n[green]OK[/green] Password change initiated")
        console.print("[yellow]Remember:[/yellow] Update your environment variable and restart to use the new password")
    else:
        console.print("[red]ERROR[/red] Password change failed")
        raise typer.Exit(1)


@auth_app.command("logout")
def auth_logout():
    """Logout and clear session"""
    _auth_manager.logout()
    console.print("[green]OK[/green] Logged out successfully")
    show_tip(TipKey.LOGOUT_SUCCESS, console)


@auth_app.command("status")
def auth_status():
    """Show current session status"""
    session_info = _auth_manager.get_session_info()
    
    if not session_info:
        console.print("[yellow]No active session[/yellow]")
        show_tip(TipKey.NO_SESSION_LOGIN, console)
        return
    
    if not session_info['is_valid']:
        console.print("[red]Session expired[/red]")
        show_tip(TipKey.SESSION_EXPIRED_LOGIN, console)
        return
    
    # Calculate human-readable time remaining
    time_remaining = session_info['time_remaining']
    hours = int(time_remaining.total_seconds() // 3600)
    minutes = int((time_remaining.total_seconds() % 3600) // 60)
    
    console.print(f"[green]Session active[/green]")
    console.print(f"Time remaining: {hours}h {minutes}m")
    console.print(f"Expires at: {session_info['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}")


@auth_app.command("hash")
def auth_hash(
    password: Annotated[str | None, typer.Option("--password", "-p", help="Password to hash")] = None
):
    """Generate bcrypt hash for a password (for manual setup)"""
    import questionary
    
    if password is None:
        password = questionary.password("Enter password to hash:").ask()
        if not password:
            console.print("[red]ERROR[/red] No password provided")
            raise typer.Exit(1)
    
    if len(password) < 8:
        console.print("[red]ERROR[/red] Password must be at least 8 characters")
        raise typer.Exit(1)
    
    hash_value = _auth_manager.hash_password(password)
    
    console.print("\n[green]Password hash generated:[/green]")
    console.print(f"\n{hash_value}\n")
    console.print("[yellow]Set this as your MONGODB_MANAGER_PASSWORD_HASH environment variable[/yellow]")


if __name__ == "__main__":
    app()
