# 02 - Backend Architecture

## Overview

The backend is a FastAPI application that provides:
1. REST API for authentication and configuration
2. WebSocket for real-time terminal communication
3. MongoDB operations (backup, restore, connection management)

## Directory Structure

```
backend/app/
├── api/              # REST API endpoints
│   ├── auth.py       # Login, password change
│   └── __init__.py
├── websocket/        # WebSocket handlers
│   └── terminal.py   # Terminal command execution
├── core/             # Business logic
│   ├── auth.py       # Authentication manager
│   ├── backup_ops.py # Backup/restore operations
│   ├── cli.py        # CLI command parser
│   ├── connection_ops.py  # Connection management
│   └── utils/        # Utilities (config, timezone)
├── middleware/       # Request middleware
│   └── auth.py       # JWT authentication
├── models/           # Pydantic models
│   ├── auth.py       # Auth request/response models
│   ├── backup.py     # Backup models
│   ├── connection.py # Connection models
│   └── terminal.py   # Terminal message models
└── main_api.py       # Application entry point
```

## Application Entry Point

**File**: `backend/app/main_api.py`

Key components:
- Creates FastAPI app instance
- Configures CORS middleware
- Mounts REST API routes (`/api`)
- Registers WebSocket endpoint (`/ws/terminal`)
- Starts on port 8000 (mapped to 9000/9001 externally)

## Request Flow

### REST API Flow
```
Client → FastAPI → Auth Middleware → API Endpoint → Core Logic → MongoDB
```

### WebSocket Flow
```
Client → WebSocket → JWT Verification → Command Parser → Executor → Response Stream
```

## Key Components

### 1. Authentication (`core/auth.py`)
- Manages user authentication with bcrypt
- Handles session storage in MongoDB
- Provides password verification and updates
- Default user: `admin` with configurable password

### 2. CLI Parser (`core/cli.py`)
- Parses terminal commands into structured data
- Supports command categories: connect, backup, db, collection, auth
- Returns command type and parsed arguments

### 3. Connection Operations (`core/connection_ops.py`)
- CRUD operations for MongoDB connections
- Connection testing and validation
- Stores connection configs in MongoDB

### 4. Backup Operations (`core/backup_ops.py`)
- Creates backups using `mongodump`
- Restores backups using `mongorestore`
- Lists available backup files
- Manages backup storage directory

## MongoDB Usage

The backend uses MongoDB for:
1. **User Sessions**: Track active sessions with timestamps
2. **Connection Storage**: Save MongoDB connection configurations
3. **User Credentials**: Store hashed passwords

Database: `mongodb_manager`
Collections:
- `sessions`: User session data
- `connections`: MongoDB connection configs
- `users`: User credentials (hashed passwords)

## Environment Configuration

Key backend environment variables:
- `MANAGER_DB_URI`: Internal MongoDB for session/config storage
- `JWT_SECRET_KEY`: Secret for signing JWT tokens
- `DEFAULT_PASSWORD`: Initial admin password
- `NODE_ENV`: Controls password change enforcement (dev/prod)

## Error Handling

- HTTP exceptions for REST API errors
- WebSocket error messages for command failures
- Structured error responses with detail messages

## Related Documentation

- [02.1 - Authentication System](02.1-authentication-system.md) - Detailed auth flow
- [02.2 - WebSocket System](02.2-websocket-system.md) - WebSocket implementation
- [04 - Business Logic](04-business-logic.md) - Command execution logic
