# 05 - Deployment Guide

## Restart Dev Stack

### With cache (fast, use after most code changes)
```bash
./scripts/docker.sh dev restart --cache
```

### Without cache (clean rebuild, use after dependency changes)
```bash
./scripts/docker.sh dev restart --no-cache
```

> Use `--no-cache` when `package.json` or `requirements.txt` changed, or after a version bump.

## Related Documentation

- [06 - Version Management](06-version-management.md)
