# 05 - Deployment Guide

## Overview

Docker-based deployment with separate configurations for development and production environments.

## Quick Start

### Development
```bash
# Start dev environment
./scripts/docker.sh dev up -d

# View logs
./scripts/docker.sh dev logs frontend
./scripts/docker.sh dev logs backend

# Stop
./scripts/docker.sh dev down
```

### Production
```bash
# Start prod environment  
./scripts/docker.sh prod up -d

# View logs
./scripts/docker.sh prod logs frontend --tail 50

# Stop
./scripts/docker.sh prod down
```

## Environment Files

### `.env.dev` (Development)
```bash
NODE_ENV=development          # Skips forced password change
DEFAULT_PASSWORD=admin123     # Default admin password
JWT_SECRET_KEY=dev-secret     # JWT signing key
MANAGER_DB_URI=mongodb://manager-mongodb-dev:27017/mongodb_manager
```

### `.env.prod` (Production)
```bash
NODE_ENV=production           # Enforces password change
DEFAULT_PASSWORD=ChangeMe123  # CHANGE THIS!
JWT_SECRET_KEY=<random-key>   # CHANGE THIS!
MANAGER_DB_URI=mongodb://manager-mongodb-prod:27017/mongodb_manager
```

**IMPORTANT**: Always change default passwords and secrets in production!

## Docker Compose Files

### Development (`docker/docker-compose.dev.yml`)
**Services**:
- `frontend` - Nuxt dev server (port 4000)
- `backend` - Uvicorn with hot reload (port 9000)
- `manager-mongodb-dev` - MongoDB 7.0 for internal storage

**Features**:
- Hot module replacement (auto-reload on code changes)
- Volume mounts for live development
- Debug-friendly configuration

### Production (`docker/docker-compose.prod.yml`)
**Services**:
- `frontend` - Optimized Nuxt build (port 4001)
- `backend` - Uvicorn production mode (port 9001)
- `manager-mongodb-prod` - MongoDB 7.0 with persistence

**Features**:
- Production builds (optimized, minified)
- Named volumes for data persistence
- Health checks enabled
- Resource limits configured

## Ports

| Service | Dev Port | Prod Port |
|---------|----------|-----------|
| Frontend | 4000 | 4001 |
| Backend | 9000 | 9001 |
| MongoDB | 27017 (internal) | 27017 (internal) |

## Volume Mounts

### Development
```yaml
volumes:
  - ../frontend:/app              # Live code reload
  - ../backend:/app               # Live code reload
  - mongodb-dev-data:/data/db     # MongoDB persistence
```

### Production
```yaml
volumes:
  - mongodb-prod-data:/data/db    # MongoDB persistence
  - backup-storage:/app/backups   # Backup files
```

## Health Checks

### Frontend
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:4000/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Backend
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Helper Script

**File**: `scripts/docker.sh`

**Usage**:
```bash
./scripts/docker.sh <env> <command> [options]

# Examples:
./scripts/docker.sh dev up -d           # Start dev
./scripts/docker.sh prod logs backend   # View prod logs
./scripts/docker.sh dev down --volumes  # Stop and remove volumes (interactive)
```

**Environments**: `dev` | `prod`

**Commands**: `up`, `down`, `logs`, `restart`, `ps`, `exec`

### Bypassing Interactive Prompts

Some commands require confirmation (like `down --volumes`). To bypass prompts in automated scripts:

```bash
# Use echo to pipe confirmation
echo "yes" | ./scripts/docker.sh dev down --volumes

# Or use docker-compose directly
docker-compose -f docker/docker-compose.dev.yml --env-file .env.dev down -v

# Examples:
echo "yes" | ./scripts/docker.sh dev reset        # Reset dev environment
echo "yes" | ./scripts/docker.sh prod down --volumes  # Remove prod volumes
```

## First-Time Setup

### 1. Clone Repository
```bash
git clone <repo-url>
cd mongodb-manager-app
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env.prod

# Edit production settings
nano .env.prod

# IMPORTANT: Change these values!
# - DEFAULT_PASSWORD
# - JWT_SECRET_KEY
# - CORS_ORIGINS (if needed)
```

### 3. Start Services
```bash
# Development
./scripts/docker.sh dev up -d

# Production
./scripts/docker.sh prod up -d
```

### 4. Access Application
- **Dev**: http://localhost:4000
- **Prod**: http://localhost:4001

### 5. First Login
- Username: `admin`
- Password: (from DEFAULT_PASSWORD in .env file)
- **Production**: Will force password change on first login

## Updating the Application

### Development
Code changes auto-reload (hot module replacement).

### Production
```bash
# Pull latest changes
git pull

# Rebuild and restart
./scripts/docker.sh prod down
./scripts/docker.sh prod up -d --build
```

## Backup Considerations

### Application Data
- MongoDB data stored in Docker volumes
- Backup files stored in `/app/backups` (configurable)

### Backup MongoDB Manager Data
```bash
# Backup internal MongoDB
docker exec manager-mongodb-prod mongodump \
  --db mongodb_manager \
  --archive=/backup/manager-backup.gz \
  --gzip
```

### Restore MongoDB Manager Data
```bash
# Restore internal MongoDB
docker exec manager-mongodb-prod mongorestore \
  --archive=/backup/manager-backup.gz \
  --gzip
```

## Troubleshooting

### Containers Won't Start
```bash
# Check logs
./scripts/docker.sh dev logs

# Check container status
docker ps -a
```

### Port Already in Use
```bash
# Find process using port
lsof -i :4000

# Kill process or change port in docker-compose file
```

### Frontend Not Loading
1. Check if container is healthy: `docker ps`
2. Hard refresh browser: `Ctrl+Shift+R`
3. Check frontend logs: `./scripts/docker.sh dev logs frontend`

### WebSocket Connection Failed
1. Verify backend is running
2. Check CORS settings in `.env` file
3. Verify JWT token is valid
4. Check network tab in browser DevTools

## Security Checklist (Production)

- [ ] Change DEFAULT_PASSWORD
- [ ] Generate random JWT_SECRET_KEY
- [ ] Configure CORS_ORIGINS for your domain
- [ ] Use HTTPS (reverse proxy recommended)
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

## Related Documentation

- [01 - Overview](01-overview.md)
- [02.1 - Authentication System](02.1-authentication-system.md)
