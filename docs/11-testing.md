# Testing Guide
**Last Updated:** 2026-04-05

## Overview

MongoDB Manager uses a two-track testing strategy: **pure logic unit tests** on both sides of the stack, and **HTTP integration tests** on the backend — all without needing a real MongoDB connection.

Tests run inside **dedicated test containers** (`docker-compose.test.yml`) via a unified shell script — the dev stack does not need to be running.

---

## Running Tests

```bash
# Run everything (backend + frontend)
./scripts/test.sh

# Backend only
./scripts/test.sh --backend

# Frontend only
./scripts/test.sh --frontend

# With coverage reports
./scripts/test.sh --coverage
./scripts/test.sh --backend --coverage
./scripts/test.sh --frontend --coverage

# Force rebuild of test images (after dependency changes)
./scripts/test.sh --build
```

> **No dev stack required.** `test.sh` uses `docker compose run --rm` against `docker/docker-compose.test.yml` — the test containers build and start on their own.

---

## Backend

### Stack

| Tool | Purpose |
|------|---------|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reports |
| `httpx` | HTTP client for FastAPI TestClient |
| `freezegun` | Time freezing for expiry tests |

### Configuration

`backend/pyproject.toml` — `[tool.pytest.ini_options]`:
```toml
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"
```

### File Structure

```
backend/tests/
├── conftest.py                  # Shared fixtures (client, auth_token, auth_headers)
├── utils/
│   ├── test_uri_builder.py      # build_mongodb_uri / build_mongodb_uri_masked
│   └── test_timezone.py         # format_timestamp, add_hours, parse_iso_datetime, is_expired
├── middleware/
│   └── test_auth.py             # create_access_token, verify_token, endpoint auth
└── routers/
    ├── test_commands.py         # /api/commands/execute integration tests
    └── test_transfer.py         # /api/transfer/* integration tests
```

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture(scope="session")
def client():
    # FastAPI TestClient with mocked init_database / close_database
    # No real MongoDB needed

@pytest.fixture
def auth_token():
    # Valid JWT for username "admin"

@pytest.fixture
def auth_headers(auth_token):
    # {"Authorization": "Bearer <token>"}
```

> `init_database` and `close_database` are patched at the session level so the FastAPI lifespan handler never attempts a real DB connection.

### What's Tested

**`test_uri_builder.py`** — 18 tests
- No-auth URI format (`mongodb://host:port`)
- Auth with `authSource` appended
- Special characters URL-encoded (`@` → `%40`, `:` → `%3A`)
- Database path appended
- Custom options dict in query string
- `ValueError` on empty host, port out of range (0, 65536), non-int port, username/password mismatch
- Masked URI shows `***`, never leaks real password

**`test_timezone.py`** — 13 tests
- `format_timestamp`: aware and naive datetimes, custom format strings
- `add_hours`: positive, zero, negative, day-crossing
- `parse_iso_datetime`: valid ISO strings (UTC, offset, naive), invalid input raises `ValueError`
- `is_expired`: past/future/boundary, injectable `current_time` parameter

**`test_auth.py`** — 11 tests
- `create_access_token` returns a 3-part JWT string
- Token round-trips through `verify_token` correctly
- `exp` claim is ~24 hours from now
- Tampered / expired / missing-claim tokens all raise `HTTPException(401)`
- Endpoint returns 403 without token, reaches handler with valid token

**`test_commands.py`** — 13 integration tests
- Health check (`/health`) needs no auth
- Execute endpoint returns 403 without token, 403 with invalid token
- `connect list` returns 200 + `{success, output, exit_code}` shape
- `connect remove []` → `success: false`, `"No connections selected"`
- `backup folder delete` without confirmation → `success: false`, error mentions "confirm"
- Missing required fields (`connection_name`, `folder_path`) return clear error messages
- `connect test []`, `connect update` (no connection), `backup create` (no connection), `backup restore` (no confirmation) all return `success: false`

**`test_transfer.py`** — 31 integration tests

All manager classes are mocked — no real filesystem or MongoDB access.

| Class | Tests | Coverage |
|-------|-------|---------|
| `TestBackupExportOptions` | 3 | Returns backup list, empty list, 401 without auth |
| `TestBackupImportOptions` | 2 | Deduplicates/sorts folders, 401 without auth |
| `TestBackupExport` | 5 | Valid ZIP stream, bad selector → 400, not found → 404, disk error → 500, 401 |
| `TestBackupImport` | 7 | Success, unregistered folder → 400, bad ZIP → 400, already exists → 400, overwrite flag forwarded, disk error → 500, 401 |
| `TestConnectExport` | 3 | JSON stream with passwords stripped, exception → 500, 401 |
| `TestConnectImport` | 8 | Imported, overwritten, skipped counts; empty array short-circuit; bad JSON → 400; missing key → 400; flags forwarded; errors in result; crash → 500 |

---

## Frontend

### Stack

| Tool | Purpose |
|------|---------|
| `vitest` | Test runner |
| `@vue/test-utils` | Vue component utilities |
| `jsdom` | Browser environment simulation |
| `@vitest/coverage-v8` | Coverage reports |

### Configuration

`frontend/vitest.config.ts`:
```ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
  },
  resolve: {
    alias: { '~': resolve(__dirname, 'app') },
  },
})
```

`~` resolves to `frontend/app/` — matching the Nuxt alias.

### npm Scripts

```bash
npm test              # vitest run (single pass)
npm run test:watch    # vitest (watch mode)
npm run test:coverage # vitest run --coverage
```

### File Structure

```
frontend/tests/
├── utils/
│   ├── token.test.ts        # isTokenExpired, getTokenExpirationTime, getTimeUntilExpiration
│   └── formHelpers.test.ts  # getFieldComponentName, decodeConnectionData
├── types/
│   └── stepper.test.ts      # createStep, getAllStepData, isStepValid, canProceedFromStep
└── enums/
    ├── terminal.test.ts              # TerminalCommand enum values (incl. CONNECT_EXPORT/IMPORT)
    └── terminal.backupOperations.test.ts  # Backup command enum values (incl. BACKUP_EXPORT/IMPORT)
```

### JWT Test Helper

All token tests use a `makeJwt()` helper that builds a structurally valid (but unsigned) JWT — sufficient for payload-decoding tests:

```ts
function makeJwt(payload: Record<string, unknown>): string {
  const header = { alg: 'HS256', typ: 'JWT' }
  return btoa(JSON.stringify(header)) + '.' + btoa(JSON.stringify(payload)) + '.fakesig'
}
```

### What's Tested

**`token.test.ts`** — 15 tests
- `isTokenExpired`: future token → false, past → true, no `exp` claim → false, malformed → true
- `getTokenExpirationTime`: returns `exp * 1000` ms, null when no claim or invalid token
- `getTimeUntilExpiration`: positive ms for future, 0 for expired/invalid (never negative)

**`formHelpers.test.ts`** — 20 tests
- `getFieldComponentName`: all field types map to correct component names, unknown type → `TerminalTextField`
- `decodeConnectionData`: string/empty/null port handling, optional empty fields removed (not set to null), non-empty fields preserved, original object not mutated

**`stepper.test.ts`** — 18 tests
- `createStep`: correct id/title/description/icon, defaults (`disabled: false`, empty `data`/`errors`, `isLoading: false`)
- `getAllStepData`: merges all step data, empty array → `{}`, later step wins on key collision
- `isStepValid`: no errors + no validate → true, errors present → false, custom `validate()` called with correct args, both custom validate and field errors checked
- `canProceedFromStep`: valid non-loading → true, loading → false, errors → false, out-of-bounds index → false

**`terminal.test.ts`** — enum value tests
- Verifies `TerminalCommand` enum includes `CONNECT_EXPORT = 'connect export'` and `CONNECT_IMPORT = 'connect import'`

**`terminal.backupOperations.test.ts`** — enum value tests
- Verifies `TerminalCommand` enum includes `BACKUP_EXPORT = 'backup export'` and `BACKUP_IMPORT = 'backup import'`

---

## Docker & `.dockerignore`

### Test Environment (`docker-compose.test.yml`)

Tests run in **dedicated lightweight containers** defined in `docker/docker-compose.test.yml`:

| Service | Image | Command |
|---------|-------|---------|
| `backend-test` | `python:3.14-rc-slim` + `.[dev]` deps | `pytest` |
| `frontend-test` | `node:20-alpine` + npm deps | `npm test` |

Key properties:
- **No MongoDB service** — `pymongo.MongoClient` is mocked at the package level in `conftest.py`, so no real socket connection is ever attempted
- **No ports exposed** — containers run and exit cleanly
- **No `restart` policy** — one-shot execution via `docker compose run --rm`
- Source code is **mounted as a volume** so tests pick up the latest changes without rebuilding the image
- Images only rebuild when `--build` is passed to `test.sh` (or explicitly with `docker compose build`)

```bash
# Build test images manually (first time or after dep changes)
docker compose -f docker/docker-compose.test.yml build

# Run backend tests directly
docker compose -f docker/docker-compose.test.yml run --rm backend-test pytest

# Run frontend tests directly
docker compose -f docker/docker-compose.test.yml run --rm frontend-test npm test
```

### `.dockerignore`

Test files are excluded from production Docker images:

**`frontend/.dockerignore`** excludes: `tests`, `vitest.config.ts`, `coverage`

**`backend/.dockerignore`** excludes: `tests`, `.pytest_cache`, `.coverage`, `htmlcov`, `coverage.xml`

Tests run inside the **test containers** (which mount source code as a volume), not in production images.

---

## Coverage

```bash
# Backend: coverage per module, missing lines listed
./scripts/test.sh --backend --coverage

# Frontend: v8 coverage in terminal
./scripts/test.sh --frontend --coverage
```

---

## Related

- [02 - Backend Architecture](02-backend-architecture.md)
- [03 - Frontend Architecture](03-frontend-architecture.md)
- [05 - Deployment Guide](05-deployment.md)
- [12 - File Widget System](12-file-widget-system.md)

## Overview

MongoDB Manager uses a two-track testing strategy: **pure logic unit tests** on both sides of the stack, and **HTTP integration tests** on the backend — all without needing a real MongoDB connection.

Tests run inside **dedicated test containers** (`docker-compose.test.yml`) via a unified shell script — the dev stack does not need to be running.

---

## Running Tests

```bash
# Run everything (backend + frontend)
./scripts/test.sh

# Backend only
./scripts/test.sh --backend

# Frontend only
./scripts/test.sh --frontend

# With coverage reports
./scripts/test.sh --coverage
./scripts/test.sh --backend --coverage
./scripts/test.sh --frontend --coverage

# Force rebuild of test images (after dependency changes)
./scripts/test.sh --build
```

> **No dev stack required.** `test.sh` uses `docker compose run --rm` against `docker/docker-compose.test.yml` — the test containers build and start on their own.

---

## Backend

### Stack

| Tool | Purpose |
|------|---------|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reports |
| `httpx` | HTTP client for FastAPI TestClient |
| `freezegun` | Time freezing for expiry tests |

### Configuration

`backend/pyproject.toml` — `[tool.pytest.ini_options]`:
```toml
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"
```

### File Structure

```
backend/tests/
├── conftest.py                  # Shared fixtures (client, auth_token, auth_headers)
├── utils/
│   ├── test_uri_builder.py      # build_mongodb_uri / build_mongodb_uri_masked
│   └── test_timezone.py         # format_timestamp, add_hours, parse_iso_datetime, is_expired
├── middleware/
│   └── test_auth.py             # create_access_token, verify_token, endpoint auth
└── routers/
    └── test_commands.py         # /api/commands/execute integration tests
```

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture(scope="session")
def client():
    # FastAPI TestClient with mocked init_database / close_database
    # No real MongoDB needed

@pytest.fixture
def auth_token():
    # Valid JWT for username "admin"

@pytest.fixture
def auth_headers(auth_token):
    # {"Authorization": "Bearer <token>"}
```

> `init_database` and `close_database` are patched at the session level so the FastAPI lifespan handler never attempts a real DB connection.

### What's Tested

**`test_uri_builder.py`** — 18 tests
- No-auth URI format (`mongodb://host:port`)
- Auth with `authSource` appended
- Special characters URL-encoded (`@` → `%40`, `:` → `%3A`)
- Database path appended
- Custom options dict in query string
- `ValueError` on empty host, port out of range (0, 65536), non-int port, username/password mismatch
- Masked URI shows `***`, never leaks real password

**`test_timezone.py`** — 13 tests
- `format_timestamp`: aware and naive datetimes, custom format strings
- `add_hours`: positive, zero, negative, day-crossing
- `parse_iso_datetime`: valid ISO strings (UTC, offset, naive), invalid input raises `ValueError`
- `is_expired`: past/future/boundary, injectable `current_time` parameter

**`test_auth.py`** — 11 tests
- `create_access_token` returns a 3-part JWT string
- Token round-trips through `verify_token` correctly
- `exp` claim is ~24 hours from now
- Tampered / expired / missing-claim tokens all raise `HTTPException(401)`
- Endpoint returns 403 without token, reaches handler with valid token

**`test_commands.py`** — 13 integration tests
- Health check (`/health`) needs no auth
- Execute endpoint returns 403 without token, 403 with invalid token
- `connect list` returns 200 + `{success, output, exit_code}` shape
- `connect remove []` → `success: false`, `"No connections selected"`
- `backup folder delete` without confirmation → `success: false`, error mentions "confirm"
- Missing required fields (`connection_name`, `folder_path`) return clear error messages
- `connect test []`, `connect update` (no connection), `backup create` (no connection), `backup restore` (no confirmation) all return `success: false`

---

## Frontend

### Stack

| Tool | Purpose |
|------|---------|
| `vitest` | Test runner |
| `@vue/test-utils` | Vue component utilities |
| `jsdom` | Browser environment simulation |
| `@vitest/coverage-v8` | Coverage reports |

### Configuration

`frontend/vitest.config.ts`:
```ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
  },
  resolve: {
    alias: { '~': resolve(__dirname, 'app') },
  },
})
```

`~` resolves to `frontend/app/` — matching the Nuxt alias.

### npm Scripts

```bash
npm test              # vitest run (single pass)
npm run test:watch    # vitest (watch mode)
npm run test:coverage # vitest run --coverage
```

### File Structure

```
frontend/tests/
├── utils/
│   ├── token.test.ts        # isTokenExpired, getTokenExpirationTime, getTimeUntilExpiration
│   └── formHelpers.test.ts  # getFieldComponentName, decodeConnectionData
└── types/
    └── stepper.test.ts      # createStep, getAllStepData, isStepValid, canProceedFromStep
```

### JWT Test Helper

All token tests use a `makeJwt()` helper that builds a structurally valid (but unsigned) JWT — sufficient for payload-decoding tests:

```ts
function makeJwt(payload: Record<string, unknown>): string {
  const header = { alg: 'HS256', typ: 'JWT' }
  return btoa(JSON.stringify(header)) + '.' + btoa(JSON.stringify(payload)) + '.fakesig'
}
```

### What's Tested

**`token.test.ts`** — 15 tests
- `isTokenExpired`: future token → false, past → true, no `exp` claim → false, malformed → true
- `getTokenExpirationTime`: returns `exp * 1000` ms, null when no claim or invalid token
- `getTimeUntilExpiration`: positive ms for future, 0 for expired/invalid (never negative)

**`formHelpers.test.ts`** — 20 tests
- `getFieldComponentName`: all field types map to correct component names, unknown type → `TerminalTextField`
- `decodeConnectionData`: string/empty/null port handling, optional empty fields removed (not set to null), non-empty fields preserved, original object not mutated

**`stepper.test.ts`** — 18 tests
- `createStep`: correct id/title/description/icon, defaults (`disabled: false`, empty `data`/`errors`, `isLoading: false`)
- `getAllStepData`: merges all step data, empty array → `{}`, later step wins on key collision
- `isStepValid`: no errors + no validate → true, errors present → false, custom `validate()` called with correct args, both custom validate and field errors checked
- `canProceedFromStep`: valid non-loading → true, loading → false, errors → false, out-of-bounds index → false

---

## Docker & `.dockerignore`

### Test Environment (`docker-compose.test.yml`)

Tests run in **dedicated lightweight containers** defined in `docker/docker-compose.test.yml`:

| Service | Image | Command |
|---------|-------|---------|
| `backend-test` | `python:3.13-slim` + `.[dev]` deps | `pytest` |
| `frontend-test` | `node:20-alpine` + npm deps | `npm test` |

Key properties:
- **No MongoDB service** — `pymongo.MongoClient` is mocked at the package level in `conftest.py`, so no real socket connection is ever attempted
- **No ports exposed** — containers run and exit cleanly
- **No `restart` policy** — one-shot execution via `docker compose run --rm`
- Source code is **mounted as a volume** so tests pick up the latest changes without rebuilding the image
- Images only rebuild when `--build` is passed to `test.sh` (or explicitly with `docker compose build`)

```bash
# Build test images manually (first time or after dep changes)
docker compose -f docker/docker-compose.test.yml build

# Run backend tests directly
docker compose -f docker/docker-compose.test.yml run --rm backend-test pytest

# Run frontend tests directly
docker compose -f docker/docker-compose.test.yml run --rm frontend-test npm test
```

### `.dockerignore`

Test files are excluded from production Docker images:

**`frontend/.dockerignore`** excludes: `tests`, `vitest.config.ts`, `coverage`

**`backend/.dockerignore`** excludes: `tests`, `.pytest_cache`, `.coverage`, `htmlcov`, `coverage.xml`

Tests run inside the **test containers** (which mount source code as a volume), not in production images.

---

## Coverage

```bash
# Backend: coverage per module, missing lines listed
./scripts/test.sh --backend --coverage

# Frontend: v8 coverage in terminal
./scripts/test.sh --frontend --coverage
```

---

## Related

- [02 - Backend Architecture](02-backend-architecture.md)
- [03 - Frontend Architecture](03-frontend-architecture.md)
- [05 - Deployment Guide](05-deployment.md)
