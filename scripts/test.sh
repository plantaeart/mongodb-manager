#!/usr/bin/env bash
# MongoDB Manager — Unified Test Runner
#
# Runs tests inside dedicated test containers (no dev stack required).
#
# Usage:
#   ./scripts/test.sh                  # Run both backend and frontend tests
#   ./scripts/test.sh --backend        # Run backend tests only
#   ./scripts/test.sh --frontend       # Run frontend tests only
#   ./scripts/test.sh --coverage       # Run both with coverage
#   ./scripts/test.sh --backend --coverage
#   ./scripts/test.sh --frontend --coverage
#   ./scripts/test.sh --build          # Force rebuild of test images before running

set -e

# ── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Resolve paths ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker/docker-compose.test.yml"

# ── Parse flags ─────────────────────────────────────────────────────────────
RUN_BACKEND=false
RUN_FRONTEND=false
WITH_COVERAGE=false
FORCE_BUILD=false

for arg in "$@"; do
  case "$arg" in
    --backend)  RUN_BACKEND=true ;;
    --frontend) RUN_FRONTEND=true ;;
    --coverage) WITH_COVERAGE=true ;;
    --build)    FORCE_BUILD=true ;;
    *)
      echo -e "${RED}Unknown argument: $arg${NC}"
      echo "Usage: $0 [--backend] [--frontend] [--coverage] [--build]"
      exit 1
      ;;
  esac
done

# Default: run both if neither flag was given
if ! $RUN_BACKEND && ! $RUN_FRONTEND; then
  RUN_BACKEND=true
  RUN_FRONTEND=true
fi

# ── Build flag ───────────────────────────────────────────────────────────────
BUILD_ARG=""
if $FORCE_BUILD; then
  BUILD_ARG="--build"
fi

# ── Helpers ─────────────────────────────────────────────────────────────────
BACKEND_FAILED=false
FRONTEND_FAILED=false

run_backend() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  🐍 Backend tests (pytest)${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  if $WITH_COVERAGE; then
    PYTEST_ARGS="pytest --cov=app --cov-report=term-missing"
  else
    PYTEST_ARGS="pytest"
  fi

  if docker compose -f "$COMPOSE_FILE" run --rm $BUILD_ARG backend-test $PYTEST_ARGS; then
    echo -e "${GREEN}  ✓ Backend tests passed${NC}"
  else
    echo -e "${RED}  ✗ Backend tests failed${NC}"
    BACKEND_FAILED=true
  fi
}

run_frontend() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  🟦 Frontend tests (vitest)${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  if $WITH_COVERAGE; then
    NPM_CMD="npm run test:coverage"
  else
    NPM_CMD="npm test"
  fi

  if docker compose -f "$COMPOSE_FILE" run --rm $BUILD_ARG frontend-test $NPM_CMD; then
    echo -e "${GREEN}  ✓ Frontend tests passed${NC}"
  else
    echo -e "${RED}  ✗ Frontend tests failed${NC}"
    FRONTEND_FAILED=true
  fi
}

# ── Run ──────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}MongoDB Manager — Test Runner${NC}"
echo -e "${CYAN}  Compose file: docker/docker-compose.test.yml${NC}"
echo -e "${CYAN}  (Dev stack not required)${NC}"

$RUN_BACKEND  && run_backend
$RUN_FRONTEND && run_frontend

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if $RUN_BACKEND; then
  if $BACKEND_FAILED; then
    echo -e "  Backend:  ${RED}FAILED${NC}"
  else
    echo -e "  Backend:  ${GREEN}PASSED${NC}"
  fi
fi

if $RUN_FRONTEND; then
  if $FRONTEND_FAILED; then
    echo -e "  Frontend: ${RED}FAILED${NC}"
  else
    echo -e "  Frontend: ${GREEN}PASSED${NC}"
  fi
fi

echo ""

if $BACKEND_FAILED || $FRONTEND_FAILED; then
  exit 1
fi

exit 0
