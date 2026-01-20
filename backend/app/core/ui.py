"""UI components for interactive prompts and display"""

import questionary
from rich.console import Console
from rich.table import Table


console = Console()


def select_connection(connections: list[dict]) -> dict | None:
    """Interactive connection selection
    
    Args:
        connections: List of connection dictionaries
        
    Returns:
        Selected connection dict or None if cancelled
    """
    if not connections:
        console.print("[red]No connections configured[/red]")
        console.print("Tip: Use 'mongodb-manager connect add' to add a connection")
        return None
    
    choices = [
        f"{c['name']} - {c['description'] or c['uri'].split('@')[-1]}"
        for c in connections
    ]
    
    selected = questionary.select(
        "Select MongoDB connection:",
        choices=choices
    ).ask()
    
    if not selected:
        return None
    
    idx = choices.index(selected)
    return connections[idx]


def select_backup(backups: list[dict]) -> dict | None:
    """Interactive backup selection
    
    Args:
        backups: List of backup dictionaries
        
    Returns:
        Selected backup dict or None if cancelled
    """
    if not backups:
        console.print("[red]No backups found[/red]")
        return None
    
    choices = [
        f"{b['name']} - {len(b['databases'])} databases ({b['created_at'][:19] if b['created_at'] else 'Unknown'})"
        for b in backups
    ]
    
    selected = questionary.select(
        "Select backup:",
        choices=choices
    ).ask()
    
    if not selected:
        return None
    
    idx = choices.index(selected)
    return backups[idx]


def display_connections_table(connections: list[dict]):
    """Display connections in a table
    
    Args:
        connections: List of connection dictionaries
    """
    table = Table(title="MongoDB Connections")
    
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URI", style="yellow")
    table.add_column("Description", style="green")
    table.add_column("Added", style="dim")
    
    for conn in connections:
        # Hide password in URI
        uri = conn["uri"]
        if "@" in uri and "://" in uri:
            protocol = uri.split("://")[0]
            rest = uri.split("@")[1]
            uri_display = f"{protocol}://***@{rest}"
        else:
            uri_display = uri
        
        table.add_row(
            conn["name"],
            uri_display,
            conn.get("description", ""),
            conn.get("added_at", "")[:19]
        )
    
    console.print(table)


def display_connection_tests(results: list[dict]):
    """Display connection test results
    
    Args:
        results: List of test result dictionaries
    """
    table = Table(title="Connection Tests")
    
    table.add_column("Connection", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message", style="dim")
    
    for result in results:
        status = "[green]OK[/green]" if result["success"] else "[red]FAILED[/red]"
        table.add_row(
            result["name"],
            status,
            result["message"]
        )
    
    console.print(table)


def display_backups_table(backups: list[dict]):
    """Display backups in a table
    
    Args:
        backups: List of backup dictionaries
    """
    table = Table(title="Available Backups")
    
    table.add_column("Backup Name", style="cyan", no_wrap=True)
    table.add_column("Connection", style="green")
    table.add_column("Databases", style="magenta")
    table.add_column("Created", style="yellow")
    
    for backup in backups:
        table.add_row(
            backup["name"],
            backup["connection_name"],
            str(len(backup["databases"])),
            backup["created_at"][:19] if backup["created_at"] else "Unknown"
        )
    
    console.print(table)


def confirm_action(message: str) -> bool:
    """Confirmation prompt
    
    Args:
        message: Confirmation message to display
        
    Returns:
        True if confirmed, False otherwise
    """
    return questionary.confirm(message, default=False).ask()
