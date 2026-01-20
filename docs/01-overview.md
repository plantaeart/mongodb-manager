# 01 - MongoDB Manager Overview

## Project Description

MongoDB Manager is a full-stack web application for managing MongoDB databases through a terminal-style interface. It provides backup/restore operations, connection management, and database administration capabilities.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.13)
- **WebSocket**: Native FastAPI WebSocket support
- **Database**: MongoDB 7.0 (for internal session/config storage)
- **Authentication**: JWT tokens + bcrypt password hashing
- **MongoDB Operations**: pymongo, mongodump, mongorestore

### Frontend
- **Framework**: Nuxt 4.2.2 (Vue 3.5.27)
- **UI Library**: @nuxt/ui (TailwindCSS + Headless UI)
- **State Management**: Pinia
- **Theme**: Custom Gruvbox color scheme
- **WebSocket**: Native browser WebSocket API

### Infrastructure
- **Container**: Docker + Docker Compose
- **Environments**: Separate dev/prod configurations
- **Process Manager**: Uvicorn (backend), Node.js (frontend)

## Project Structure

```
mongodb-manager-app/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── websocket/    # WebSocket handlers
│   │   ├── core/         # Business logic
│   │   ├── models/       # Pydantic models
│   │   └── middleware/   # Auth middleware
│   └── requirements.txt
├── frontend/             # Nuxt frontend
│   ├── app/
│   │   ├── components/   # Vue components
│   │   ├── composables/  # Singleton services
│   │   ├── stores/       # Pinia stores
│   │   ├── pages/        # Route pages
│   │   └── types/        # TypeScript types
│   └── package.json
├── docker/               # Docker configurations
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
├── scripts/              # Helper scripts
│   └── docker.sh         # Docker management
├── docs/                 # Documentation (this folder)
├── .env.dev             # Dev environment variables
└── .env.prod            # Prod environment variables
```

## Key Features

1. **Terminal Interface**: Command-line style UI for MongoDB operations
2. **Real-time Communication**: WebSocket for live command output
3. **Connection Management**: Save and manage multiple MongoDB connections
4. **Backup/Restore**: Create and restore MongoDB backups (mongodump/mongorestore)
5. **Authentication**: Secure login with forced password change on first use
6. **Multi-Environment**: Separate dev/prod configurations

## Ports

- **Dev**: Frontend (4000), Backend (9000)
- **Prod**: Frontend (4001), Backend (9001)

## Environment Variables

Key environment variables:
- `NODE_ENV`: development/production (controls password change requirement)
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `DEFAULT_PASSWORD`: Initial admin password
- `MANAGER_DB_URI`: MongoDB connection for internal storage

See `.env.example` for complete list.

## Related Documentation

- [02 - Backend Architecture](02-backend-architecture.md)
- [02.1 - Authentication System](02.1-authentication-system.md)
- [02.2 - WebSocket System](02.2-websocket-system.md)
- [03 - Frontend Architecture](03-frontend-architecture.md)
- [03.1 - State Management](03.1-state-management.md)
- [04 - Business Logic](04-business-logic.md)
- [05 - Deployment](05-deployment.md)
