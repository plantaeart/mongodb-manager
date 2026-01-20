# MongoDB Manager - Quick Start Guide

## 🚀 5-Minute Setup

### For Development (Hot Reload)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd mongodb-manager-app

# 2. Start development environment
./scripts/docker.sh dev up

# 3. Open your browser
# http://localhost:3000

# 4. Login
# Username: admin
# Password: admin123
# (You'll be forced to change it)

# Done! 🎉
```

**Features**:
- ✅ Hot reload on code changes
- ✅ Source code mounted as volumes
- ✅ Verbose logging for debugging

### For Production (Optimized)

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd mongodb-manager-app

# 2. Configure production secrets
cp .env.prod .env.prod.local

# Edit .env.prod.local:
# - Set strong MANAGER_DB_PASSWORD
# - Generate JWT_SECRET: openssl rand -base64 64
# - Update ports if needed

# 3. Start production environment
./scripts/docker.sh prod up

# 4. Open your browser
# http://localhost:3000

# 5. Login and change default password
# Username: admin
# Password: admin123

# Done! 🎉
```

**Features**:
- ✅ Optimized Docker builds
- ✅ Resource limits (CPU/memory)
- ✅ Log rotation
- ✅ Health checks

## 📋 Available Commands

### Using Helper Scripts

```bash
# Development
./scripts/docker.sh dev up          # Start
./scripts/docker.sh dev down        # Stop
./scripts/docker.sh dev build       # Rebuild
./scripts/docker.sh dev logs        # View logs
./scripts/docker.sh dev restart     # Restart
./scripts/docker.sh dev ps          # Status

# Production
./scripts/docker.sh prod up         # Start
./scripts/docker.sh prod down       # Stop
./scripts/docker.sh prod build      # Rebuild
./scripts/docker.sh prod logs       # View logs

# Execute commands in containers
./scripts/docker.sh dev exec backend bash
./scripts/docker.sh prod exec frontend sh
```

### Manual Docker Compose

```bash
# Development
docker-compose -f docker/docker-compose.dev.yml --env-file .env.dev up -d
docker-compose -f docker/docker-compose.dev.yml down

# Production
docker-compose -f docker/docker-compose.prod.yml --env-file .env.prod.local up -d
docker-compose -f docker/docker-compose.prod.yml down
```

## 🌐 Access Points

| Service | Development | Production |
|---------|------------|-----------|
| Frontend | http://localhost:3000 | http://localhost:3000 |
| Backend API | http://localhost:8000 | http://localhost:8000 |
| API Docs | http://localhost:8000/docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health | http://localhost:8000/health |

*(Ports can be customized via `.env.dev` or `.env.prod.local`)*

## 🔐 Default Credentials

**First Login**:
- Username: `admin`
- Password: `admin123`

**⚠️ IMPORTANT**: You'll be forced to change the password on first login!

## 📁 Project Structure

```
mongodb-manager-app/
├── backend/               # FastAPI backend
├── frontend/              # Nuxt frontend
├── docker/
│   ├── docker-compose.dev.yml   # Development config
│   ├── docker-compose.prod.yml  # Production config
│   └── docker-compose.yml       # Default (→ prod)
├── scripts/
│   ├── docker.sh          # Linux/Mac helper
│   └── docker.bat         # Windows helper
├── docs/
│   └── DEV_VS_PROD.md     # Detailed comparison
├── .env.dev               # Dev environment
├── .env.prod              # Prod template
└── README.md              # Full documentation
```

## 🔧 Terminal Commands (in Web UI)

Once logged in, you can use these commands in the terminal:

### Connection Management
```bash
connect list              # List all connections
connect add               # Add new connection (interactive)
connect remove <name>     # Remove a connection
connect test <name>       # Test a connection
```

### Backup Operations
```bash
backup create <name>      # Create backup
backup list               # List all backups
backup restore <file>     # Restore from backup
backup delete <file>      # Delete backup file
```

### Other Commands
```bash
help                      # Show all commands
clear                     # Clear terminal
auth change-password      # Change your password
auth logout               # Logout
```

## 🆘 Troubleshooting

### Services won't start

```bash
# Check what's running
docker ps

# View logs
./scripts/docker.sh dev logs

# Stop and restart
./scripts/docker.sh dev down
./scripts/docker.sh dev up
```

### Port already in use

Edit `.env.dev` or `.env.prod.local`:
```bash
BACKEND_PORT=9000
FRONTEND_PORT=4000
```

Then restart:
```bash
./scripts/docker.sh dev down
./scripts/docker.sh dev up
```

### Hot reload not working (dev mode)

Check if source code is mounted:
```bash
./scripts/docker.sh dev exec backend ls -la /app
```

If empty, rebuild:
```bash
./scripts/docker.sh dev down
./scripts/docker.sh dev build
./scripts/docker.sh dev up
```

### Can't connect to MongoDB

1. Verify internal MongoDB is healthy:
   ```bash
   docker ps | grep mongodb
   ```
   Should show "healthy" status

2. Check backend logs:
   ```bash
   ./scripts/docker.sh dev logs backend
   ```

3. Verify environment variables:
   ```bash
   cat .env.dev  # or .env.prod.local
   ```

## 📚 Learn More

- **Full Documentation**: See [README.md](../README.md)
- **Dev vs Prod Guide**: See [docs/DEV_VS_PROD.md](DEV_VS_PROD.md)
- **API Documentation**: http://localhost:8000/docs (when running)

## 🎯 Next Steps

1. **Add MongoDB Connections**: Use `connect add` command
2. **Create Backups**: Use `backup create <name>` command
3. **Explore Features**: Check the visual panel for quick actions
4. **Customize**: Edit environment files for ports and settings
5. **Deploy**: Use production mode for real deployments

## 💡 Pro Tips

- Use `Tab` for command autocomplete
- Use `↑/↓` arrows for command history
- Click "Show Panel" for quick actions and favorites
- Save frequently used commands as favorites
- Change your password regularly via `auth change-password`

---

**Need help?** Open an issue on GitHub or check the [README.md](../README.md) for detailed documentation.
