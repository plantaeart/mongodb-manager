# 05 - Deployment Guide

## Restart Dev Stack

The app runs inside Docker Compose. Always restart after code changes.

### Default (most code changes)
```bash
./scripts/docker.sh dev restart --cache
```

### Without cache (big changes only)
```bash
./scripts/docker.sh dev restart --no-cache
```

> Use `--no-cache` only when `package.json` or `requirements.txt` changed, or after a version bump.

## Related Documentation

- [06 - Version Management](06-version-management.md)
