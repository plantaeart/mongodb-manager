"""UI components for interactive prompts and display"""

import sys
import questionary
from rich.console import Console
from rich.table import Table

from .utils import show_tip, TipKey


console = Console(
    file=sys.stdout,
    force_terminal=False,
    force_interactive=False,
    no_color=True,
    width=120,
    soft_wrap=False,
    highlight=False
)


def select_connection(connections: list[dict]) -> dict | None:
    """Interactive connection selection
    
    Args:
        connections: List of connection dictionaries
        
    Returns:
        Selected connection dict or None if cancelled
    """
    if not connections:
        console.print("[red]No connections configured[/red]")
        show_tip(TipKey.NO_CONNECTIONS_ADD, console)
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


def display_discovery_config_table(settings) -> None:
    """Display discovery configuration in Rich table
    
    Args:
        settings: DiscoverySettings instance
    """
    from .config import DiscoverySettings  # Import here to avoid circular dependency
    
    table = Table(title="MongoDB Discovery Configuration")
    
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")
    
    # Get display dict
    display_data = settings.to_display_dict()
    
    # Add rows for non-list values
    for key, value in display_data.items():
        if isinstance(value, list):
            # Handle lists specially - show first item with key, rest without
            if value:
                # Show count if more than 3 items
                if len(value) > 3:
                    table.add_row(key, f"{value[0]}")
                    for item in value[1:3]:
                        table.add_row("", str(item))
                    table.add_row("", f"... ({len(value) - 3} more)")
                else:
                    table.add_row(key, str(value[0]))
                    for item in value[1:]:
                        table.add_row("", str(item))
            else:
                table.add_row(key, "None")
        else:
            table.add_row(key, str(value))
    
    console.print(table)


def display_discovered_mongodb_table(instances: list) -> None:
    """Display discovered MongoDB instances in Rich table
    
    Args:
        instances: List of MongoDBInstance objects
    """
    table = Table(title="Discovered MongoDB Instances")
    
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold cyan", min_width=30, no_wrap=True)
    table.add_column("Host", style="cyan", min_width=15)
    table.add_column("Port", style="magenta", width=7)
    table.add_column("Version", style="green", width=10)
    table.add_column("Auth Required", style="yellow", width=13)
    table.add_column("Location", style="dim", width=10)
    
    for idx, instance in enumerate(instances, 1):
        # Use the new get_short_name() method which returns container name or host:port
        name = instance.get_short_name()
        
        table.add_row(
            str(idx),
            name,
            instance.host,
            str(instance.port),
            instance.version or "Unknown",
            "Yes" if instance.requires_auth else "No",
            instance.get_location_type().capitalize()
        )
    
    console.print(table)
    
    # Summary
    if instances:
        console.print(f"\n[green]Found {len(instances)} MongoDB instance(s)[/green]")
    else:
        console.print("\n[yellow]No MongoDB instances found[/yellow]")
