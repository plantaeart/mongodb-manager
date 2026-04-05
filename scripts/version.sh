#!/bin/bash
# MongoDB Manager - Version Bump Script
# Bumps frontend (package.json) and backend (pyproject.toml) versions in sync.
#
# Usage:
#   ./scripts/version.sh patch   # Bug fixes:       1.0.0 → 1.0.1
#   ./scripts/version.sh minor   # New features:    1.0.0 → 1.1.0
#   ./scripts/version.sh major   # Breaking change: 1.0.0 → 2.0.0

set -e

BUMP_TYPE="${1:-}"

if [[ "$BUMP_TYPE" != "patch" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "major" ]]; then
    echo "Usage: $0 [patch|minor|major]"
    exit 1
fi

# Resolve paths relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"
BACKEND_TOML="$SCRIPT_DIR/../backend/pyproject.toml"

# --------------------------------------------------------------------------- #
# Frontend — npm handles version bumping
# --------------------------------------------------------------------------- #

echo "Bumping frontend ($BUMP_TYPE)..."
(cd "$FRONTEND_DIR" && npm version "$BUMP_TYPE" --no-git-tag-version)

NEW_VERSION=$(grep '"version"' "$FRONTEND_DIR/package.json" | sed 's/.*"version": "\([^"]*\)".*/\1/')
echo "Frontend → $NEW_VERSION"

# --------------------------------------------------------------------------- #
# Backend — replace version line in pyproject.toml
# --------------------------------------------------------------------------- #

echo "Bumping backend..."
sed -i'' "s/^version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$NEW_VERSION\"/" "$BACKEND_TOML"
echo "Backend → $NEW_VERSION"

# --------------------------------------------------------------------------- #
# Backend — regenerate uv.lock
# uv is not installed on the host; run it in a throwaway Docker container
# --------------------------------------------------------------------------- #

BACKEND_DIR="$SCRIPT_DIR/../backend"

echo "Regenerating uv.lock..."
docker run --rm \
  -v "$(cd "$BACKEND_DIR" && pwd):/app" \
  -w /app \
  python:3.14-rc-slim \
  sh -c "pip install --quiet uv && uv lock"
echo "uv.lock → updated"

# --------------------------------------------------------------------------- #
# Done
# --------------------------------------------------------------------------- #

echo ""
echo "All versions bumped to $NEW_VERSION"
echo ""
echo "Next steps:"
echo "  git add frontend/package.json backend/pyproject.toml backend/uv.lock"
echo "  git commit -m \"chore: bump version to $NEW_VERSION\""
echo "  git tag v$NEW_VERSION"
