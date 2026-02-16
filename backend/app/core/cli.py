"""Main CLI application"""

import typer
from pathlib import Path
from typing_extensions import Annotated
import os
import questionary
import sys
import warnings
import logging
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
from .ui import (
    select_connection,
    select_backup,
    display_connections_table,
    display_connection_tests,
    display_backups_table,
    confirm_action,
    display_discovery_config_table,
    display_discovered_mongodb_table,
    console
)
from .config import DiscoverySettings
from .network_scanner import NetworkScanner
from ..models.mongodb_instance import MongoDBInstance


app = typer.Typer(
    name="mongodb-manager",
    help="MongoDB backup/restore manager for Docker volumes",
    no_args_is_help=True
)
connect_app = typer.Typer(help="Manage MongoDB connections")
auth_app = typer.Typer(help="Authentication management")
mongodb_app = typer.Typer(help="MongoDB discovery and configuration")
app.add_typer(connect_app, name="connect")
app.add_typer(auth_app, name="auth")
app.add_typer(mongodb_app, name="mongodb")

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
    uri: Annotated[str | None, typer.Option("--uri", "-u", help="MongoDB connection URI")] = None,
    description: Annotated[str, typer.Option("--description", "-d", help="Description")] = "",
):
    """Add a new MongoDB connection
    
    Usage:
        # Via HTTP API with form (frontend handles this)
        connect add --name my-db --uri mongodb://localhost:27017 --description "My DB"
        
        # Via terminal (interactive wizard for non-WebSocket terminals)
        connect add
    """
    require_auth()
    conn_mgr = ConnectionManager()
    
    # Direct mode: if name and uri provided, add immediately
    # This is used when called via HTTP API with form data
    if name and uri:
        if conn_mgr.add_connection(name, uri, description):
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
def connect_test(
    name: Annotated[str | None, typer.Option("--name", "-n", help="Connection name")] = None,
    all_connections: Annotated[bool, typer.Option("--all", help="Test all connections")] = False,
):
    """Test MongoDB connection(s)"""
    require_auth()
    conn_mgr = ConnectionManager()
    
    if all_connections:
        results = conn_mgr.test_all_connections()
        display_connection_tests(results)
    elif name:
        success, message = conn_mgr.test_connection(name)
        if success:
            console.print(f"[green]OK[/green] {message}")
        else:
            console.print(f"[red]ERROR[/red] {message}")
            raise typer.Exit(1)
    else:
        # Interactive selection
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
):
    """Remove a MongoDB connection"""
    require_auth()
    conn_mgr = ConnectionManager()
    
    if name is None:
        # Interactive selection
        connections = conn_mgr.list_connections()
        selected = select_connection(connections)
        if not selected:
            return
        name = selected["name"]
    
    if not confirm_action(f"Remove connection '{name}'?"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    if conn_mgr.remove_connection(name):
        console.print(f"[green]OK[/green] Connection '{name}' removed")
    else:
        console.print(f"[red]ERROR[/red] Connection '{name}' not found")


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
    
    instance = MongoDBInstance(
        host=host,
        port=port,
        detected=False
    )
    
    success, message = instance.test_connection(timeout=3)
    
    username = ""
    password = ""
    
    if not success:
        console.print("[yellow]✗ Authentication required[/yellow]")
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
        success, message = instance.test_connection(username, password, timeout=3)
        
        if not success:
            console.print(f"[red]✗ Connection failed: {message}[/red]")
            
            # Ask if they want to add anyway
            add_anyway = questionary.confirm(
                "Add connection anyway?",
                default=False
            ).ask()
            
            if not add_anyway:
                console.print("[yellow]Connection setup cancelled[/yellow]")
                return
    else:
        console.print(f"[green]✓ {message}[/green]")
    
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
    
    # Build connection URI with credentials
    connection_uri = instance.get_connection_uri(
        username=username,
        password=password,
        auth_source="admin"
    )
    
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
        backup_folder = backup_mgr.create_backup(conn["uri"], connection_name)
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
        backup_mgr.restore_backup(backup_folder, conn["uri"], drop=drop)
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
    console.print("\n[cyan]Add New Backup Folder[/cyan]")
    
    path = questionary.text(
        "Enter backup folder path:",
        validate=lambda text: True if text.strip() else "Path cannot be empty"
    ).ask()
    
    if not path:
        return
    
    path = path.strip()
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


# --- MongoDB Discovery Configuration Commands ---

@mongodb_app.command("config")
def mongodb_config(
    ctx: typer.Context,
):
    """Manage MongoDB discovery configuration (interactive menu)"""
    require_auth()
    
    # Show interactive menu
    choice = questionary.select(
        "MongoDB Discovery Configuration:",
        choices=[
            "Show current configuration",
            "Update configuration",
            "Cancel"
        ]
    ).ask()
    
    if not choice or choice == "Cancel":
        return
    
    if choice == "Show current configuration":
        mongodb_config_show()
    elif choice == "Update configuration":
        mongodb_config_update()


@mongodb_app.command("config-show")
def mongodb_config_show():
    """Display current discovery configuration"""
    require_auth()
    
    settings = DiscoverySettings.load()
    display_discovery_config_table(settings)
    console.print()


@mongodb_app.command("config-update")
def mongodb_config_update():
    """Update discovery configuration interactively"""
    require_auth()
    
    settings = DiscoverySettings.load()
    
    console.print("[bold cyan]MongoDB Discovery Configuration[/bold cyan]")
    console.print()
    
    while True:
        # Show current settings
        display_discovery_config_table(settings)
        console.print()
        
        # Show menu
        choice = questionary.select(
            "What would you like to update?",
            choices=[
                "Update port range",
                "Update scan timeout",
                "Update max concurrent scans",
                "Toggle Docker network scanning",
                "Manage Docker network ranges",
                "Manage custom IP ranges",
                "Reset to defaults",
                "Save and exit"
            ]
        ).ask()
        
        if not choice or choice == "Save and exit":
            settings.save()
            console.print("[green]Configuration saved successfully[/green]")
            break
        
        try:
            if choice == "Update port range":
                _update_port_range_interactive(settings)
            elif choice == "Update scan timeout":
                _update_timeout_interactive(settings)
            elif choice == "Update max concurrent scans":
                _update_max_concurrent_interactive(settings)
            elif choice == "Toggle Docker network scanning":
                _toggle_docker_scan_interactive(settings)
            elif choice == "Manage Docker network ranges":
                _manage_docker_ranges_interactive(settings)
            elif choice == "Manage custom IP ranges":
                _manage_custom_ranges_interactive(settings)
            elif choice == "Reset to defaults":
                if _confirm_reset_config():
                    settings = settings.reset_to_defaults()
                    console.print("[green]Configuration reset to defaults[/green]")
        except ValueError as e:
            console.print(f"[red]ERROR[/red] {e}")
        
        console.print()


def _update_port_range_interactive(settings: DiscoverySettings) -> None:
    """Interactive prompt to update port range"""
    current = settings.scan_settings.port_range
    
    console.print(f"Current port range: {current['start']} - {current['end']}")
    
    start = questionary.text(
        "Enter start port:",
        default=str(current['start']),
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 65535
    ).ask()
    
    if not start:
        return
    
    end = questionary.text(
        "Enter end port:",
        default=str(current['end']),
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 65535
    ).ask()
    
    if not end:
        return
    
    settings.update_port_range(int(start), int(end))
    console.print(f"[green]Port range updated to {start}-{end}[/green]")


def _update_timeout_interactive(settings: DiscoverySettings) -> None:
    """Interactive prompt to update timeout"""
    current = settings.scan_settings.timeout_seconds
    
    console.print(f"Current timeout: {current} seconds")
    
    timeout = questionary.text(
        "Enter timeout in seconds (1-30):",
        default=str(current),
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 30
    ).ask()
    
    if not timeout:
        return
    
    settings.update_timeout(int(timeout))
    console.print(f"[green]Timeout updated to {timeout} seconds[/green]")


def _update_max_concurrent_interactive(settings: DiscoverySettings) -> None:
    """Interactive prompt to update max concurrent scans"""
    current = settings.scan_settings.max_concurrent_scans
    
    console.print(f"Current max concurrent scans: {current}")
    
    max_concurrent = questionary.text(
        "Enter max concurrent scans (1-50):",
        default=str(current),
        validate=lambda x: x.isdigit() and 1 <= int(x) <= 50
    ).ask()
    
    if not max_concurrent:
        return
    
    settings.update_max_concurrent(int(max_concurrent))
    console.print(f"[green]Max concurrent scans updated to {max_concurrent}[/green]")


def _toggle_docker_scan_interactive(settings: DiscoverySettings) -> None:
    """Interactive prompt to toggle Docker network scanning"""
    current = settings.scan_settings.scan_docker_networks
    
    enabled = questionary.confirm(
        "Enable Docker network scanning?",
        default=current
    ).ask()
    
    if enabled is None:
        return
    
    settings.toggle_docker_scan(enabled)
    status = "enabled" if enabled else "disabled"
    console.print(f"[green]Docker network scanning {status}[/green]")


def _manage_docker_ranges_interactive(settings: DiscoverySettings) -> None:
    """Interactive menu to add/remove Docker network ranges"""
    while True:
        ranges = settings.scan_settings.docker_network_ranges
        
        console.print("\n[cyan]Current Docker Network Ranges:[/cyan]")
        for i, ip_range in enumerate(ranges, 1):
            console.print(f"  {i}. {ip_range}")
        console.print()
        
        choice = questionary.select(
            "Manage Docker network ranges:",
            choices=[
                "Add new range",
                "Remove existing range",
                "Back"
            ]
        ).ask()
        
        if not choice or choice == "Back":
            break
        
        if choice == "Add new range":
            ip_range = questionary.text(
                "Enter IP range in CIDR notation (e.g., 172.23.0.0/24):"
            ).ask()
            
            if ip_range:
                try:
                    settings.add_docker_range(ip_range)
                    console.print(f"[green]Added range: {ip_range}[/green]")
                except ValueError as e:
                    console.print(f"[red]ERROR[/red] {e}")
        
        elif choice == "Remove existing range":
            if not ranges:
                console.print("[yellow]No ranges to remove[/yellow]")
                continue
            
            selected = questionary.select(
                "Select range to remove:",
                choices=ranges + ["Cancel"]
            ).ask()
            
            if selected and selected != "Cancel":
                try:
                    settings.remove_docker_range(selected)
                    console.print(f"[green]Removed range: {selected}[/green]")
                except ValueError as e:
                    console.print(f"[red]ERROR[/red] {e}")


def _manage_custom_ranges_interactive(settings: DiscoverySettings) -> None:
    """Interactive menu to add/remove custom IP ranges"""
    while True:
        ranges = settings.scan_settings.custom_ip_ranges
        
        console.print("\n[cyan]Current Custom IP Ranges:[/cyan]")
        if ranges:
            for i, ip_range in enumerate(ranges, 1):
                console.print(f"  {i}. {ip_range}")
        else:
            console.print("  None configured")
        console.print()
        
        choice = questionary.select(
            "Manage custom IP ranges:",
            choices=[
                "Add new range",
                "Remove existing range" if ranges else None,
                "Back"
            ]
        ).ask()
        
        if not choice or choice == "Back":
            break
        
        if choice == "Add new range":
            ip_range = questionary.text(
                "Enter IP range in CIDR notation (e.g., 192.168.1.0/24):"
            ).ask()
            
            if ip_range:
                try:
                    settings.add_ip_range(ip_range)
                    console.print(f"[green]Added range: {ip_range}[/green]")
                except ValueError as e:
                    console.print(f"[red]ERROR[/red] {e}")
        
        elif choice == "Remove existing range" and ranges:
            selected = questionary.select(
                "Select range to remove:",
                choices=ranges + ["Cancel"]
            ).ask()
            
            if selected and selected != "Cancel":
                try:
                    settings.remove_ip_range(selected)
                    console.print(f"[green]Removed range: {selected}[/green]")
                except ValueError as e:
                    console.print(f"[red]ERROR[/red] {e}")


def _confirm_reset_config() -> bool:
    """Confirm before resetting to defaults"""
    return questionary.confirm(
        "Are you sure you want to reset all settings to defaults?",
        default=False
    ).ask()


# --- MongoDB Discovery Commands ---

@mongodb_app.command("discover")
def mongodb_discover(
    port_start: Annotated[int | None, typer.Option(help="Override port range start")] = None,
    port_end: Annotated[int | None, typer.Option(help="Override port range end")] = None,
    skip_docker: Annotated[bool, typer.Option(help="Skip Docker network scanning")] = False,
):
    """Discover MongoDB instances on the network"""
    logger.debug("[CLI-DISCOVER] Starting mongodb discover command")
    
    require_auth()
    logger.debug("[CLI-DISCOVER] Auth check passed")
    
    # Load settings and apply overrides
    settings = DiscoverySettings.load()
    logger.debug("[CLI-DISCOVER] Settings loaded")
    
    if port_start or port_end:
        current_range = settings.scan_settings.port_range
        start = port_start or current_range["start"]
        end = port_end or current_range["end"]
        settings.update_port_range(start, end)
        logger.debug(f"[CLI-DISCOVER] Port range updated: {start}-{end}")
    
    if skip_docker:
        settings.toggle_docker_scan(False)
        logger.debug("[CLI-DISCOVER] Docker scan disabled")
    
    # Display scan plan
    logger.debug("[CLI-DISCOVER] Displaying scan plan")
    _display_scan_plan(settings)
    console.print()
    
    # Run scan
    logger.debug("[CLI-DISCOVER] Creating scanner")
    scanner = NetworkScanner(settings)
    logger.debug("[CLI-DISCOVER] Running scan with progress")
    instances = _run_scan_with_progress(scanner)
    logger.debug(f"[CLI-DISCOVER] Scan complete, found {len(instances)} instances")
    
    console.print()
    
    # Display results
    if instances:
        logger.debug("[CLI-DISCOVER] Displaying results table")
        display_discovered_mongodb_table(instances)
        console.print()
        
        # Offer to add connection
        _offer_add_connection(instances)
    else:
        console.print("[yellow]No MongoDB instances found[/yellow]")
        console.print()
        show_tip(TipKey.MONGODB_DISCOVERY_NONE_FOUND, console)
    
    logger.debug("[CLI-DISCOVER] Command completed")


def _display_scan_plan(settings: DiscoverySettings) -> None:
    """Display what will be scanned before starting"""
    from rich.panel import Panel
    
    port_range = settings.scan_settings.port_range
    
    scan_info = []
    scan_info.append(f"[cyan]Port Range:[/cyan] {port_range['start']}-{port_range['end']}")
    scan_info.append(f"[cyan]Timeout:[/cyan] {settings.scan_settings.timeout_seconds}s per probe")
    scan_info.append(f"[cyan]Max Concurrent:[/cyan] {settings.scan_settings.max_concurrent_scans} scans")
    scan_info.append("")
    scan_info.append("[bold]Scan Targets:[/bold]")
    scan_info.append("  • Localhost ports")
    
    if settings.scan_settings.scan_docker_networks:
        docker_count = len(settings.scan_settings.docker_network_ranges)
        scan_info.append(f"  • Docker networks ({docker_count} ranges)")
    
    if settings.scan_settings.custom_ip_ranges:
        custom_count = len(settings.scan_settings.custom_ip_ranges)
        scan_info.append(f"  • Custom IP ranges ({custom_count} ranges)")
    
    panel = Panel(
        "\n".join(scan_info),
        title="[bold cyan]MongoDB Discovery[/bold cyan]",
        border_style="cyan"
    )
    
    console.print(panel)


def _run_scan_with_progress(scanner: NetworkScanner) -> list[MongoDBInstance]:
    """Run scan and show progress with detailed steps"""
    logger.debug("[CLI-SCAN] Starting scan with progress")
    
    instances = []
    settings = scanner.settings
    ip_ranges = settings.get_all_ip_ranges()
    logger.debug(f"[CLI-SCAN] Will scan {len(ip_ranges)} network ranges")
    
    # Scan localhost
    logger.debug("[CLI-SCAN] About to scan localhost")
    console.print("[cyan]Scanning localhost ports...[/cyan]")
    console.file.flush() if hasattr(console, 'file') and console.file else None
    sys.stdout.flush()  # Force immediate output
    localhost_instances = scanner.scan_localhost_ports()
    logger.debug(f"[CLI-SCAN] Localhost scan returned {len(localhost_instances)} instances")
    instances.extend(localhost_instances)
    
    if localhost_instances:
        console.print(f"  [green]✓[/green] Found {len(localhost_instances)} instance(s) on localhost")
        console.file.flush() if hasattr(console, 'file') and console.file else None
        sys.stdout.flush()
    else:
        console.print(f"  [dim]No instances on localhost[/dim]")
        console.file.flush() if hasattr(console, 'file') and console.file else None
        sys.stdout.flush()
    
    # Scan each network range
    for idx, ip_range in enumerate(ip_ranges, 1):
        logger.debug(f"[CLI-SCAN] Scanning range {idx}/{len(ip_ranges)}: {ip_range}")
        console.print(f"[cyan]Scanning network {ip_range}... [{idx}/{len(ip_ranges)}][/cyan]")
        console.file.flush() if hasattr(console, 'file') and console.file else None
        sys.stdout.flush()
        network_instances = scanner.scan_ip_range(ip_range)
        logger.debug(f"[CLI-SCAN] Range {ip_range} returned {len(network_instances)} instances")
        instances.extend(network_instances)
        
        if network_instances:
            console.print(f"  [green]✓[/green] Found {len(network_instances)} instance(s) on {ip_range}")
            console.file.flush() if hasattr(console, 'file') and console.file else None
            sys.stdout.flush()  # Force immediate output
    
    print("[CLI-SCAN] All scans complete, printing completion message", file=sys.stderr, flush=True)
    console.print("[green]✓ Scan complete[/green]")
    console.file.flush() if hasattr(console, 'file') and console.file else None
    sys.stdout.flush()  # Force immediate output
    console.print()
    print(f"[CLI-SCAN] Returning {len(instances)} total instances", file=sys.stderr, flush=True)
    return instances


def _offer_add_connection(instances: list[MongoDBInstance]) -> None:
    """Offer to add connection from discovered instances"""
    add_connection = questionary.confirm(
        "Would you like to add a connection now?",
        default=True
    ).ask()
    
    if not add_connection:
        console.print("[dim]Skipping interactive prompt (not a TTY)[/dim]")
        return
    
    # Let user select instance
    choices = [
        f"{inst.get_display_name()} ({inst.host}:{inst.port})"
        for inst in instances
    ]
    choices.append("Cancel")
    
    selected = questionary.select(
        "Select MongoDB instance:",
        choices=choices
    ).ask()
    
    if not selected or selected == "Cancel":
        return
    
    # Get selected instance
    idx = choices.index(selected)
    instance = instances[idx]
    
    # Add connection flow
    _add_connection_from_instance(instance)


def _add_connection_from_instance(instance: MongoDBInstance) -> None:
    """Interactive flow to add connection from discovered instance"""
    console.print(f"\n[cyan]Adding connection for {instance.get_display_name()}[/cyan]")
    console.print()
    
    # Test connection without auth first
    console.print("[dim]Testing connection without authentication...[/dim]")
    success, message = instance.test_connection(timeout=3)
    
    username = ""
    password = ""
    
    if not success:
        console.print("[yellow]✗ Authentication required[/yellow]")
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
        success, message = instance.test_connection(username, password, timeout=3)
        
        if not success:
            console.print(f"[red]✗ Connection failed: {message}[/red]")
            console.print("[yellow]Unable to add connection with provided credentials[/yellow]")
            return
    
    console.print(f"[green]✓ {message}[/green]")
    console.print()
    
    # Prompt for connection details
    default_name = f"{instance.host}-{instance.port}"
    connection_name = questionary.text(
        "Connection name:",
        default=default_name
    ).ask()
    
    if not connection_name:
        console.print("[yellow]Connection setup cancelled[/yellow]")
        return
    
    description = questionary.text(
        "Description (optional):",
        default=f"Discovered MongoDB at {instance.host}:{instance.port}"
    ).ask()
    
    if description is None:
        description = f"Discovered MongoDB at {instance.host}:{instance.port}"
    
    # Build connection URI with credentials
    connection_uri = instance.get_connection_uri(
        username=username,
        password=password,
        auth_source="admin"
    )
    
    # Add connection
    conn_mgr = ConnectionManager()
    
    if conn_mgr.add_connection(connection_name, connection_uri, description or ""):
        console.print(f"\n[green]✓ Connection '{connection_name}' added successfully[/green]")
        console.print()
        show_tip(TipKey.CONNECTION_ADDED_BACKUP_TIP, console)
    else:
        console.print(f"\n[red]✗ Connection '{connection_name}' already exists[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
