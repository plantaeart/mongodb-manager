"""Centralized tip messages for MongoDB Manager CLI

This module provides a centralized registry of all tip messages displayed
throughout the application. Using enums and a registry pattern ensures:
- Type safety and IDE autocomplete
- Single source of truth for all tips
- Easy maintenance and updates
- Consistent formatting
- No duplication
"""

from enum import Enum
from rich.console import Console


class TipCategory(Enum):
    """Categories for organizing tips"""
    CONNECTION = "connection"
    BACKUP = "backup"
    AUTH = "auth"
    DISCOVERY = "discovery"
    GENERAL = "general"


class TipKey(Enum):
    """Unique keys for all available tips
    
    Each key maps to a specific tip message in TIPS_REGISTRY.
    Use these keys with show_tip() to display tips consistently.
    """
    # Connection tips
    NO_CONNECTIONS_ADD = "no_connections_add"
    CONNECTION_NOT_FOUND_LIST = "connection_not_found_list"
    
    # Backup tips
    NO_BACKUP_FOLDER = "no_backup_folder"
    NO_BACKUPS_FOUND = "no_backups_found"
    
    # Auth tips
    SESSION_EXPIRED_LOGIN = "session_expired_login"
    NO_SESSION_LOGIN = "no_session_login"
    LOGOUT_SUCCESS = "logout_success"
    
    # Discovery tips
    MONGODB_DISCOVERY_NONE_FOUND = "mongodb_discovery_none_found"
    MONGODB_DISCOVERY_USE_CONFIG = "mongodb_discovery_use_config"
    CONNECTION_ADDED_BACKUP_TIP = "connection_added_backup_tip"
    CONFIG_UPDATED_DISCOVER = "config_updated_discover"
    
    # General tips
    USE_HELP = "use_help"


# Tips Registry: Single source of truth for all tip messages
TIPS_REGISTRY: dict[TipKey, str] = {
    # Connection tips - removed "mongodb-manager" prefix for web terminal
    TipKey.NO_CONNECTIONS_ADD: "Use 'connect add' to add a connection",
    TipKey.CONNECTION_NOT_FOUND_LIST: "Use 'connect list' to see available connections",
    
    # Backup tips
    TipKey.NO_BACKUP_FOLDER: "Use 'create-backup-folder' to configure backup folders",
    TipKey.NO_BACKUPS_FOUND: "Use 'backup create' to create your first backup",
    
    # Auth tips
    TipKey.SESSION_EXPIRED_LOGIN: "Run any command to login again",
    TipKey.NO_SESSION_LOGIN: "Run any command to login",
    TipKey.LOGOUT_SUCCESS: "Your next command will prompt for login",
    
    # Discovery tips
    TipKey.MONGODB_DISCOVERY_NONE_FOUND: (
        "No MongoDB instances found. Make sure MongoDB is running and accessible. "
        "Use 'mongodb config-update' to adjust scan settings (port range, networks, timeout)."
    ),
    TipKey.MONGODB_DISCOVERY_USE_CONFIG: (
        "Use 'mongodb config-show' to view scan settings or 'mongodb config-update' to customize."
    ),
    TipKey.CONNECTION_ADDED_BACKUP_TIP: (
        "Use 'backup create' to create your first backup for this connection."
    ),
    TipKey.CONFIG_UPDATED_DISCOVER: (
        "Configuration updated. Use 'mongodb discover' to scan with new settings."
    ),
    
    # General tips
    TipKey.USE_HELP: "Type 'help' to see all available commands",
}


def show_tip(tip_key: TipKey, console: Console | None = None) -> None:
    """Display a tip message with consistent formatting
    
    Args:
        tip_key: The tip to display (from TipKey enum)
        console: Optional Rich console instance (creates new if not provided)
        
    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> show_tip(TipKey.NO_CONNECTIONS_ADD, console)
        Tip: Use 'connect add' to add a connection
    """
    if console is None:
        console = Console()
    
    tip_message = TIPS_REGISTRY.get(tip_key)
    if tip_message:
        console.print(f"Tip: {tip_message}")
    else:
        # Fallback for missing tips (should never happen in production)
        console.print(f"[yellow]Warning: Tip '{tip_key.value}' not found in registry[/yellow]")


def get_tip_message(tip_key: TipKey) -> str:
    """Get the raw tip message without formatting
    
    Useful for testing, composition, or custom formatting.
    
    Args:
        tip_key: The tip to retrieve
        
    Returns:
        The tip message string, or empty string if not found
        
    Example:
        >>> message = get_tip_message(TipKey.NO_CONNECTIONS_ADD)
        >>> print(message)
        Use 'connect add' to add a connection
    """
    return TIPS_REGISTRY.get(tip_key, "")


def list_all_tips(category: TipCategory | None = None) -> dict[TipKey, str]:
    """Get all tips, optionally filtered by category
    
    Useful for documentation, testing, or displaying help.
    
    Args:
        category: Optional category filter
        
    Returns:
        Dictionary of TipKey -> tip message
        
    Example:
        >>> tips = list_all_tips(TipCategory.CONNECTION)
        >>> for key, message in tips.items():
        ...     print(f"{key.value}: {message}")
    """
    if category is None:
        return TIPS_REGISTRY.copy()
    
    # Filter by category (for future use when categories are added to registry)
    # For now, return all tips
    return TIPS_REGISTRY.copy()
