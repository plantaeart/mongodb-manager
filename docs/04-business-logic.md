# 04 - Business Logic (MongoDB Operations)

## Overview

Core MongoDB management operations: connection management, backup/restore, database operations.

## Command Categories

### 1. Connection Management

**File**: `backend/app/core/connection_ops.py`

#### `connect list`
Lists all saved MongoDB connections.

```python
def list_connections() -> List[Connection]:
    connections = connections_collection.find()
    return [Connection(**conn) for conn in connections]
```

#### `connect add`
Adds a new MongoDB connection (interactive).

**Flow**:
1. Prompt for connection details (name, URI, description)
2. Validate MongoDB URI format
3. Test connection
4. Save to MongoDB if successful

#### `connect remove <name>`
Removes a saved connection by name.

#### `connect test <name>`
Tests if a connection is valid.

```python
def test_connection(name: str) -> bool:
    connection = get_connection_by_name(name)
    client = MongoClient(connection.uri, serverSelectionTimeoutMS=5000)
    client.server_info()  # Raises exception if can't connect
    return True
```

### 2. Backup Operations

**File**: `backend/app/core/backup_ops.py`

#### `backup create <connection_name>`
Creates a backup using mongodump.

**Flow**:
1. Get connection URI from saved connections
2. Generate backup filename: `{connection_name}_{timestamp}.gz`
3. Execute mongodump command:
   ```bash
   mongodump --uri="<uri>" --archive=<backup_file> --gzip
   ```
4. Save to backup directory
5. Return backup file path

#### `backup list`
Lists all available backup files.

```python
def list_backups() -> List[BackupInfo]:
    backup_dir = Path(BACKUP_DIR)
    backups = []
    for file in backup_dir.glob("*.gz"):
        backups.append(BackupInfo(
            filename=file.name,
            size=file.stat().st_size,
            created=file.stat().st_mtime
        ))
    return backups
```

#### `backup restore <filename>`
Restores a backup using mongorestore.

**Flow**:
1. Verify backup file exists
2. Prompt for target connection
3. Execute mongorestore command:
   ```bash
   mongorestore --uri="<uri>" --archive=<backup_file> --gzip --drop
   ```
4. Stream output to client

#### `backup delete <filename>`
Deletes a backup file.

### 3. Database Operations

**Commands**:
- `db list` - List databases in connected instance
- `db switch <name>` - Switch to a database
- `collection list` - List collections in current database

**Note**: These operations require an active connection context (work in progress).

### 4. Authentication Commands

**Built-in Commands** (handled in frontend):
- `auth change-password` - Opens password change modal
- `auth logout` - Logs out user

**Built-in Terminal Commands**:
- `help` - Show available commands
- `clear` - Clear terminal history

## Command Parsing

**File**: `backend/app/core/cli.py`

### CLIParser Class

Parses natural language commands into structured data:

```python
command = "connect list"
result = CLIParser.parse(command)
# Returns: {
#   "category": "connect",
#   "action": "list",
#   "args": {}
# }
```

**Supported Categories**:
- `connect`: Connection management
- `backup`: Backup operations
- `db`: Database operations
- `collection`: Collection operations
- `auth`: Authentication

## Execution Flow

```
User types: "backup create prod-db"
    ↓
Frontend sends via WebSocket: {"type": "execute", "command": "..."}
    ↓
Backend receives command
    ↓
CLIParser.parse() → {category: "backup", action: "create", args: ["prod-db"]}
    ↓
Route to backup_ops.create_backup("prod-db")
    ↓
Execute mongodump subprocess
    ↓
Stream output to WebSocket:
    {"type": "output", "line": "Creating backup..."}
    {"type": "output", "line": "Backup created: prod-db_20240120.gz"}
    {"type": "complete", "status": "success"}
```

## MongoDB Storage

**Database**: `mongodb_manager`

**Collections**:

### `connections`
Stores saved MongoDB connections.

```json
{
  "name": "prod-db",
  "uri": "mongodb://localhost:27017",
  "description": "Production database",
  "created_at": "2024-01-20T19:00:00Z"
}
```

### `sessions`
Tracks user sessions.

```json
{
  "username": "admin",
  "created_at": "2024-01-20T19:00:00Z"
}
```

### `users`
Stores user credentials.

```json
{
  "username": "admin",
  "password_hash": "$2b$12$...",
  "created_at": "2024-01-20T19:00:00Z"
}
```

## Error Handling

### Connection Errors
- Invalid URI → Error message to client
- Connection timeout → "Failed to connect" message
- MongoDB down → Connection test fails

### Backup Errors
- mongodump not found → "mongodump command not available"
- Insufficient permissions → Permission error message
- Disk full → Space error message

### Command Errors
- Unknown command → "Command not recognized"
- Missing arguments → "Usage: <command> <args>"
- Invalid arguments → Specific validation error

## External Dependencies

**Required System Commands**:
- `mongodump` - For creating backups
- `mongorestore` - For restoring backups

**Python Packages**:
- `pymongo` - MongoDB driver
- `subprocess` - Execute shell commands
- `pathlib` - File path operations

## Related Documentation

- [02 - Backend Architecture](02-backend-architecture.md)
- [02.2 - WebSocket System](02.2-websocket-system.md)
- [01 - Overview](01-overview.md)
