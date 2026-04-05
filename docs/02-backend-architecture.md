# 02 - Backend Architecture
**Last Updated:** 2026-04-05

## Overview

The backend is a FastAPI application that provides:
1. REST API for authentication, forms, and file transfer
2. WebSocket for real-time terminal communication
3. MongoDB operations (backup, restore, connection management)

## Directory Structure

```
backend/app/
├── routers/          # REST API routers
│   ├── auth.py       # Login, password change
│   ├── forms.py      # Form definitions for CLI commands
│   ├── transfer.py   # File transfer (backup/connect export & import)
│   └── __init__.py
├── websocket/        # WebSocket handlers
│   └── terminal.py   # Terminal command execution
├── core/             # Business logic
│   ├── auth.py       # Authentication manager
│   ├── backup_ops.py # Backup/restore + ZIP export/import
│   ├── cli.py        # CLI command parser
│   ├── connection_ops.py  # Connection management + JSON export/import
│   └── utils/        # Utilities (config, timezone, backup_utils)
├── middleware/       # Request middleware
│   └── auth.py       # JWT authentication
├── models/           # Pydantic models
│   ├── auth.py       # Auth request/response models
│   └── terminal.py   # Terminal message models
├── enums/            # Shared enums
│   └── commands.py   # Command enum (used by CLI + tests)
└── main_api.py       # Application entry point
```

## Application Entry Point

**File**: `backend/app/main_api.py`

Key components:
- Creates FastAPI app instance
- Configures CORS middleware
- Registers routers: `auth`, `forms`, `transfer`, `commands`
- Registers WebSocket endpoint (`/ws/terminal`)
- Starts on port 8000 (mapped to 9000/9001 externally)

## Request Flows

### REST API (forms / auth)
```
Client → FastAPI → Auth Middleware → Router → Core Logic → MongoDB
```

### WebSocket (terminal commands)
```
Client → WebSocket → JWT Verification → CLI Parser → Core Ops → Response Stream
```

### File Transfer (export / import)
```
Client → GET/POST /api/transfer/... → Auth Middleware → Transfer Router
    export → Core Ops → StreamingResponse (ZIP or JSON bytes)
    import → Core Ops → JSON result
```

## Key Components

### 1. Authentication (`core/auth.py`)
- Manages user authentication with bcrypt
- Provides password verification and updates
- Default user: `admin` with configurable password

### 2. CLI Parser (`core/cli.py`)
- Parses terminal commands into structured data
- Supports command categories: connect, backup, db, collection, auth
- Returns command type and parsed arguments

### 3. Connection Operations (`core/connection_ops.py`)
- CRUD operations for MongoDB connections
- Connection testing and validation
- `export_connections()` — sanitises connections (strips passwords)
- `import_connections()` — upserts connections from JSON payload

### 4. Backup Operations (`core/backup_ops.py`)
- Creates backups using `mongodump`
- Restores backups using `mongorestore`
- Lists and deletes backup folders
- `export_backup_zip()` — zips a backup folder in memory
- `import_backup_zip()` — extracts a ZIP into a backup folder

### 5. Transfer Router (`routers/transfer.py`)
- Dedicated REST router for file-based operations (prefix `/api/transfer`)
- 4 transfer endpoints + 2 options endpoints
- All require JWT authentication
- See [12 - File Widget System](12-file-widget-system.md) for full details

## MongoDB Usage

The backend uses MongoDB for:
1. **Connection Storage**: Save MongoDB connection configurations
2. **User Credentials**: Store hashed passwords

Database: `mongodb_manager`
Collections:
- `connections`: MongoDB connection configs
- `users`: User credentials (hashed passwords)

## Environment Configuration

Key backend environment variables:
- `MANAGER_DB_URI`: Internal MongoDB for session/config storage
- `JWT_SECRET_KEY`: Secret for signing JWT tokens
- `DEFAULT_PASSWORD`: Initial admin password
- `NODE_ENV`: Controls password change enforcement (dev/prod)

## Error Handling

- HTTP exceptions for REST API errors (4xx / 5xx with `detail` field)
- WebSocket error messages for command failures
- Structured error responses with detail messages

## Related Documentation

- [02.1 - Authentication System](02.1-authentication-system.md) - Detailed auth flow
- [02.2 - WebSocket System](02.2-websocket-system.md) - WebSocket implementation
- [04 - Business Logic](04-business-logic.md) - Command execution logic
- [12 - File Widget System](12-file-widget-system.md) - Transfer endpoints
