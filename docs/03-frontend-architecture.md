# 03 - Frontend Architecture
**Last Updated:** 2026-04-05

## Overview

Nuxt 4.2.2 application with Vue 3.5.27, providing a terminal-style UI for MongoDB management.

## Directory Structure

```
frontend/app/
├── components/       # Vue components
│   ├── Auth/         # Authentication modals
│   │   ├── LoginModal.vue
│   │   └── ChangePasswordModal.vue
│   ├── Terminal/     # Terminal interface
│   │   ├── TerminalWindow.vue
│   │   ├── TerminalOutput.vue
│   │   ├── CommandInput.vue
│   │   └── Forms/
│   │       ├── TerminalForm.vue          # WebSocket form renderer
│   │       ├── TerminalFileWidget.vue    # File export/import widget
│   │       └── (field components...)
│   └── Panel/        # Side panels
│       └── VisualPanel.vue
├── composables/      # Singleton services
│   ├── useWebSocket.ts    # WebSocket service (singleton)
│   └── useTerminal.ts     # Terminal service (singleton)
├── stores/           # Pinia state stores
│   └── auth.ts       # Authentication store
├── pages/            # Route pages
│   └── index.vue     # Main application page
├── utils/            # Utility functions
│   └── downloadFile.ts    # downloadBlob() helper
├── types/            # TypeScript type definitions
│   ├── auth.ts       # Auth types
│   └── terminal.ts   # Terminal message types + FileWidgetData
└── app.vue           # Root component
```

## Component Hierarchy

```
app.vue (Root)
  └── pages/index.vue (Main Page)
      ├── LoginModal (v-if !authenticated)
      ├── ChangePasswordModal (v-if needsPasswordChange)
      └── TerminalWindow (v-if authenticated)
          ├── TerminalOutput (displays command history)
          │   ├── TerminalForm (v-if entry.form)
          │   └── TerminalFileWidget (v-else-if entry.fileWidget)
          ├── CommandInput (user input)
          └── VisualPanel (optional side panel)
```

## Singleton Services (Composables)

### Why Singletons?
Ensures **shared state** across all components. Multiple components can call the same composable and access the same data instance.

### 1. WebSocketService (`useWebSocket.ts`)
- Manages single WebSocket connection
- Handles authentication-based connection lifecycle
- Provides message handler registration
- Auto-reconnect with exponential backoff

### 2. TerminalService (`useTerminal.ts`)
- Manages terminal command history (shared across all components)
- Executes commands via three paths: built-in, form, or file widget
- Manages favorite commands with localStorage persistence
- Handles WebSocket message processing

**Command routing:**
```typescript
// Built-in
if (cmd === CLEAR || cmd === HELP) { ... }

// Form (REST + WebSocket)
if (getApiPathForCommand(cmd)) { await executeFormCommand(...) }

// File widget (REST + browser file APIs)
if (FILE_WIDGET_COMMANDS.has(cmd)) { await executeFileWidgetCommand(...) }

// Otherwise → WebSocket
sendCommandFn(cmd)
```

**File widget lifecycle methods exposed:**

| Method | Purpose |
|--------|---------|
| `resolveFileWidget(id, msg)` | Mark entry SUCCESS after download/upload |
| `cancelFileWidget(id)` | Mark entry ERROR on Cancel |
| `hasActiveWidget` | Computed boolean (mirrors `hasActiveForm`) |

## State Management (Pinia)

### Auth Store (`stores/auth.ts`)
**State**:
```typescript
{
  isAuthenticated: boolean
  token: string | null
  username: string | null
  needsPasswordChange: boolean
}
```

## TypeScript Types

### Terminal Types (`types/terminal.ts`)
- `TerminalEntry` — command history entry (has optional `form` and `fileWidget` fields)
- `FileWidgetData` / `FileWidgetMode` / `FileWidgetOption` — file widget state
- `WebSocketMessage`, `FormRequestMessage`, `FormField`, etc. — form system types

### Auth Types (`types/auth.ts`)
- `LoginRequest`, `LoginResult`
- `PasswordChangeRequest`, `PasswordChangeResult`

## Key Features

1. **Auto-focus**: Terminal input auto-focuses on mount
2. **Command History**: Up/Down arrows navigate previous commands
3. **Auto-complete**: Tab completion for known commands
4. **Favorites**: Star commands for quick access
5. **Syntax Highlighting**: Color-coded output (success/error/warning)
6. **Auto-scroll**: Terminal scrolls to show latest output
7. **File Widget**: In-terminal UI for file download/upload operations (no WebSocket needed)

## Related Documentation

- [03.1 - State Management](03.1-state-management.md) - Detailed singleton pattern
- [07 - Terminal Forms System](07-terminal-forms.md) - WebSocket form system
- [12 - File Widget System](12-file-widget-system.md) - File export/import widget
- [02.2 - WebSocket System](02.2-websocket-system.md) - Backend WebSocket
