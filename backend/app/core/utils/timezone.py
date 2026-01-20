"""Timezone utilities for MongoDB Manager

This module provides timezone-aware datetime utilities following DRY principles.
All timestamps in the application use the configured timezone (default: Europe/Paris).
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_timezone() -> ZoneInfo:
    """Get the configured timezone
    
    Returns:
        ZoneInfo: Configured timezone (default: Europe/Paris for France)
    """
    tz_name = os.getenv('TZ', 'Europe/Paris')
    return ZoneInfo(tz_name)


# Single source of truth for timezone
TIMEZONE = get_timezone()


def get_current_time() -> datetime:
    """Get current datetime in configured timezone
    
    Returns:
        datetime: Current time in configured timezone (timezone-aware)
        
    Example:
        >>> now = get_current_time()
        >>> now.tzinfo
        ZoneInfo(key='Europe/Paris')
    """
    return datetime.now(TIMEZONE)


def format_timestamp(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string using configured timezone
    
    Args:
        dt: Datetime object to format (timezone-aware or naive)
        fmt: Format string (default: "%Y-%m-%d %H:%M:%S")
        
    Returns:
        str: Formatted datetime string
        
    Example:
        >>> dt = get_current_time()
        >>> format_timestamp(dt)
        '2026-01-19 22:50:00'
    """
    # Convert naive datetime to timezone-aware if needed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TIMEZONE)
    return dt.strftime(fmt)


def get_backup_timestamp() -> str:
    """Get timestamp for backup folder naming
    
    Returns:
        str: Timestamp in DDMMYYYY_HHMMSS format
        
    Example:
        >>> get_backup_timestamp()
        '19012026_225000'
    """
    return get_current_time().strftime("%d%m%Y_%H%M%S")


def add_hours(dt: datetime, hours: int) -> datetime:
    """Add hours to a datetime
    
    Args:
        dt: Base datetime
        hours: Number of hours to add
        
    Returns:
        datetime: New datetime with hours added
        
    Example:
        >>> now = get_current_time()
        >>> tomorrow = add_hours(now, 24)
    """
    return dt + timedelta(hours=hours)


def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO format datetime string
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        datetime: Parsed datetime object
        
    Example:
        >>> dt = parse_iso_datetime('2026-01-19T22:50:00+01:00')
    """
    return datetime.fromisoformat(iso_string)


def is_expired(expires_at: datetime, current_time: datetime | None = None) -> bool:
    """Check if a datetime has expired
    
    Args:
        expires_at: Expiration datetime
        current_time: Current time to compare against (default: now)
        
    Returns:
        bool: True if expired, False otherwise
        
    Example:
        >>> expires = get_current_time() + timedelta(hours=1)
        >>> is_expired(expires)
        False
    """
    if current_time is None:
        current_time = get_current_time()
    return current_time >= expires_at
