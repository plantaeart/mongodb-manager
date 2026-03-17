#!/bin/bash
# MongoDB Manager - Version Bump Script
# Bumps frontend (package.json) and backend (pyproject.toml) versions in sync.
#
# Usage:
#   ./scripts/version.sh patch   # Bug fixes:      1.0.0 → 1.0.1
#   ./scripts/version.sh minor   # New features:   1.0.0 → 1.1.0
#   ./scripts/version.sh major   # Breaking change: 1.0.0 → 2.0.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Resolve script directory to support calling from any location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_TOML="$ROOT_DIR/backend/pyproject.toml"

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

usage() {
    echo -e "${YELLOW}Usage:${NC} $0 [patch|minor|major]"
    echo ""
    echo "  patch  Bug fixes, backward compatible   (e.g. 1.0.0 → 1.0.1)"
    echo "  minor  New features, backward compatible (e.g. 1.0.0 → 1.1.0)"
    echo "  major  Breaking changes                  (e.g. 1.0.0 → 2.0.0)"
    exit 1
}

# Bump a semver string: bump_semver <version> <patch|minor|major>
bump_semver() {
    local version="$1"
    local bump_type="$2"

    IFS='.' read -r major minor patch <<< "$version"

    case "$bump_type" in
        patch) patch=$((patch + 1)) ;;
        minor) minor=$((minor + 1)); patch=0 ;;
        major) major=$((major + 1)); minor=0; patch=0 ;;
    esac

    echo "${major}.${minor}.${patch}"
}

# --------------------------------------------------------------------------- #
# Validate input
# --------------------------------------------------------------------------- #

BUMP_TYPE="${1:-}"

if [[ "$BUMP_TYPE" != "patch" && "$BUMP_TYPE" != "minor" && "$BUMP_TYPE" != "major" ]]; then
    echo -e "${RED}Error: bump type must be patch, minor, or major.${NC}"
    echo ""
    usage
fi

# --------------------------------------------------------------------------- #
# Read current versions
# --------------------------------------------------------------------------- #

# Frontend: read from package.json
FRONTEND_VERSION=$(node -p "require('$FRONTEND_DIR/package.json').version" 2>/dev/null)
if [[ -z "$FRONTEND_VERSION" ]]; then
    echo -e "${RED}Error: could not read frontend version from $FRONTEND_DIR/package.json${NC}"
    exit 1
fi

# Backend: read from pyproject.toml (match 'version = "x.y.z"')
BACKEND_VERSION=$(grep -E '^version\s*=' "$BACKEND_TOML" | head -1 | sed 's/version\s*=\s*"\(.*\)"/\1/')
if [[ -z "$BACKEND_VERSION" ]]; then
    echo -e "${RED}Error: could not read backend version from $BACKEND_TOML${NC}"
    exit 1
fi

# --------------------------------------------------------------------------- #
# Compute new versions
# --------------------------------------------------------------------------- #

NEW_FRONTEND_VERSION=$(bump_semver "$FRONTEND_VERSION" "$BUMP_TYPE")
NEW_BACKEND_VERSION=$(bump_semver "$BACKEND_VERSION" "$BUMP_TYPE")

# --------------------------------------------------------------------------- #
# Preview & confirm
# --------------------------------------------------------------------------- #

echo ""
echo -e "${CYAN}Version bump: ${BUMP_TYPE}${NC}"
echo ""
echo -e "  Frontend  ${YELLOW}${FRONTEND_VERSION}${NC} → ${GREEN}${NEW_FRONTEND_VERSION}${NC}   (frontend/package.json)"
echo -e "  Backend   ${YELLOW}${BACKEND_VERSION}${NC} → ${GREEN}${NEW_BACKEND_VERSION}${NC}   (backend/pyproject.toml)"
echo ""
read -r -p "Proceed? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

# --------------------------------------------------------------------------- #
# Apply versions
# --------------------------------------------------------------------------- #

# Frontend: use npm version (--no-git-tag-version to skip auto commit/tag)
echo ""
echo -e "${CYAN}Bumping frontend...${NC}"
(cd "$FRONTEND_DIR" && npm version "$BUMP_TYPE" --no-git-tag-version --silent)
echo -e "${GREEN}✓ Frontend updated to ${NEW_FRONTEND_VERSION}${NC}"

# Backend: sed replace in pyproject.toml
echo -e "${CYAN}Bumping backend...${NC}"
sed -i.bak "s/^version\s*=\s*\"${BACKEND_VERSION}\"/version = \"${NEW_BACKEND_VERSION}\"/" "$BACKEND_TOML"
rm -f "${BACKEND_TOML}.bak"
echo -e "${GREEN}✓ Backend updated to ${NEW_BACKEND_VERSION}${NC}"

# --------------------------------------------------------------------------- #
# Done
# --------------------------------------------------------------------------- #

echo ""
echo -e "${GREEN}Both versions bumped to ${NEW_FRONTEND_VERSION} ✓${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  git add frontend/package.json backend/pyproject.toml"
echo "  git commit -m \"chore: bump version to ${NEW_FRONTEND_VERSION}\""
echo "  git tag v${NEW_FRONTEND_VERSION}"
