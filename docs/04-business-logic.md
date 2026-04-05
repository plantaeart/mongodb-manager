# 04 - Business Logic (MongoDB Operations)
**Last Updated:** 2026-04-05

## Overview

Core MongoDB management operations: connection management, backup/restore, database operations.

## Command Categories

### 1. Connection Management

**File**: `backend/app/core/connection_ops.py`

#### `connect list`
Lists all saved MongoDB connections (opens a form panel).

#### `connect add`
Adds a new MongoDB connection (interactive stepper form).

**Flow**:
1. Prompt for connection details (name, host, port, credentials, description)
2. Test connection before saving
3. Save to MongoDB if successful

#### `connect remove`
Removes one or more saved connections (checkbox list form).

#### `connect test`
Tests one or more connections (checkbox list form).

#### `connect update`
Updates an existing connection (form).

#### `connect export`
Downloads all connections as a `connections.json` file to the browser. **Passwords are never included.**

Uses the File Widget system — see [12 - File Widget System](12-file-widget-system.md).

```python
# ConnectionManager.export_connections() — strips passwords
def export_connections(self) -> list[dict]:
    connections = self.list_connections()
    return [{k: v for k, v in conn.items() if k not in ('password', '_id')}
            for conn in connections]
```

#### `connect import`
Imports connections from a `connections.json` file uploaded from the browser.

Options:
- **Overwrite**: replace existing connections with the same name
- **Import backup paths**: preserve `backup_paths` from the file (off by default — paths may not exist on the target machine)

Uses the File Widget system — see [12 - File Widget System](12-file-widget-system.md).

### 2. Backup Operations

**File**: `backend/app/core/backup_ops.py`

#### `backup create`
Creates a backup using `mongodump`.

**Flow**:
1. Interactive form: choose connection + provide backup name
2. Run `mongodump --uri=<uri> --out=<backup_path>`
3. Save `metadata.json` alongside backup files
4. Stream output to terminal

#### `backup list`
Lists all backup folders across all registered backup paths.

#### `backup restore`
Restores a backup using `mongorestore` (interactive form).

#### `backup delete`
Deletes one or more backup folders.

#### `backup export`
Downloads a selected backup as a `.zip` file to the browser.

**Flow**:
1. File widget loads available backups from `/api/transfer/backup/export/options`
2. User selects a backup from the dropdown
3. Backend zips the backup folder in-memory (`zipfile.ZipFile` + `io.BytesIO`)
4. `StreamingResponse` sends the ZIP; browser downloads it via `downloadBlob()`

Uses the File Widget system — see [12 - File Widget System](12-file-widget-system.md).

```python
# BackupManager.export_backup_zip() — zips in memory
def export_backup_zip(self, backup_name: str) -> bytes:
    backup_path = self.backup_root / backup_name
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in backup_path.rglob("*"):
            if file_path.is_file():
                arcname = Path(backup_name) / file_path.relative_to(backup_path)
                zf.write(file_path, arcname)
    return buffer.getvalue()
```

#### `backup import`
Imports a `.zip` file (previously exported from this app) into a registered backup folder.

Options:
- **Destination folder**: must be a registered backup folder
- **Overwrite**: replace existing backup with the same name

Uses the File Widget system — see [12 - File Widget System](12-file-widget-system.md).

### 3. Authentication Commands

**Built-in Commands** (handled in frontend):
- `auth change-password` — Opens password change modal
- `auth logout` — Logs out user

**Built-in Terminal Commands**:
- `help` — Show available commands
- `clear` — Clear terminal history

## Command Routing

Commands are routed in `useTerminal.ts` through three paths:

| Path | Condition | Examples |
|------|-----------|---------|
| Built-in | `CLEAR`, `HELP` | `clear`, `help` |
| Form (REST + WebSocket) | listed in `COMMAND_TO_API_PATH` | `connect add`, `backup create` |
| File Widget (REST only) | in `FILE_WIDGET_COMMANDS` set | `backup export`, `connect import` |

## Execution Flows

### WebSocket-based command (e.g. `backup create`)
```
User types command
    ↓
Frontend sends via WebSocket: {"type": "execute", "command": "..."}
    ↓
Backend CLI parses command → dispatches to core ops
    ↓
Execute mongodump subprocess
    ↓
Stream output lines: {"type": "output", "line": "..."}
    {"type": "complete", "status": "success"}
```

### File Widget command (e.g. `backup export`)
```
User types command
    ↓
useTerminal detects FILE_WIDGET_COMMANDS match
    ↓
GET /api/transfer/backup/export/options  (fetch dropdown data)
    ↓
TerminalFileWidget.vue rendered in terminal
    ↓
User selects backup, clicks Export & Download
    ↓
GET /api/transfer/backup/export?backup_selector=...
    ↓
StreamingResponse (ZIP bytes) → downloadBlob() → browser saves file
```

## MongoDB Storage

**Database**: `mongodb_manager`

**Collections**:

### `connections`
Stores saved MongoDB connections.

```json
{
  "name": "prod-db",
  "host": "localhost",
  "port": 27017,
  "username": null,
  "database": null,
  "auth_source": null,
  "description": "Production database",
  "backup_paths": ["/data/backups/prod-db"]
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
- Connection timeout → "Failed to connect" message
- Auth failure → "Authentication failed" message

### Backup Errors
- `mongodump` not found → error message in terminal
- Backup not found → 404 from transfer endpoint
- Invalid ZIP → 400 from transfer endpoint

### Transfer Errors
- Unregistered folder → 400 "not a registered backup folder"
- Backup already exists without overwrite → 400 with hint to enable overwrite

## External Dependencies

**Required System Commands**:
- `mongodump` — For creating backups
- `mongorestore` — For restoring backups

**Python stdlib** (no extra packages):
- `zipfile`, `io` — In-memory ZIP pack/unpack for `backup export/import`

**Python Packages**:
- `pymongo` — MongoDB driver
- `subprocess` — Execute shell commands
- `pathlib` — File path operations

## Related Documentation

- [02 - Backend Architecture](02-backend-architecture.md)
- [02.2 - WebSocket System](02.2-websocket-system.md)
- [12 - File Widget System](12-file-widget-system.md)
- [01 - Overview](01-overview.md)
