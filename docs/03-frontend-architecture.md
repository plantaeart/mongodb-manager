# 03 - Frontend Architecture

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
│   │   └── CommandInput.vue
│   └── Panel/        # Side panels
│       └── VisualPanel.vue
├── composables/      # Singleton services
│   ├── useWebSocket.ts    # WebSocket service (singleton)
│   └── useTerminal.ts     # Terminal service (singleton)
├── stores/           # Pinia state stores
│   └── auth.ts       # Authentication store
├── pages/            # Route pages
│   └── index.vue     # Main application page
├── types/            # TypeScript type definitions
│   ├── auth.ts       # Auth types
│   └── terminal.ts   # Terminal message types
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
- Executes commands (built-in and server commands)
- Manages favorite commands with localStorage persistence
- Handles WebSocket message processing

## State Management (Pinia)

### Auth Store (`stores/auth.ts`)
**Responsibilities**:
- User authentication state (isAuthenticated, token, username)
- Login/logout actions
- Password change actions
- Token persistence in localStorage

**State**:
```typescript
{
  isAuthenticated: boolean
  token: string | null
  username: string | null
  needsPasswordChange: boolean
}
```

## Component Communication

### Pattern 1: Singleton Service (Terminal)
```
CommandInput.vue                    TerminalOutput.vue
       ↓                                   ↓
   useTerminal()  ← Same Instance →   useTerminal()
       ↓                                   ↓
   executeCommand()                  commandHistory
       ↓                                   ↓
Updates shared commandHistory array
```

### Pattern 2: Pinia Store (Auth)
```
LoginModal.vue              index.vue
      ↓                         ↓
  authStore.login()      authStore.isAuthenticated
      ↓                         ↓
Updates shared auth state
```

### Pattern 3: WebSocket Messages
```
WebSocketService (receives message)
         ↓
Notifies all registered handlers
         ↓
TerminalService.handleWebSocketMessage()
         ↓
Updates commandHistory
         ↓
TerminalOutput auto-updates (reactive)
```

## Styling

**Theme**: Custom Gruvbox color scheme
**CSS Variables**:
- `--gb-bg`: Background colors
- `--gb-fg`: Foreground colors  
- `--gb-green`, `--gb-red`, `--gb-blue`, etc.: Theme colors

**Approach**: Scoped styles per component + global theme variables

## TypeScript Types

### Terminal Types (`types/terminal.ts`)
- `TerminalEntry`: Command history entry
- `WebSocketMessage`: WebSocket message types
- `CommandExecuteRequest`: Command execution request

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

## Related Documentation

- [03.1 - State Management](03.1-state-management.md) - Detailed singleton pattern
- [01 - Overview](01-overview.md) - Project overview
- [02.2 - WebSocket System](02.2-websocket-system.md) - Backend WebSocket
