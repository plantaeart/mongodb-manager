"""MongoDB Database Client for Manager Database

This module provides a singleton MongoDB client for the manager database
where connections and other application data are stored.
"""

import os
from typing import Optional
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure


class DatabaseClient:
    """Singleton MongoDB client for manager database"""
    
    _instance: Optional['DatabaseClient'] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database client (only once due to singleton)"""
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish connection to manager database"""
        # Try to get URI from environment
        uri = os.getenv('MANAGER_DB_URI')
        
        # If not set, construct from individual vars
        if not uri:
            host = os.getenv('NUXT_MONGODB_HOST', 'localhost')
            port = os.getenv('NUXT_MONGODB_PORT', '27017')
            database = os.getenv('NUXT_MONGODB_DATABASE', 'mongodb_manager')
            username = os.getenv('NUXT_MONGODB_USERNAME')
            password = os.getenv('NUXT_MONGODB_PASSWORD')
            
            if username and password:
                # URL-encode username and password to handle special characters
                username_encoded = quote_plus(username)
                password_encoded = quote_plus(password)
                uri = f"mongodb://{username_encoded}:{password_encoded}@{host}:{port}/{database}?authSource=admin"
            else:
                uri = f"mongodb://{host}:{port}/{database}"
        
        try:
            self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.admin.command('ping')
            
            # Extract database name from URI or use default
            if '/' in uri:
                db_name = uri.split('/')[-1].split('?')[0]
            else:
                db_name = os.getenv('NUXT_MONGODB_DATABASE', 'mongodb_manager')
            
            self._database = self._client[db_name]
            
        except ConnectionFailure as e:
            raise
        except Exception as e:
            raise
    
    def get_database(self) -> Database:
        """Get the manager database instance
        
        Returns:
            MongoDB Database instance
            
        Raises:
            RuntimeError: If database is not connected
        """
        if self._database is None:
            raise RuntimeError("Database not connected. Call _connect() first.")
        return self._database
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None


# Singleton instance
_db_client = DatabaseClient()


def get_manager_db() -> Database:
    """Get the manager database instance
    
    This is the main function to use throughout the application.
    
    Returns:
        MongoDB Database instance
    """
    return _db_client.get_database()


def init_database():
    """Initialize database and create indexes
    
    This should be called on application startup.
    """
    db = get_manager_db()
    
    # Create unique index on connection name
    db.connections.create_index("name", unique=True)
    
    # Create index on created_by for user filtering
    db.connections.create_index("created_by")
    
    # Create index on added_at for sorting
    db.connections.create_index("added_at")


def close_database():
    """Close database connection
    
    This should be called on application shutdown.
    """
    _db_client.close()
