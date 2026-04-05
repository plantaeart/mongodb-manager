# 05 - Deployment Guide
**Last Updated:** 2026-04-05

## Restart Dev Stack

The app runs inside Docker Compose. Always restart after code changes.

> **Windows / PowerShell users:** `.sh` scripts must be run with `bash` explicitly — do not run them directly or Windows will ask you to choose an app to open the file.

### Default (most code changes)
```bash
bash ./scripts/docker.sh dev restart --cache
```

### Without cache (big changes only)
```bash
bash ./scripts/docker.sh dev restart --no-cache
```

> Use `--no-cache` only when `package.json` or `pyproject.toml` changed, or after a version bump.

## Related Documentation

- [06 - Version Management](06-version-management.md)
