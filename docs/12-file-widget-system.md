# 12 - File Widget System (Transfer Commands)
**Last Updated:** 2026-04-05

## Overview

The File Widget system handles the 4 transfer commands — `backup export`, `backup import`, `connect export`, `connect import` — that require browser file APIs (download or upload). These commands bypass the standard WebSocket/form system entirely and use dedicated REST endpoints + a purpose-built frontend widget.

## Why a Separate System?

The existing form system sends JSON over WebSocket. That approach cannot handle:
- **Binary streaming downloads** (ZIP / JSON file to browser)
- **Multipart file uploads** (user picks a file from their disk)

These 4 commands use native browser `fetch`, `Blob`, `FormData`, and `URL.createObjectURL` instead.

## Architecture

```
User types command
      │
      ▼
useTerminal.ts
  FILE_WIDGET_COMMANDS.has(cmd)?
      │ yes
      ▼
executeFileWidgetCommand()
  GET /api/transfer/.../options   ← fetch options (dropdowns)
      │
      ▼
TerminalEntry { fileWidget: FileWidgetData }  ← added to history
      │
      ▼
TerminalOutput.vue renders TerminalFileWidget.vue
      │
      ▼
User fills widget + clicks submit
      │
      ├─ export → GET /api/transfer/.../export  → StreamingResponse → downloadBlob()
      └─ import → POST /api/transfer/.../import → multipart upload → success message
      │
      ▼
widget emits 'done' / 'cancel'
      │
      ▼
resolveFileWidget() / cancelFileWidget()
  entry.status = SUCCESS / ERROR
  entry.fileWidget kept (shows readonly done-state)
```

## Backend — Transfer Router

**File**: `backend/app/routers/transfer.py`  
**Prefix**: `/api/transfer`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/backup/export/options` | List all backups as dropdown options |
| `GET` | `/backup/import/options` | List registered backup folders |
| `GET` | `/backup/export?backup_selector=folder\|name` | Stream ZIP download |
| `POST` | `/backup/import` | Upload ZIP, extract into folder |
| `GET` | `/connect/export` | Stream connections.json (no passwords) |
| `POST` | `/connect/import` | Upload connections.json, insert/update |

All endpoints require a valid JWT (`Authorization: Bearer <token>`).

### `backup_selector` format

Export uses a composite key `folder_path|backup_name` (pipe-separated) to identify a backup, since backup names are only unique within a folder.

### Business logic lives in core modules

- ZIP pack/unpack → `BackupManager.export_backup_zip()` / `import_backup_zip()` in `backup_ops.py`
- Connection sanitise/import → `ConnectionManager.export_connections()` / `import_connections()` in `connection_ops.py`

### Connection import options

| Field | Default | Effect |
|-------|---------|--------|
| `overwrite` | `false` | When `true`, existing connections with the same name are updated |
| `import_backup_paths` | `false` | When `true`, `backup_paths` from the file are preserved; otherwise stripped |

Passwords are **always stripped on export** and never included in the downloaded file.

## Frontend — Types

**File**: `frontend/app/types/terminal.ts`

```typescript
export type FileWidgetMode =
  | 'backup-export'
  | 'backup-import'
  | 'connect-export'
  | 'connect-import'

export interface FileWidgetOption {
  value: string
  label: string
  description?: string
}

export interface FileWidgetData {
  mode: FileWidgetMode
  backupOptions?: FileWidgetOption[]   // for 'backup-export'
  folderOptions?: FileWidgetOption[]   // for 'backup-import'
}
```

`TerminalEntry` has an optional `fileWidget?: FileWidgetData | null` field alongside the existing `form` field.

## Frontend — Composable (`useTerminal.ts`)

```typescript
/** Commands routed to the file-widget path (not WebSocket / form) */
const FILE_WIDGET_COMMANDS = new Set<TerminalCommand>([
  TerminalCommand.BACKUP_EXPORT,
  TerminalCommand.BACKUP_IMPORT,
  TerminalCommand.CONNECT_EXPORT,
  TerminalCommand.CONNECT_IMPORT,
])
```

**Lifecycle methods:**

| Method | Signature | Purpose |
|--------|-----------|---------|
| `executeFileWidgetCommand` | `(cmd: TerminalCommand) → void` | Fetch options, push entry with `fileWidget` |
| `resolveFileWidget` | `(entryId, message) → void` | Mark entry SUCCESS, clear active widget |
| `cancelFileWidget` | `(entryId) → void` | Mark entry ERROR, clear active widget |

`hasActiveWidget` computed getter is exposed in the composable return value (mirrors `hasActiveForm`).

## Frontend — Component (`TerminalFileWidget.vue`)

**File**: `frontend/app/components/Terminal/Forms/TerminalFileWidget.vue`

Renders one of four modes inside the terminal history. Becomes **readonly** when `entry.status !== RUNNING`.

### Modes

| Mode | UI elements |
|------|------------|
| `backup-export` | Backup selector (dropdown), submit downloads ZIP |
| `backup-import` | Folder selector + file picker (`.zip`), overwrite checkbox |
| `connect-export` | Info box only ("passwords not included"), submit downloads JSON |
| `connect-import` | File picker (`.json`), overwrite + import_backup_paths checkboxes |

### Props / Events

```typescript
// Props
interface Props {
  widgetData: FileWidgetData
  readonly?: boolean
}

// Events
emit('done', message: string)   // operation succeeded
emit('cancel')                  // user clicked Cancel
```

### API calls inside the widget

Uses native `fetch` (not `$fetch`) to handle binary responses (`response.blob()`).

```typescript
// Export: GET → Blob → downloadBlob()
const response = await fetch(`${baseUrl}/api/transfer/backup/export?...`, { headers })
const blob = await response.blob()
downloadBlob(blob, filename)

// Import: POST multipart → JSON result
const formData = new FormData()
formData.append('file', selectedFile)
formData.append('folder_path', folderPath)
const response = await fetch(url, { method: 'POST', headers, body: formData })
```

## Frontend — Utility (`downloadFile.ts`)

**File**: `frontend/app/utils/downloadFile.ts`

```typescript
/**
 * Trigger a browser file download from a Blob.
 * Creates a temporary object URL, clicks a hidden anchor, then revokes.
 */
export function downloadBlob(blob: Blob, filename: string): void
```

## Adding a New File-Widget Command

1. Add enum entry in `frontend/app/enums/terminal.ts`
2. Add `Command` entry in `backend/app/enums/commands.py`
3. Add endpoint(s) in `backend/app/routers/transfer.py`
4. Add the command to `FILE_WIDGET_COMMANDS` in `useTerminal.ts`
5. Add a new `mode` to `FileWidgetMode` in `types/terminal.ts`
6. Add the new mode branch to `TerminalFileWidget.vue` (template + `modeConfig` + `canSubmit` + `handleSubmit`)
7. Add tests in `backend/tests/routers/test_transfer.py`

## Related

- [07 - Terminal Forms System](07-terminal-forms.md) — the WebSocket-based form system (different path)
- [04 - Business Logic](04-business-logic.md) — backup/connection core operations
- [02 - Backend Architecture](02-backend-architecture.md) — router registration
- [11 - Testing Guide](11-testing.md) — transfer endpoint tests
