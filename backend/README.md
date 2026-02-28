# MongoDB Manager

A CLI tool for managing MongoDB backups and restores using mongodump/mongorestore. Designed for easy backup management with support for multiple MongoDB connections.

## Features

- 🔌 **Connection Management**: Store and manage multiple MongoDB connections
- 💾 **Backup**: Create backups using mongodump with oplog support
- 🔄 **Restore**: Restore backups using mongorestore with optional --drop
- 📋 **List**: View all configured connections and backups
- ✅ **Test**: Verify MongoDB connections before use
- 🎨 **Interactive**: Beautiful CLI with interactive prompts (or use direct commands)
- 🔐 **Secure**: Password-based authentication with bcrypt hashing and MongoDB-backed session management

## Architecture

MongoDB Manager uses a dual-database architecture:

### Internal MongoDB (Application Data Storage)
- **Purpose**: Stores application data (connections, sessions, user auth)
- **Database**: `manager_app`
- **Collections**: 
  - `connections` - MongoDB connection configurations
  - `sessions` - User authentication sessions
  - `users` - User accounts and password hashes
- **Features**: 
  - Automatic session expiration via TTL index
  - Isolated Docker network (no external access)
  - Unique index on connection names
  - All data persisted in MongoDB (no file-based storage)

### External MongoDB (Backup Target)
- **Purpose**: Your production/VPS MongoDB instances
- **Operations**: Backup and restore operations using mongodump/mongorestore
- **Connections**: Stored in internal MongoDB `connections` collection

```
┌─────────────────────────────────────────────┐
│ Docker Network                              │
│                                              │
│  ┌──────────────────┐   ┌────────────────┐ │
│  │ mongodb-manager  │──►│ manager-mongodb│ │
│  │ (CLI App)        │   │ (Sessions DB)  │ │
│  └────────┬─────────┘   └────────────────┘ │
└───────────┼──────────────────────────────────┘
            │
            │ Connects to external MongoDB
            ▼
   ┌────────────────────┐
   │ VPS MongoDB 1      │
   │ Production MongoDB │
   │ (Backup/Restore)   │
   └────────────────────┘
```

## Authentication

MongoDB Manager uses password-based authentication to protect your database operations. Sessions are stored in an internal MongoDB database for enhanced security.

### First-Time Setup

1. **Default Password**: On first run, the default password is `admin123`
2. **Forced Change**: When you login with the default password, you'll be forced to change it
3. **Environment Variable**: After changing, update your environment with the new hash

### Authentication Flow

```bash
# Run any command - authentication will be prompted
docker-compose run --rm mongodb-manager connect list

# First time with default password:
Enter password: admin123
⚠️  You are using the default password!
For security, you must change it now.

Enter new password: ********
Confirm new password: ********

✓ Password changed successfully!
Your new password is now active. No restart needed!

# Password is stored in MongoDB - ready to use immediately!
```

### Environment Setup

#### Docker Development (Recommended)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update internal MongoDB credentials (optional but recommended):
   ```bash
   MANAGER_DB_USERNAME=manager_admin
   MANAGER_DB_PASSWORD=your_secure_password_here
   ```

3. Start services:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. Login with default credentials and change password:
   - Username: `admin`
   - Password: `admin123`
   - System will force password change on first login
   - New password stored in MongoDB (no restart needed!)

#### Coolify Deployment

1. Add environment variables in Coolify dashboard:
   ```bash
   # Internal MongoDB credentials
   MANAGER_DB_USERNAME=manager_admin
   MANAGER_DB_PASSWORD=your_secure_password_here
   
   # Timezone
   TZ=Europe/Paris
   
   # Coolify flag
   COOLIFY=true
   ```

2. Add persistent volumes:
   - `/backups_mongodb_manager` → Backup storage
   - MongoDB data managed internally (connections stored in database)

3. Deploy and login with default credentials (`admin` / `admin123`)
4. System will force password change
5. Password stored in MongoDB - no restart needed!

### Session Management

- **Duration**: Sessions last 24 hours
- **Storage**: Sessions stored in internal MongoDB (`manager_app.sessions`)
- **User Tracking**: Each session linked to username
- **Auto-Cleanup**: Expired sessions automatically deleted via TTL index
- **Automatic**: Session checked before each command
- **Re-auth**: Prompts for password when session expires
- **Security**: MongoDB authentication required, isolated Docker network

### Auth Commands

```bash
# Check session status
mongodb-manager auth status

# Change password (instant, no restart needed!)
mongodb-manager auth change

# Logout (clear session)
mongodb-manager auth logout

# Generate password hash (for manual testing)
mongodb-manager auth hash
```

### Security Best Practices

1. Change default CLI password immediately on first use (forced on first login)
2. Change internal MongoDB password (`MANAGER_DB_PASSWORD`) before deployment
3. Use strong passwords (minimum 8 characters)
4. Don't commit `.env` files to version control
5. Rotate passwords regularly
6. Keep environment variables secure
7. Internal MongoDB is isolated on Docker network (no external access)

## Installation

### Using UV (Recommended)

```bash
cd mongodb-manager-app
uv sync
```

### Using pip

```bash
cd mongodb-manager-app
pip install -e .
```

## Quick Start

### 1. Add a MongoDB Connection

```bash
# Interactive mode
mongodb-manager connect add --name prod --uri "mongodb://admin:password@localhost:27017" --description "Production DB"

# Example with authentication
mongodb-manager connect add --name dev --uri "mongodb://localhost:27017"
```

### 2. Test Connection

```bash
# Test specific connection
mongodb-manager connect test --name prod

# Test all connections
mongodb-manager connect test --all
```

### 3. Initialize Backup Folder

```bash
# Use default path (/backups_mongodb_manager)
mongodb-manager init-backup

# Or specify custom path
mongodb-manager init-backup --path /mnt/backups_mongodb_manager
```

### 4. Create Backup

```bash
# Interactive mode (select from list)
mongodb-manager backup

# Direct mode
mongodb-manager backup --connection prod
```

### 5. List Backups

```bash
mongodb-manager list-backups
```

### 6. Restore Backup

```bash
# Interactive mode
mongodb-manager restore

# Direct mode
mongodb-manager restore --backup prod_19012026_215500 --connection prod

# With --drop flag (drops existing collections before restore)
mongodb-manager restore --backup prod_19012026_215500 --connection prod --drop
```

### 7. Clear Backups

```bash
# Interactive mode (select from list)
mongodb-manager clear

# Delete specific backup
mongodb-manager clear --backup prod_19012026_215500

# Delete all backups
mongodb-manager clear --all
```

## Command Reference

### Authentication Commands

```bash
# Check session status
mongodb-manager auth status

# Change password
mongodb-manager auth change

# Logout
mongodb-manager auth logout

# Generate password hash
mongodb-manager auth hash [--password <password>]
```

### Connection Commands

```bash
# Add connection
mongodb-manager connect add --name <name> --uri <uri> [--description <desc>]

# List connections
mongodb-manager connect list

# Test connection
mongodb-manager connect test [--name <name>] [--all]

# Remove connection
mongodb-manager connect remove [--name <name>]
```

### Backup Commands

```bash
# Initialize backup folder
mongodb-manager init-backup [--path <path>]

# Create backup
mongodb-manager backup [--connection <name>] [--backup-path <path>]

# List backups
mongodb-manager list-backups [--backup-path <path>]

# Restore backup
mongodb-manager restore [--backup <name>] [--connection <name>] [--drop] [--backup-path <path>]

# Delete backups
mongodb-manager clear [--backup <name>] [--all] [--backup-path <path>]
```

## Docker Usage

### Architecture

The Docker setup includes two services:
- **manager-mongodb**: Internal MongoDB for session storage (isolated, not exposed)
- **mongodb-manager**: CLI application

Both services communicate over an isolated Docker network.

### Build Image

```bash
docker build -f docker/Dockerfile -t mongodb-manager .
```

### Using Docker Compose (Recommended)

First, create a `.env` file with your credentials:

```bash
cp .env.example .env
# Edit .env and update:
# - MONGODB_MANAGER_PASSWORD_HASH (CLI password)
# - MANAGER_DB_USERNAME (internal MongoDB user)
# - MANAGER_DB_PASSWORD (internal MongoDB password)
```

Start the services:

```bash
# Start internal MongoDB and app
docker-compose -f docker/docker-compose.yml up -d
```

Run commands:

```bash
# Check authentication status
docker-compose -f docker/docker-compose.yml run --rm mongodb-manager auth status

# Add external MongoDB connection
docker-compose -f docker/docker-compose.yml run --rm mongodb-manager \
  connect add \
  --name production \
  --uri "mongodb://user:pass@your-vps-server:27017" \
  --description "Production Database"

# Create backup
docker-compose -f docker/docker-compose.yml run --rm mongodb-manager backup --connection production

# List backups
docker-compose -f docker/docker-compose.yml run --rm mongodb-manager list-backups
```

### Inspecting Internal MongoDB (Advanced)

To inspect session data in the internal MongoDB:

```bash
# Connect to internal MongoDB
docker exec -it manager-mongodb mongosh \
  -u manager_admin \
  -p changeme123 \
  --authenticationDatabase admin

# Switch to app database
use manager_app

# View sessions
db.sessions.find().pretty()

# Check indexes
db.sessions.getIndexes()

# Count active sessions
db.sessions.count()
```

### Deploy to Coolify

1. Set environment variables in Coolify:
   ```bash
   # Internal MongoDB credentials
   MANAGER_DB_USERNAME=manager_admin
   MANAGER_DB_PASSWORD=your_secure_password_here
   
   # Timezone and environment
   TZ=Europe/Paris
   COOLIFY=true
   ```

2. Configure volumes:
   - `/backups_mongodb_manager` → mongodb-backups (backup storage)
   - MongoDB data volume is managed internally (connections stored in database)

3. Deploy and login with default credentials (`admin` / `admin123`)

4. System will force password change - password stored in MongoDB (no restart needed!)

## Configuration

### Connections

Connections are stored in the internal MongoDB database (`manager_app.connections` collection):

```json
{
  "_id": ObjectId("..."),
  "name": "prod",
  "uri": "mongodb://admin:password@prod-server:27017",
  "description": "Production Database",
  "created_by": "admin",
  "added_at": ISODate("2026-01-19T21:55:00Z"),
  "updated_at": ISODate("2026-01-19T21:55:00Z")
}
```

**Features:**
- Stored in MongoDB (no file-based storage)
- Unique index on `name` field
- Indexed on `created_by` and `added_at` for fast queries
- Supports multi-user isolation (ready for future)

### Authentication Configuration

Authentication is configured via environment variables:

```bash
# .env file (Docker Compose)

# Internal MongoDB credentials (user accounts & sessions storage)
MANAGER_DB_USERNAME=manager_admin
MANAGER_DB_PASSWORD=changeme123

# Timezone (default: Europe/Paris for France)
TZ=Europe/Paris

# Coolify environment detection
COOLIFY=true
```

**Note**: All timestamps (backups, sessions, logs) use the configured timezone (Europe/Paris by default).

### User Storage

User accounts are stored in internal MongoDB (`manager_app.users` collection):

```json
{
  "_id": ObjectId("..."),
  "username": "admin",
  "password_hash": "$2b$12$...",
  "is_default": false,
  "created_at": ISODate("2026-01-19T10:00:00Z"),
  "updated_at": ISODate("2026-01-19T15:30:00Z")
}
```

**Features:**
- Passwords hashed with bcrypt (industry standard)
- Default admin user created on first run
- Password changes instant (no restart needed)
- Ready for multi-user support in future

### Session Storage

Sessions are stored in internal MongoDB (`manager_app.sessions` collection):

```json
{
  "_id": ObjectId("..."),
  "username": "admin",
  "token": "uuid-v4",
  "created_at": ISODate("2026-01-19T10:00:00Z"),
  "expires_at": ISODate("2026-01-20T10:00:00Z"),
  "last_accessed": ISODate("2026-01-19T15:30:00Z")
}
```

**Features:**
- Automatic expiration via TTL index (24 hours)
- Last accessed timestamp tracking
- Linked to username (multi-user ready)
- Isolated Docker network security
- No file-based storage

## Backup Structure

Backups are stored in the following structure:

```
/backups_mongodb_manager/
├── prod_19012026_215500/          # Backup folder (connection_DDMMYYYY_HHMMSS)
│   ├── admin/                      # MongoDB databases
│   ├── myapp/
│   ├── oplog.bson                 # Point-in-time consistency
│   └── metadata.json              # Backup metadata
├── prod_20012026_103000/          # Another backup
└── dev_19012026_220000/           # Different connection
```

## Requirements

- Python 3.13+
- MongoDB tools (mongodump, mongorestore) - included in Docker image
- Access to MongoDB server(s)

## Development

### Install Dev Dependencies

```bash
uv sync --all-extras
```

### Run Tests

```bash
pytest
```

### Format Code

```bash
ruff format src/
```

### Lint Code

```bash
ruff check src/
```

## Tips

- Use `--help` on any command to see available options
- All commands support both interactive and direct modes
- Backup folder path must end with `_mongodb_manager`
- Default backup path is `/backups_mongodb_manager`
- Connection URIs support all MongoDB connection string formats
- Use `--drop` flag with restore to replace existing data

## Troubleshooting

### Authentication Failed

```bash
# Check if password hash is set correctly
echo $MONGODB_MANAGER_PASSWORD_HASH

# Generate new hash
mongodb-manager auth hash

# Update .env file with new hash
# Then restart the application

# Check session status
mongodb-manager auth status

# Logout and login again
mongodb-manager auth logout
mongodb-manager connect list  # Will prompt for login
```

### Session Expired

Sessions last 24 hours. When expired, you'll be prompted to login again:

```bash
# Run any command
mongodb-manager connect list

# You'll see:
Authentication required
Enter password: ********
```

### Forgot Password

**Option 1: Reset to Default (Development Only)**
```bash
# Set default hash in .env
MONGODB_MANAGER_PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqXw5L6T3u

# Login with: admin123
# Change password immediately
```

**Option 2: Generate New Hash**
```bash
# If you have access to the tool
mongodb-manager auth hash --password "new-password"

# Copy hash to .env or Coolify environment variable
```

### Connection Test Fails

```bash
# Check if MongoDB is running
mongosh <your-uri>

# Verify connection string format
mongodb://[username:password@]host[:port][/database][?options]
```

### Backup Fails

```bash
# Ensure mongodump is installed
mongodump --version

# Check MongoDB connection
mongodb-manager connect test --name <connection-name>

# Verify backup folder permissions
ls -la /backups_mongodb_manager
```

### Restore Fails

```bash
# Ensure mongorestore is installed
mongorestore --version

# Check if backup exists
mongodb-manager list-backups

# Use --drop flag if you want to replace existing data
mongodb-manager restore --backup <name> --connection <name> --drop
```

## License

MIT

## Author

MongoDB Manager Team
