# 06 - Version Management

## Overview

MongoDB Manager uses semantic versioning (SemVer) for both frontend and backend components. Both versions are always kept in sync and bumped together using a single script.

## Semantic Versioning

Version format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.0.0 → 1.1.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 1.0.0 → 1.0.1)

## Version Bump Script

All version bumps go through a single script that updates both `frontend/package.json` and `backend/pyproject.toml` atomically:

```bash
# Bug fixes (1.0.0 → 1.0.1)
./scripts/version.sh patch

# New features (1.0.0 → 1.1.0)
./scripts/version.sh minor

# Breaking changes (1.0.0 → 2.0.0)
./scripts/version.sh major
```

The script will:
1. Show the current → new version for both components
2. Ask for confirmation before making any changes
3. Update `frontend/package.json` via `npm version`
4. Update `backend/pyproject.toml` via sed
5. Print the git commands to commit and tag the release

## Current Versions

```bash
# Frontend version
cat frontend/package.json | grep '"version"'

# Backend version
cat backend/pyproject.toml | grep '^version'
```

## Full Release Workflow

```bash
# 1. Bump both versions
./scripts/version.sh minor   # or patch / major

# 2. Commit and tag
git add frontend/package.json backend/pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git tag vX.Y.Z

# 3. Push changes and tag
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

## Git Commit Message Convention

Use conventional commit format:

- `feat:` New feature → minor version bump
- `fix:` Bug fix → patch version bump
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

## Managing Git Tags

```bash
# List all tags
git tag -l

# Delete a local tag (if needed)
git tag -d v1.1.0

# Delete a remote tag (if needed)
git push origin --delete v1.1.0
```

## Related Documentation

- [05 - Deployment Guide](05-deployment.md) - Docker deployment workflows
- [01 - Overview](01-overview.md) - Project structure and tech stack
