#!/usr/bin/env python3
"""
One-shot migration script: Convert connection URIs to component-based storage

This script:
1. Reads all connections from MongoDB
2. Parses URI strings into components (host, port, username, password, etc.)
3. Updates documents with component fields
4. Keeps original URI field for backup (can be removed later)

Run once: python backend/migrate_connections.py
"""

import sys
import os
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs
import re

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.mongodb import get_database
from app.repositories.connection_repository import ConnectionRepository


def parse_mongodb_uri(uri: str) -> dict:
    """
    Parse MongoDB URI into components
    
    Args:
        uri: MongoDB connection URI
        
    Returns:
        Dict with components: host, port, username, password, database, auth_source
        
    Examples:
        mongodb://admin:pass123@localhost:27017?authSource=admin
        -> {host: localhost, port: 27017, username: admin, password: pass123, auth_source: admin}
        
        mongodb://localhost:27017
        -> {host: localhost, port: 27017, username: None, password: None, ...}
    """
    # Parse URI
    parsed = urlparse(uri)
    
    # Extract host and port
    netloc = parsed.netloc
    
    # Check for username:password@host:port pattern
    if '@' in netloc:
        auth_part, host_part = netloc.rsplit('@', 1)
        if ':' in auth_part:
            username, password = auth_part.split(':', 1)
            username = unquote(username) if username else None
            password = unquote(password) if password else None
        else:
            username = unquote(auth_part) if auth_part else None
            password = None
    else:
        username = None
        password = None
        host_part = netloc
    
    # Extract host and port
    if ':' in host_part:
        host, port_str = host_part.rsplit(':', 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 27017  # Default
    else:
        host = host_part
        port = 27017  # Default
    
    # Extract database from path
    database = None
    if parsed.path and len(parsed.path) > 1:
        database = parsed.path.lstrip('/')
    
    # Extract authSource from query string
    auth_source = 'admin'  # Default
    if parsed.query:
        query_params = parse_qs(parsed.query)
        if 'authSource' in query_params:
            auth_source = query_params['authSource'][0]
    
    return {
        'host': host or 'localhost',
        'port': port,
        'username': username,
        'password': password,
        'database': database,
        'auth_source': auth_source
    }


def migrate_connections():
    """Migrate all connections from URI-based to component-based storage"""
    
    print("🔄 MongoDB Connection Migration Script")
    print("=" * 60)
    print()
    
    # Get database
    db = get_database()
    repository = ConnectionRepository(db)
    
    # Get all connections
    connections = repository.list_connections()
    
    if not connections:
        print("✅ No connections found. Nothing to migrate.")
        return
    
    print(f"📊 Found {len(connections)} connection(s) to check")
    print()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for conn in connections:
        name = conn.get('name', 'Unknown')
        
        # Check if already migrated (has component fields)
        if 'host' in conn and 'port' in conn:
            print(f"⏭️  SKIP: '{name}' - Already has component fields")
            skipped_count += 1
            continue
        
        # Check if has URI field to migrate
        if 'uri' not in conn:
            print(f"⚠️  SKIP: '{name}' - No URI field found")
            skipped_count += 1
            continue
        
        uri = conn['uri']
        print(f"🔧 MIGRATING: '{name}'")
        print(f"   URI: {uri[:50]}..." if len(uri) > 50 else f"   URI: {uri}")
        
        try:
            # Parse URI into components
            components = parse_mongodb_uri(uri)
            
            print(f"   ├─ Host: {components['host']}")
            print(f"   ├─ Port: {components['port']}")
            print(f"   ├─ Username: {components['username'] or 'None'}")
            print(f"   ├─ Password: {'***' if components['password'] else 'None'}")
            print(f"   ├─ Database: {components['database'] or 'None'}")
            print(f"   └─ Auth Source: {components['auth_source']}")
            
            # Update connection with components
            update_data = {
                'host': components['host'],
                'port': components['port'],
                'username': components['username'],
                'password': components['password'],
                'database': components['database'],
                'auth_source': components['auth_source'],
                # Keep original URI for backup (can remove later if needed)
                'uri_backup': uri
            }
            
            # Update in database
            result = repository.update_connection(name, update_data)
            
            if result:
                print(f"   ✅ SUCCESS")
                migrated_count += 1
            else:
                print(f"   ❌ FAILED: Update returned False")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 60)
    print("📈 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"✅ Migrated: {migrated_count}")
    print(f"⏭️  Skipped:  {skipped_count}")
    print(f"❌ Errors:   {error_count}")
    print()
    
    if migrated_count > 0:
        print("🎉 Migration completed successfully!")
        print()
        print("ℹ️  Note: Original URIs are kept in 'uri_backup' field")
        print("   You can manually remove them later if desired.")
    elif skipped_count > 0 and error_count == 0:
        print("✅ All connections already migrated!")
    else:
        print("⚠️  Migration completed with errors. Check logs above.")


if __name__ == '__main__':
    try:
        migrate_connections()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
