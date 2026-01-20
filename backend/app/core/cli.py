"""Main CLI application"""

import typer
from pathlib import Path
from typing_extensions import Annotated

from .connection_ops import ConnectionManager
from .backup_ops import BackupManager
from .auth import AuthManager
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
    name: Annotated[str, typer.Option("--name", "-n", help="Connection name")],
    uri: Annotated[str, typer.Option("--uri", "-u", help="MongoDB connection URI")],
    description: Annotated[str, typer.Option("--description", "-d", help="Description")] = "",
):
    """Add a new MongoDB connection"""
    require_auth()
    conn_mgr = ConnectionManager()
    
    if conn_mgr.add_connection(name, uri, description):
        console.print(f"[green]OK[/green] Connection '{name}' added successfully")
    else:
        console.print(f"[red]ERROR[/red] Connection '{name}' already exists")
        raise typer.Exit(1)


@connect_app.command("list")
def connect_list():
    """List all configured connections"""
    require_auth()
    conn_mgr = ConnectionManager()
    connections = conn_mgr.list_connections()
    
    if not connections:
        console.print("[yellow]No connections configured[/yellow]")
        console.print("Tip: Use 'mongodb-manager connect add' to add a connection")
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
    backup_path: Annotated[Path, typer.Option("--backup-path", "-p", help="Backup folder path")] = DEFAULT_BACKUP_PATH,
):
    """Backup a MongoDB connection using mongodump"""
    require_auth()
    conn_mgr = ConnectionManager()
    backup_mgr = BackupManager(backup_path)
    
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
        console.print("Tip: Use 'mongodb-manager connect list' to see available connections")
        raise typer.Exit(1)
    
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
    backup_path: Annotated[Path, typer.Option("--backup-path", "-p", help="Backup folder path")] = DEFAULT_BACKUP_PATH,
):
    """List all backups in _mongodb_manager folder"""
    require_auth()
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
    console.print("Tip: Your next command will prompt for login")


@auth_app.command("status")
def auth_status():
    """Show current session status"""
    session_info = _auth_manager.get_session_info()
    
    if not session_info:
        console.print("[yellow]No active session[/yellow]")
        console.print("Tip: Run any command to login")
        return
    
    if not session_info['is_valid']:
        console.print("[red]Session expired[/red]")
        console.print("Tip: Run any command to login again")
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
