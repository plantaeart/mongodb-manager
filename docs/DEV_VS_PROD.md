# Development vs Production Environments

MongoDB Manager provides two separate Docker Compose configurations optimized for different use cases.

## Quick Comparison

| Feature | Development (`dev`) | Production (`prod`) |
|---------|-------------------|-------------------|
| **Hot Reload** | ✅ Yes (backend & frontend) | ❌ No (static builds) |
| **Source Mounting** | ✅ Code mounted as volumes | ❌ Code copied into image |
| **Build Time** | Fast (incremental) | Slower (full optimization) |
| **Image Size** | Larger (~800MB) | Smaller (~200MB) |
| **Logging** | Verbose (debug mode) | Rotated (10MB max, 3 files) |
| **Resource Limits** | None | CPU/Memory limits enforced |
| **Container Names** | `*-dev` suffix | `*-prod` suffix |
| **Volume Names** | `*-dev` suffix | `*-prod` suffix |
| **Restart Policy** | `unless-stopped` | `always` |
| **Security** | Relaxed (dev secrets) | Hardened (strong secrets required) |
| **Health Checks** | Basic | Comprehensive |
| **Node Environment** | `development` | `production` |

## When to Use Each

### Use Development Mode When:
- 🔧 Actively developing features
- 🐛 Debugging issues
- 🧪 Testing code changes
- 📚 Learning the codebase
- 🚀 Need fast iteration cycles

### Use Production Mode When:
- 🌐 Deploying to a server (VPS, cloud, etc.)
- 📦 Releasing a stable version
- 🔒 Security is a priority
- 💰 Minimizing resource usage
- 📊 Performance is critical

## File Differences

### Docker Compose Files

**`docker-compose.dev.yml`**:
```yaml
services:
  backend:
    build:
      dockerfile: Dockerfile.dev  # Dev-optimized build
    volumes:
      - ../backend:/app          # Mount source code
    command: uvicorn app.main_api:app --reload  # Hot reload
    environment:
      - NODE_ENV=development
      - PYTHONUNBUFFERED=1
```

**`docker-compose.prod.yml`**:
```yaml
services:
  backend:
    build:
      dockerfile: Dockerfile      # Production multi-stage build
    # No source volumes mounted
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
```

### Dockerfiles

**`Dockerfile.dev`**:
- Single stage build
- Installs ALL dependencies (including dev)
- No source code copied (mounted as volume)
- Runs dev server with hot reload

**`Dockerfile`** (production):
- Multi-stage build (deps → builder → runner)
- Installs only production dependencies
- Source code copied and built
- Runs optimized production build
- Non-root user for security

### Environment Files

**`.env.dev`**:
```bash
MANAGER_DB_USERNAME=dev_admin
MANAGER_DB_PASSWORD=dev123
JWT_SECRET=dev-secret-not-for-production
```

**`.env.prod`** (template):
```bash
MANAGER_DB_USERNAME=manager_admin_prod
MANAGER_DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD_HERE
JWT_SECRET=CHANGE_ME_USE_OPENSSL_RAND_BASE64_64_TO_GENERATE
```

## Data Isolation

Development and production environments use **separate Docker volumes**, so your data never mixes:

### Development Volumes:
- `manager-mongodb-data-dev` - Dev database
- `mongodb-backups-dev` - Dev backups
- `mongodb-manager-data-dev` - Dev config

### Production Volumes:
- `manager-mongodb-data-prod` - Production database
- `mongodb-backups-prod` - Production backups
- `mongodb-manager-data-prod` - Production config

This means you can run both environments simultaneously on different ports without conflicts!

## Port Configuration

Both environments respect the `FRONTEND_PORT` and `BACKEND_PORT` variables.

**Example: Run both environments side-by-side**:

`.env.dev`:
```bash
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

`.env.prod.local`:
```bash
BACKEND_PORT=9000
FRONTEND_PORT=4000
```

Then:
```bash
# Start dev on ports 8000/3000
./scripts/docker.sh dev up

# Start prod on ports 9000/4000 (in another terminal)
./scripts/docker.sh prod up
```

## Migration Path

### From Development to Production

1. **Test locally in prod mode**:
   ```bash
   # Stop dev
   ./scripts/docker.sh dev down
   
   # Start prod with test credentials
   ./scripts/docker.sh prod up
   ```

2. **Verify everything works**:
   - Test authentication flow
   - Test all terminal commands
   - Check logs for errors
   - Verify health checks pass

3. **Update production secrets**:
   ```bash
   # In .env.prod.local
   JWT_SECRET=$(openssl rand -base64 64)
   MANAGER_DB_PASSWORD=$(openssl rand -base64 24)
   ```

4. **Deploy to server**:
   ```bash
   # Copy files to server
   scp -r mongodb-manager-app user@server:/opt/
   
   # SSH to server
   ssh user@server
   cd /opt/mongodb-manager-app
   
   # Start production
   ./scripts/docker.sh prod up
   ```

## Troubleshooting

### "Hot reload not working in dev mode"

Check that source code is properly mounted:
```bash
./scripts/docker.sh dev exec backend ls -la /app
./scripts/docker.sh dev exec frontend ls -la /app
```

You should see your source files, not the container's built files.

### "Production build fails"

Try building without cache:
```bash
./scripts/docker.sh prod build --no-cache
```

### "Port already in use"

Check if another environment is running:
```bash
docker ps | grep mongodb-manager
```

Stop conflicting containers or change ports in `.env.dev` / `.env.prod.local`.

### "Database credentials don't work after switching environments"

Remember: dev and prod use **separate databases**. If you change your password in dev, you'll need to change it again when you switch to prod (or vice versa).

## Best Practices

### Development:
1. ✅ Use `.env.dev` (weak passwords are OK)
2. ✅ Commit code frequently
3. ✅ Test changes in dev before prod
4. ✅ Use verbose logging to debug issues
5. ❌ Don't commit `.env.dev` if you customize it

### Production:
1. ✅ Use strong, unique passwords
2. ✅ Generate JWT secret with `openssl rand -base64 64`
3. ✅ Never commit `.env.prod.local`
4. ✅ Set up reverse proxy with SSL (nginx/Caddy)
5. ✅ Monitor logs regularly
6. ✅ Set up automated backups
7. ✅ Use firewall to restrict access
8. ❌ Don't use default credentials
9. ❌ Don't expose internal MongoDB port

## Summary

- **Development**: Fast iteration, hot reload, verbose logs, relaxed security
- **Production**: Optimized builds, resource limits, log rotation, hardened security

Use development mode for building and testing, then deploy to production mode when you're ready to go live!
