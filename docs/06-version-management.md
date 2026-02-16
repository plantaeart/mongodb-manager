# 06 - Version Management

## Overview

MongoDB Manager uses semantic versioning (SemVer) for both frontend and backend components. This guide explains how to bump versions and deploy updates.

## Semantic Versioning

Version format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.0.0 → 1.1.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 1.0.0 → 1.0.1)

## Current Versions

Check current versions:

```bash
# Frontend version
cat frontend/package.json | grep version

# Backend version
cat backend/pyproject.toml | grep version
```

## Version Bump Commands

### Frontend (Nuxt/Vue)

The frontend uses npm's built-in version management:

```bash
# Navigate to frontend directory
cd frontend

# Patch version (bug fixes: 1.0.0 → 1.0.1)
npm run version:patch

# Minor version (new features: 1.0.0 → 1.1.0)
npm run version:minor

# Major version (breaking changes: 1.0.0 → 2.0.0)
npm run version:major
```

**What it does:**
- Updates `package.json` version
- Creates git commit with version change
- Creates git tag (e.g., `v1.1.0`)

### Backend (Python/FastAPI)

The backend requires manual version update in `pyproject.toml`:

```bash
# Edit backend version
nano backend/pyproject.toml

# Find and update the version line:
version = "0.2.0"  # Change this number

# Commit the change
git add backend/pyproject.toml
git commit -m "chore: bump backend version to 0.2.0"
git tag backend-v0.2.0
```

## Typical Version Bump Workflow

### For New Features

```bash
# 1. Navigate to project root
cd mongodb-manager-app

# 2. Bump frontend version (minor)
cd frontend
npm run version:minor
cd ..

# 3. Bump backend version (manual)
# Edit backend/pyproject.toml: version = "0.2.0"
nano backend/pyproject.toml

# 4. Commit backend version
git add backend/pyproject.toml
git commit -m "chore: bump backend version to 0.2.0"

# 5. Tag backend version
git tag backend-v0.2.0

# 6. Push changes and tags
git push origin main
git push origin --tags
```

### For Bug Fixes

```bash
# 1. Bump frontend version (patch)
cd frontend
npm run version:patch
cd ..

# 2. Bump backend version (manual)
# Edit backend/pyproject.toml: version = "0.1.1"
nano backend/pyproject.toml

# 3. Commit and tag
git add backend/pyproject.toml
git commit -m "fix: bump backend version to 0.1.1"
git tag backend-v0.1.1

# 4. Push changes
git push origin main
git push origin --tags
```

## Restart Dev Stack After Version Bump

After bumping versions, restart the development environment to ensure changes are reflected:

```bash
# Stop current dev environment
./scripts/docker.sh dev down

# Start with fresh build
./scripts/docker.sh dev up -d --build

# View logs to verify startup
./scripts/docker.sh dev logs
```

## Production Deployment After Version Bump

```bash
# 1. Pull latest changes
git pull origin main

# 2. Stop production environment
./scripts/docker.sh prod down

# 3. Rebuild and start
./scripts/docker.sh prod up -d --build

# 4. Verify deployment
./scripts/docker.sh prod logs --tail 50
```

## Version History Best Practices

### Git Commit Messages

Use conventional commit format:

- `feat:` New feature (minor version bump)
- `fix:` Bug fix (patch version bump)
- `chore:` Maintenance, version bumps
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test changes

**Examples:**
```bash
git commit -m "feat: add interactive connection removal with table display"
git commit -m "fix: resolve WebSocket reconnection issue"
git commit -m "chore: bump version to 1.1.0"
```

### Git Tags

Tags should match the version format:

- Frontend: `v1.1.0` (npm creates automatically)
- Backend: `backend-v0.2.0` (manual)

**List all tags:**
```bash
git tag -l
```

**Delete tag (if needed):**
```bash
# Delete local tag
git tag -d v1.1.0

# Delete remote tag
git push origin --delete v1.1.0
```

## Version Synchronization

While frontend and backend can have different versions, keep major versions aligned for clarity:

| Component | Version | Notes |
|-----------|---------|-------|
| Frontend  | 1.1.0   | Nuxt/Vue application |
| Backend   | 0.2.0   | FastAPI/Python API |

**Recommendation**: When making breaking changes, bump both major versions together.

## Changelog Maintenance

Keep a `CHANGELOG.md` file (optional but recommended):

```bash
# Create changelog
cat > CHANGELOG.md << 'EOF'
# Changelog

## [1.1.0] - 2024-02-16

### Added
- Interactive connection removal with table display
- Double confirmation for safe deletion
- Password masking in connection URIs

### Fixed
- Connection removal error handling

## [1.0.0] - 2024-01-20

### Added
- Initial release
- MongoDB connection management
- Backup/restore operations
- WebSocket terminal interface
EOF
```

## Quick Reference

```bash
# Frontend version bump (new feature)
cd frontend && npm run version:minor && cd ..

# Backend version bump (manual)
# 1. Edit backend/pyproject.toml
# 2. git commit -m "chore: bump backend to X.Y.Z"
# 3. git tag backend-vX.Y.Z

# Restart dev stack
./scripts/docker.sh dev down && ./scripts/docker.sh dev up -d --build

# Deploy to production
git push origin main --tags
./scripts/docker.sh prod down && ./scripts/docker.sh prod up -d --build
```

## Related Documentation

- [05 - Deployment Guide](05-deployment.md) - Docker deployment workflows
- [01 - Overview](01-overview.md) - Project structure and tech stack
