# MongoDB Manager - Web UI

A modern web-based tool for managing MongoDB backups and restores with a terminal-style interface. Built with FastAPI backend and Nuxt 3 frontend featuring a beautiful Gruvbox theme.

## Features

- 🌐 **Web Interface**: Terminal-style UI accessible from any browser
- 🔌 **Connection Management**: Store and manage multiple MongoDB connections
- 💾 **Backup Operations**: Create backups using mongodump with oplog support
- 🔄 **Restore Operations**: Restore backups using mongorestore with optional --drop
- 📋 **Visual Panel**: Quick actions, favorites, and command reference
- ⚡ **Real-time Streaming**: Command output streams live via WebSocket
- 🔐 **Secure Authentication**: JWT-based auth with forced password change on first login
- 🎨 **Beautiful UI**: Retro terminal aesthetic with Gruvbox color scheme
- 📜 **Command History**: Navigate previous commands with arrow keys
- 🔍 **Autocomplete**: Tab completion for available commands

## Architecture

MongoDB Manager uses a modern full-stack architecture:

### Backend (FastAPI)
- **Port**: 8000
- **API**: RESTful endpoints for authentication and operations
- **WebSocket**: Real-time command execution and output streaming
- **Database**: Internal MongoDB for sessions and user data
- **CLI Core**: Wrapped existing CLI logic for command execution

### Frontend (Nuxt 3)
- **Port**: 3000
- **Framework**: Nuxt 3 with Vue 3 Composition API
- **UI**: Terminal-style interface with split view
- **Theme**: Gruvbox color palette
- **State**: Composables for auth, WebSocket, and terminal

### Internal MongoDB (Session Storage)
- **Purpose**: Stores user authentication and sessions
- **Database**: `manager_app`
- **Collections**: `users`, `sessions`
- **Features**: 
  - Automatic session expiration via TTL index
  - Isolated Docker network (no external access)
  - Secure password hashing with bcrypt

### External MongoDB (Backup Target)
- **Purpose**: Your production/VPS MongoDB instances
- **Operations**: Backup and restore operations
- **Connections**: Managed via web interface

```
┌─────────────────────────────────────────────────────┐
│ Docker Network                                      │
│                                                      │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────┐│
│  │  Frontend   │──►│   Backend    │──►│ Internal ││
│  │  (Nuxt 3)   │   │  (FastAPI)   │   │ MongoDB  ││
│  │  Port 3000  │   │  Port 8000   │   │ Sessions ││
│  └─────────────┘   └──────┬───────┘   └──────────┘│
└────────────────────────────┼──────────────────────┘
                             │
                             │ Manages external MongoDB
                             ▼
                    ┌────────────────────┐
                    │ VPS MongoDB        │
                    │ Production MongoDB │
                    │ (Backup/Restore)   │
                    └────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 1GB free disk space

### Installation

MongoDB Manager provides separate configurations for **development** and **production** environments.

#### Development Mode (with hot-reload)

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd mongodb-manager
   ```

2. **Define .env or .env.dev file**:
   Use .env.example to define your env files in local

3. **Start development environment**:
   ```bash
   ./scripts/docker.sh dev up
   ```

   Or manually:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml --env-file .env.dev up -d
   ```

4. **Access the web interface**:
   - Frontend: http://localhost:3000 (hot-reload enabled)
   - Backend API: http://localhost:8000 (hot-reload enabled)
   - API Docs: http://localhost:8000/docs

**Development Features**:
- ✅ Hot-reload for backend (uvicorn --reload)
- ✅ Hot-reload for frontend (Nuxt dev server)
- ✅ Source code mounted as volumes
- ✅ Verbose logging for debugging
- ✅ No resource limits
- ✅ Separate dev database volumes

#### Production Mode (optimized builds)

1. **Copy and configure production environment**:
   ```bash
   cp .env.prod .env.prod.local
   ```

2. **Update production credentials** (`.env.prod.local`):
   ```bash
   # CRITICAL: Change these before deploying!
   MANAGER_DB_USERNAME=manager_admin_prod
   MANAGER_DB_PASSWORD=$(openssl rand -base64 24)
   JWT_SECRET=$(openssl rand -base64 64)
   
   # Ports (optional)
   FRONTEND_PORT=3000
   BACKEND_PORT=8000
   
   # Timezone
   TZ=UTC
   ```

3. **Start production environment**:
   ```bash
   ./scripts/docker.sh prod up
   ```

   Or manually:
   ```bash
   docker-compose -f docker/docker-compose.prod.yml --env-file .env.prod.local up -d
   ```

4. **Access the web interface**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

**Production Features**:
- ✅ Multi-stage Docker builds (optimized size)
- ✅ Resource limits (CPU/memory)
- ✅ Log rotation (10MB max, 3 files)
- ✅ Health checks with auto-restart
- ✅ Non-root user execution
- ✅ Separate production volumes

### First Login

1. Open http://localhost:3000 in your browser
2. Login with default credentials:
   - Password: `admin123`
3. You'll be forced to change the password immediately
4. Set a strong password (minimum 8 characters)
5. Done! Your new password is stored securely in MongoDB

## Usage

### Terminal Commands

The web interface provides a terminal where you can execute commands:

#### Connection Management
```bash
connect list              # List all MongoDB connections
connect add               # Add a new connection (interactive)
connect remove <name>     # Remove a connection
connect test <name>       # Test a connection
```

#### Backup Operations
```bash
backup create <name>      # Create a backup of the specified connection
backup list               # List all available backups
backup restore <file>     # Restore a backup
backup delete <file>      # Delete a backup file
```

#### Other Commands
```bash
help                      # Show available commands
clear                     # Clear terminal output
auth change-password      # Change your password
auth logout               # Logout
```

### Visual Panel

Click "Show Panel" to access:
- **Favorites**: Save frequently used commands
- **Quick Actions**: One-click buttons for common operations
- **Command Reference**: Quick help for all commands

### Features

#### Real-time Output
Commands execute on the backend and stream output in real-time to your browser via WebSocket.

#### Command History
- Press `↑` to navigate to previous commands
- Press `↓` to navigate to next commands
- Up to 50 commands stored in history

#### Autocomplete
- Start typing a command
- Press `Tab` to complete or cycle through suggestions
- Suggestions include both standard commands and your favorites

#### Syntax Highlighting
- Success messages in green
- Errors in red
- Warnings in yellow
- Info messages in blue

## Development

### Project Structure

```
mongodb-manager-app/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # CLI logic (auth, backups, etc.)
│   │   ├── models/           # Pydantic models
│   │   ├── middleware/       # JWT authentication
│   │   ├── websocket/        # WebSocket handlers
│   │   └── main_api.py       # FastAPI app entry point
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── main.py               # CLI entry point (legacy)
│
├── frontend/
│   ├── app/
│   │   ├── components/       # Vue components
│   │   │   ├── Auth/         # Login, password change
│   │   │   ├── Terminal/     # Terminal UI components
│   │   │   └── Panel/        # Visual panel
│   │   ├── composables/      # Vue composables
│   │   │   ├── useAuth.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useTerminal.ts
│   │   ├── types/            # TypeScript types
│   │   ├── pages/            # Nuxt pages
│   │   └── assets/           # CSS, images
│   ├── Dockerfile
│   ├── nuxt.config.ts
│   └── package.json
│
├── docker/
│   ├── docker-compose.dev.yml   # Development configuration
│   ├── docker-compose.prod.yml  # Production configuration
│   └── docker-compose.yml       # Legacy (points to prod)
│
├── scripts/
│   └── docker.sh                # Docker helper script
│
├── .env.dev                     # Development environment
├── .env.prod                    # Production template
├── .env.example                 # Legacy example
└── README.md
```

### Docker Helper Script

A convenience script is provided to manage both dev and prod environments:

```bash
# Development
./scripts/docker.sh dev up          # Start dev environment
./scripts/docker.sh dev down        # Stop dev environment
./scripts/docker.sh dev build       # Rebuild dev images
./scripts/docker.sh dev logs        # View dev logs
./scripts/docker.sh dev restart     # Restart dev services
./scripts/docker.sh dev ps          # Show dev containers

# Production
./scripts/docker.sh prod up         # Start prod environment
./scripts/docker.sh prod down       # Stop prod environment
./scripts/docker.sh prod build      # Rebuild prod images
./scripts/docker.sh prod logs       # View prod logs

# Execute commands in containers
./scripts/docker.sh dev exec backend bash
./scripts/docker.sh prod exec frontend sh
```

### Running Without Docker (Local Development)

#### Backend (with hot reload):
```bash
cd backend
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e .
uvicorn app.main_api:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (with hot reload):
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000 with hot module replacement.

### Environment Files

The project includes three environment file templates:

- **`.env.dev`** - Development settings (hot-reload, verbose logging)
- **`.env.prod`** - Production template (strong credentials required)
- **`.env.example`** - Legacy example file

**Important**: Never commit `.env.prod.local` or any file with real credentials to version control!

### API Endpoints

#### Authentication
- `POST /api/auth/login` - Login with password
- `POST /api/auth/logout` - Logout (clear session)
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/change-password` - Change password (authenticated)
- `POST /api/auth/first-time-password-change` - Force password change

#### WebSocket
- `WS /ws/terminal?token=<jwt>` - Terminal WebSocket connection

#### Health
- `GET /health` - Health check endpoint

### Environment Variables

#### Backend
```bash
# Internal MongoDB connection
MANAGER_DB_URI=mongodb://user:pass@host:port/database

# JWT authentication
JWT_SECRET=your-secret-key-here

# Timezone
TZ=Europe/Paris
```

#### Frontend
```bash
# API endpoints (configured in nuxt.config.ts)
NUXT_PUBLIC_API_URL=http://localhost:8000
NUXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Security

### Best Practices

1. **Change Default Passwords**: The default admin password (`admin123`) must be changed on first login
2. **Secure JWT Secret**: Use a strong random string for `JWT_SECRET`
3. **Update DB Credentials**: Change `MANAGER_DB_PASSWORD` in production
4. **HTTPS in Production**: Use a reverse proxy (nginx/Caddy) with SSL
5. **Network Isolation**: Internal MongoDB is not exposed to the host
6. **Session Expiration**: JWT tokens expire after 24 hours
7. **Password Requirements**: Minimum 8 characters, hashed with bcrypt

### Production Deployment

#### Using Docker Compose

1. Update `.env` with secure credentials:
   ```bash
   JWT_SECRET=$(openssl rand -base64 32)
   MANAGER_DB_PASSWORD=$(openssl rand -base64 24)
   ```

2. Build and start:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d --build
   ```

3. Set up reverse proxy (nginx example):
   ```nginx
   server {
       listen 443 ssl;
       server_name manager.yourdomain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
       
       location /api/ {
           proxy_pass http://localhost:8000;
       }
       
       location /ws/ {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

#### Using Coolify

1. Set environment variable in Coolify dashboard:
   ```bash
   COOLIFY=true
   JWT_SECRET=<your-secret>
   ```

2. Deploy from Git repository
3. Coolify will automatically handle SSL and domains

## Troubleshooting

### Frontend won't connect to backend

Check CORS settings in `backend/app/main_api.py`. In development, both `localhost:3000` and `127.0.0.1:3000` should be allowed.

### WebSocket connection fails

1. Verify JWT token is being sent in URL: `ws://backend:8000/ws/terminal?token=<jwt>`
2. Check browser console for WebSocket errors
3. Ensure backend health check passes: `curl http://localhost:8000/health`

### Commands not executing

1. Check WebSocket connection status in status bar (should show green dot)
2. Verify backend logs: `docker logs mongodb-manager-backend`
3. Test API directly: `curl http://localhost:8000/health`

### Backend container won't start

1. Check logs: `docker logs mongodb-manager-backend`
2. Verify internal MongoDB is healthy: `docker ps` (should show "healthy")
3. Ensure `.env` file exists with correct credentials

## License

[Your License Here]

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions, please open a GitHub issue.
