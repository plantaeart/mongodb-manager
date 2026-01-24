"""Configuration utilities for MongoDB Manager

This module provides centralized configuration management following SOLID principles.
Follows Single Responsibility Principle - only handles configuration concerns.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file (local development)
load_dotenv()


def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable value
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        str: Environment variable value or default
        
    Example:
        >>> get_env_var('MONGODB_MANAGER_PASSWORD_HASH')
        '$2b$12$...'
    """
    return os.getenv(key, default)


def is_coolify_environment() -> bool:
    """Check if running in Coolify environment
    
    Returns:
        bool: True if running in Coolify, False otherwise
        
    Example:
        >>> is_coolify_environment()
        False
    """
    return os.getenv('COOLIFY', '').lower() in ('true', '1', 'yes')


def get_session_directory() -> Path:
    """Get session directory path
    
    Returns:
        Path: Session directory path (default: ~/.mongodb-manager or /data/.mongodb-manager)
        
    Example:
        >>> get_session_directory()
        PosixPath('/home/user/.mongodb-manager')
    """
    default_dir = str(Path.home() / '.mongodb-manager')
    session_dir_str = get_env_var('MONGODB_MANAGER_SESSION_DIR', default_dir)
    return Path(session_dir_str)


def ensure_directory_exists(directory: Path) -> Path:
    """Ensure directory exists, create if not
    
    Args:
        directory: Directory path to check/create
        
    Returns:
        Path: The directory path
        
    Example:
        >>> ensure_directory_exists(Path('/tmp/test'))
        PosixPath('/tmp/test')
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_internal_db_uri() -> str:
    """Get MongoDB URI for internal app data storage (sessions)
    
    Auto-generates URI from environment components following NUXT_ prefix convention.
    Properly URL-encodes username and password to handle special characters.
    
    Returns:
        str: MongoDB connection URI for internal database
        
    Example:
        >>> get_internal_db_uri()
        'mongodb://mongodb_manager_admin:password@manager-mongodb:27017/manager_app?authSource=admin'
    """
    username = get_env_var('NUXT_MONGODB_USERNAME', 'mongodb_manager_admin')
    password = get_env_var('NUXT_MONGODB_PASSWORD', 'changeme123')
    host = get_env_var('NUXT_MONGODB_HOST', 'manager-mongodb')
    port = get_env_var('NUXT_MONGODB_PORT', '27017')
    database = get_env_var('NUXT_MONGODB_DATABASE', 'manager_app')
    
    # URL-encode username and password to handle special characters
    encoded_username = quote_plus(username)
    encoded_password = quote_plus(password)
    
    return f"mongodb://{encoded_username}:{encoded_password}@{host}:{port}/{database}?authSource=admin"


def get_internal_db_client():
    """Get PyMongo client for internal database
    
    Returns:
        MongoClient: Connected MongoDB client for session storage
        
    Example:
        >>> client = get_internal_db_client()
        >>> client.manager_app.sessions.count_documents({})
        0
    """
    from pymongo import MongoClient
    uri = get_internal_db_uri()
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


class ConfigManager:
    """Configuration manager following Single Responsibility Principle
    
    Centralized configuration access point for the application.
    """
    
    @staticmethod
    def get_session_dir() -> Path:
        """Get session directory path"""
        return get_session_directory()
    
    @staticmethod
    def is_coolify() -> bool:
        """Check if running in Coolify"""
        return is_coolify_environment()
    
    @staticmethod
    def get_timezone() -> str:
        """Get configured timezone"""
        return get_env_var('TZ', 'Europe/Paris')
    
    @staticmethod
    def get_internal_db_uri() -> str:
        """Get internal MongoDB URI"""
        return get_internal_db_uri()
    
    @staticmethod
    def get_internal_db_client():
        """Get internal MongoDB client"""
        return get_internal_db_client()
