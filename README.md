# MongoDB Manager - Web UI

A web-based tool for managing MongoDB backups and restores with a terminal-style interface. FastAPI backend, Nuxt frontend, Gruvbox theme. Everything runs in Docker.

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
- **Port**: `BACKEND_PORT` on the host (default 9000)
- **API**: RESTful endpoints for authentication and operations
- **WebSocket**: Real-time command execution and output streaming
- **Database**: Internal MongoDB for sessions and user data
- **CLI Core**: Wrapped existing CLI logic for command execution

### Frontend (Nuxt 4)
- **Port**: `FRONTEND_PORT` on the host (default 4000)
- **Framework**: Nuxt 4 + Vue 3, with Nuxt UI
- **UI**: Terminal-style interface
- **Theme**: Gruvbox color palette
- **State**: Pinia store + composables for auth, WebSocket, and terminal

### Internal MongoDB (Session Storage)
- **Purpose**: Stores user authentication, sessions, and connection definitions
- **Database**: `MONGODB_MANAGER_DB` (`NUXT_MONGODB_DATABASE`)
- **Collections**: `users`, `sessions`, connections
- **Never exposed** to the host — reachable only inside the Docker network
- **Features**: automatic session expiration via TTL index, bcrypt password hashing

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
│  │  (Nuxt 4)   │   │  (FastAPI)   │   │ MongoDB  ││
│  │:FRONTEND_PORT│   │:BACKEND_PORT │   │ Sessions ││
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

## Installation

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (`docker compose`)
- At least 2 GB free disk space (images + backups)
- The ports you plan to use free on your machine: `FRONTEND_PORT` (4000) and `BACKEND_PORT` (9000) by default (see [Ports](#ports))

### 1. Get the code

```bash
git clone https://github.com/plantaeart/mongodb-manager.git
cd mongodb-manager
```

### 2. Create your environment file

Everything is configured in a single env file. `.env.example` documents every
variable inline — read the comments, then copy it:

```bash
cp .env.example .env.prod
```

**Before starting, change these two lines in `.env.prod`:**

```bash
# The password you will type in the web UI login form
NUXT_ADMIN_PASSWORD=choose-a-strong-password

# Signs session tokens. Generate a random one:
#   openssl rand -base64 64
NUXT_JWT_SECRET=paste-your-random-secret-here
```

That is the minimum for a working install. Everything else in `.env.example` has
a working default, including the ports.

### 3. Start the app

```bash
./scripts/docker.sh prod up
```

The first run builds the images (a few minutes). Subsequent starts are fast.

```bash
./scripts/docker.sh prod ps      # check status
./scripts/docker.sh prod logs   # follow logs
```

### 4. Log in

Open **http://localhost:`${FRONTEND_PORT}`** and log in with:

- **Username**: `admin` (always `admin`, not configurable)
- **Password**: the `NUXT_ADMIN_PASSWORD` you set in step 2

With `NODE_ENV=production` you are forced to change the password immediately.
The new password is stored hashed in the internal MongoDB.

### 5. Add a MongoDB connection

In the web UI, run `connect add` and enter the URI of the MongoDB instance you
want to back up, e.g. `mongodb://user:password@vps-host:27017/mydb`. Then
`backup create <connection-name>`.

### Ports

Both ports are configured in section 4 of your env file:

| Variable | Default | What it is |
| --- | --- | --- |
| `FRONTEND_PORT` | `4000` | the web UI — this is the one you open |
| `BACKEND_PORT` | `9000` | the API, also serves the WebSocket terminal |

Change either one and everything else follows automatically: `CORS_ORIGINS`
reuses `FRONTEND_PORT`, and `NUXT_PUBLIC_API_URL` / `NUXT_PUBLIC_WS_URL` reuse
`BACKEND_PORT`. There is nothing to keep in sync by hand.

Throughout this README, `${FRONTEND_PORT}` and `${BACKEND_PORT}` mean "the
value you set in your env file", not a literal string to copy. With the
defaults shown above, that is `http://localhost:4000`.

Remember that port changes need a **recreate**, not a restart (see
[troubleshooting](#you-forgot-the-admin-password)).

API docs (FastAPI): **http://localhost:`${BACKEND_PORT}`/docs**

### Updating

```bash
git pull
./scripts/docker.sh prod restart --cache   # rebuild and restart
```

Your data lives in Docker volumes and is untouched by updates. Your env file is
gitignored, so `git pull` never overwrites it.

### Uninstall

```bash
./scripts/docker.sh prod down            # stop, keep data
./scripts/docker.sh prod down --volumes  # stop and delete all data
```

### Development mode

Same setup, but with hot-reload and source code mounted as volumes:

```bash
cp .env.example .env.dev
./scripts/docker.sh dev up
```

Useful while you are working on the code:

```bash
./scripts/docker.sh dev logs             # follow logs
./scripts/docker.sh dev exec backend bash # shell inside the API container
./scripts/docker.sh dev reset             # wipe data and start fresh
```

### Without Docker

<details>
<summary>Run backend and frontend directly (for development only)</summary>

Backend:

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e .
uvicorn app.main_api:app --reload --host 0.0.0.0 --port ${BACKEND_PORT:-9000}
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `NUXT_PUBLIC_API_URL` / `NUXT_PUBLIC_WS_URL` (see
`nuxt.config.ts`) and needs a MongoDB reachable at `NUXT_MONGODB_HOST`. Start
one with `docker compose -f docker/docker-compose.dev.yml --env-file .env.dev up -d manager-mongodb`,
or point `MANAGER_DB_URI` at an external MongoDB.

</details>

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
mongodb-manager/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes (auth, forms)
│   │   ├── core/             # Auth manager, database client
│   │   ├── models/           # Pydantic models
│   │   ├── middleware/       # JWT authentication
│   │   ├── websocket/        # WebSocket terminal
│   │   ├── stores/           # CLI command handlers
│   │   └── main_api.py       # FastAPI app entry point
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/
│   ├── app/                  # Nuxt 4 srcDir
│   │   ├── app.vue           # Root component (mounts UApp → toasts)
│   │   ├── components/       # Vue components (Auth, Terminal, Forms, Base)
│   │   ├── composables/      # useWebSocket, useTerminal, useVersion, ...
│   │   ├── stores/           # Pinia auth store
│   │   ├── enums/            # Shared enums (Toast, Terminal, WebSocket)
│   │   ├── types/            # TypeScript types
│   │   ├── pages/            # Nuxt pages
│   │   └── assets/css/       # Tailwind + Gruvbox theme
│   ├── Dockerfile
│   ├── nuxt.config.ts
│   └── package.json
│
├── docker/
│   ├── docker-compose.dev.yml   # Development configuration
│   ├── docker-compose.prod.yml  # Production configuration
│   └── docker-compose.yml       # Root copy of the production stack
│
├── scripts/
│   └── docker.sh                # Docker helper script
│
├── .env.example                 # Annotated template — copy to .env.dev / .env.prod
├── .env.dev                     # Development environment (gitignored)
├── .env.prod                    # Production environment (gitignored)
└── README.md
```

### Docker Helper Script

`./scripts/docker.sh <dev|prod> <action>` — the script reads the env file
matching the environment name (`.env.dev` / `.env.prod`):

```bash
# Actions (same for dev and prod)
./scripts/docker.sh prod up              # Start
./scripts/docker.sh prod ps              # Show status
./scripts/docker.sh prod logs            # Follow logs
./scripts/docker.sh prod restart         # Restart
./scripts/docker.sh prod restart --cache # Restart, rebuild with cache
./scripts/docker.sh prod restart --no-cache  # Restart, clean rebuild
./scripts/docker.sh prod build           # Build images
./scripts/docker.sh prod down            # Stop (keep data)
./scripts/docker.sh prod down --volumes  # Stop and delete all data
./scripts/docker.sh prod reset           # Wipe data and start fresh

# Shell inside a container
./scripts/docker.sh prod exec backend bash
./scripts/docker.sh prod exec frontend sh
```

Prefer plain Docker? The equivalent of `prod up`:

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d
```

### Environment Files

| File | Tracked in git | Purpose |
| --- | --- | --- |
| `.env.example` | yes | Annotated template, copy it to start |
| `.env.dev` | no | Development environment |
| `.env.prod` | no | Production environment |

Only `.env.example` is committed. Your env files are gitignored, so updates
never overwrite them. Every variable is documented inline in `.env.example`.

**Never commit a file containing real credentials.**

### Environment Variables

**Passwords you set:**

| Variable | What it is |
| --- | --- |
| `NUXT_ADMIN_PASSWORD` | The web UI login password. Username is always `admin`. |
| `NUXT_JWT_SECRET` | Secret used to sign session tokens. `openssl rand -base64 64` |

**Ports:**

| Variable | Default | What it is |
| --- | --- | --- |
| `BACKEND_PORT` | `9000` | API + WebSocket, on the host |
| `FRONTEND_PORT` | `4000` | Web UI, on the host |

**Internal MongoDB** (the app's own database, not your backup targets):
`NUXT_MONGODB_USERNAME`, `NUXT_MONGODB_PASSWORD`, `NUXT_MONGODB_HOST`,
`NUXT_MONGODB_PORT`, `NUXT_MONGODB_DATABASE`.

**Browser-side URLs** (baked into the frontend bundle at build time):
`NUXT_PUBLIC_API_URL`, `NUXT_PUBLIC_WS_URL`.

**Other**: `NODE_ENV`, `TZ`, `CORS_ORIGINS`, `BACKUP_BASE_DIR`,
`MANAGER_DB_URI`, `COOLIFY`.

See `.env.example` for what each one does.

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

## Security

### Best Practices

1. **Set a strong `NUXT_ADMIN_PASSWORD`**: this is the web UI login password. You are forced to change it on first login in production.
2. **Set a random `NUXT_JWT_SECRET`**: `openssl rand -base64 64`
3. **HTTPS in production**: put a reverse proxy (nginx/Caddy) in front, and set `NUXT_PUBLIC_API_URL` / `NUXT_PUBLIC_WS_URL` to `https://` / `wss://` before building.
4. **Network isolation**: the internal MongoDB is never published to the host, only reachable inside the Docker network.
5. **Session expiration**: JWT tokens expire automatically, and refresh before expiry.
6. **Password storage**: hashed with bcrypt in the internal MongoDB, never in the env file.

### Behind a reverse proxy

The frontend is served on `FRONTEND_PORT` and the API on `BACKEND_PORT`. Point
your proxy at both, and use `wss://` for the WebSocket path.

nginx does not read your `.env` file, so replace the ports below with the
values you set (`4000` for the web UI, `9000` for the API, unless you changed
them):

```nginx
server {
    listen 443 ssl;
    server_name manager.yourdomain.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Web UI — replace 4000 with your FRONTEND_PORT
    location / {
        proxy_pass http://localhost:4000;
        proxy_set_header Host $host;
    }

    # API — replace 9000 with your BACKEND_PORT
    location /api/ {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
    }

    # WebSocket terminal — replace 9000 with your BACKEND_PORT
    location /ws/ {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Then update the browser-facing URLs and rebuild, because they are baked into the
bundle at build time:

```bash
# in .env.prod
NUXT_PUBLIC_API_URL=https://manager.yourdomain.com
NUXT_PUBLIC_WS_URL=wss://manager.yourdomain.com
CORS_ORIGINS=https://manager.yourdomain.com
NODE_ENV=production
```

```bash
./scripts/docker.sh prod restart --no-cache
```

### Using Coolify

Deploy from the Git repository, then set the same variables in the Coolify
dashboard (`NUXT_ADMIN_PASSWORD`, `NUXT_JWT_SECRET`, `COOLIFY=true`, ports,
and the `NUXT_PUBLIC_*` URLs for your domain). Coolify handles SSL and domains.

## Troubleshooting

### Login fails, or the browser console shows a CORS error

`CORS_ORIGINS` must list the origin you actually open. It follows
`FRONTEND_PORT` automatically, so if you changed the port *above* it, it is
already correct. If you hardcoded a value, fix it:

```bash
# in .env.prod (or .env.dev)
CORS_ORIGINS=http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}
```

Then recreate the containers so they pick it up:

```bash
./scripts/docker.sh prod down && ./scripts/docker.sh prod up
```

### The WebSocket connection fails

1. Check the browser console for WebSocket errors.
2. Make sure `NUXT_PUBLIC_WS_URL` reuses `BACKEND_PORT` in your env file. It is baked in at build time in production, so rebuild after changing it: `./scripts/docker.sh prod restart --no-cache`.
3. Test the API directly: `curl http://localhost:${BACKEND_PORT}/health`

### Commands don't execute

1. Check the WebSocket status in the status bar (should show a green dot).
2. Follow the logs: `./scripts/docker.sh prod logs`
3. Test the API: `curl http://localhost:${BACKEND_PORT}/health`

### A container won't start

1. Follow the logs: `./scripts/docker.sh prod logs`
2. Check the internal MongoDB is healthy: `docker ps` (should show `healthy`)
3. Make sure your env file exists and is named `.env.prod` (or `.env.dev`)

### You forgot the admin password

Edit `NUXT_ADMIN_PASSWORD` in your env file, then **recreate** the containers
(`restart` is not enough — it reuses the existing containers, so they keep the
environment they were created with):

```bash
./scripts/docker.sh prod down && ./scripts/docker.sh prod up
```

Or, without the helper script:

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d
```

The new password applies on the next login, and also re-triggers the forced
password change.

Same rule for any other variable: `NUXT_PUBLIC_API_URL`, `NUXT_PUBLIC_WS_URL`,
`CORS_ORIGINS` and the ports only change after a recreate.

## License

[Your License Here]

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions, please open a GitHub issue.
