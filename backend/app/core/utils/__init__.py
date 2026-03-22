"""Utility modules for MongoDB Manager"""

from .timezone import (
    get_current_time,
    get_backup_timestamp,
    format_timestamp,
    add_hours,
    parse_iso_datetime,
    is_expired,
    TIMEZONE,
)
from .config import (
    get_env_var,
    is_coolify_environment,
    get_session_directory,
    ensure_directory_exists,
    ConfigManager,
)
from .tips import (
    TipKey,
    TipCategory,
    show_tip,
    get_tip_message,
    list_all_tips,
    TIPS_REGISTRY,
)
from .paths import normalize_backup_folder_path
from .backup_utils import parse_backup_selector, collect_all_backups
from .fs import delete_directory_if_exists

__all__ = [
    # Timezone utilities
    'get_current_time',
    'get_backup_timestamp',
    'format_timestamp',
    'add_hours',
    'parse_iso_datetime',
    'is_expired',
    'TIMEZONE',
    # Config utilities
    'get_env_var',
    'is_coolify_environment',
    'get_session_directory',
    'ensure_directory_exists',
    'ConfigManager',
    # Tip utilities
    'TipKey',
    'TipCategory',
    'show_tip',
    'get_tip_message',
    'list_all_tips',
    'TIPS_REGISTRY',
    # Path utilities
    'normalize_backup_folder_path',
    # Backup utilities
    'parse_backup_selector',
    'collect_all_backups',
    # Filesystem utilities
    'delete_directory_if_exists',
]
