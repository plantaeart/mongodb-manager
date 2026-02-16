# CLI Dual-Mode Pattern

## Overview

MongoDB Manager CLI commands support two execution modes:
1. **Direct Mode**: Non-interactive, parameter-based execution
2. **Interactive Mode**: Terminal wizard with prompts

## Architecture

### Direct Mode
- Accepts command-line parameters (e.g., `--name`, `--uri`)
- Executes immediately without user prompts
- Used by: HTTP API, scripts, automation
- Always synchronous

### Interactive Mode
- Shows terminal wizards using `questionary`
- Used by: Direct terminal usage (native terminal only)
- Always synchronous
- Falls back when no parameters provided

## Important Constraints

### ❌ WebSocket Forms in CLI Commands
**Never** use async WebSocket forms in CLI commands:
- CLI commands are synchronous (Typer requirement)
- WebSocket terminal runs in uvloop event loop
- Cannot mix async/await with sync CLI execution
- Results in deadlocks and infinite loops

### ✅ WebSocket Forms via HTTP API
WebSocket forms should be handled via:
- Dedicated HTTP API routes (e.g., `/api/connections/remove`)
- Frontend calls API with form data
- API calls CLI in direct mode with parameters

## Implementation Pattern

### Example: connect add

**Direct Mode:**
```python
@connect_app.command("add")
def connect_add(
    name: str | None = None,
    uri: str | None = None,
    description: str = ""
):
    if name and uri:
        # Direct mode: add immediately
        conn_mgr.add_connection(name, uri, description)
        return
    
    # Interactive mode: show wizard
    _show_add_connection_wizard(conn_mgr)
```

**Interactive Wizard (questionary only):**
```python
def _show_add_connection_wizard(conn_mgr):
    choice = questionary.select(...).ask()
    name = questionary.text(...).ask()
    # etc.
```

### Example: connect remove

**Direct Mode:**
```python
@connect_app.command("remove")
def connect_remove(name: str | None = None):
    if name:
        # Direct mode: remove specific connection
        _remove_connection_direct(conn_mgr, name)
        return
    
    # Interactive mode: show selection wizard
    _show_remove_connection_wizard(conn_mgr)
```

**Interactive Wizard:**
```python
def _show_remove_connection_wizard(conn_mgr):
    # Use questionary for selection (single connection)
    _show_remove_form_terminal(conn_mgr, connections)
```

## WebSocket Terminal Limitation

Questionary prompts don't work in WebSocket terminals because:
- WebSocket terminal is a browser-based UI
- `questionary` requires a real TTY (terminal device)
- `sys.stdin.isatty()` returns `False` in WebSocket context
- Interactive prompts are automatically skipped

**Solution**: Use HTTP API + frontend forms instead of CLI wizards in WebSocket context.

## Rules

1. ✅ **DO**: Accept parameters for direct mode
2. ✅ **DO**: Use questionary for terminal interactive mode
3. ✅ **DO**: Keep all CLI commands synchronous
4. ❌ **DON'T**: Use async/await in CLI commands
5. ❌ **DON'T**: Call FormManager.request_form() from CLI
6. ❌ **DON'T**: Use asyncio.run() in CLI commands
7. ❌ **DON'T**: Try to wait for async tasks from sync code

## Testing

**Direct Mode (works everywhere):**
```bash
mongodb-manager connect add --name test --uri mongodb://localhost:27017
mongodb-manager connect remove --name test
```

**Interactive Mode (native terminal only):**
```bash
mongodb-manager connect add
# Shows questionary prompts in native terminal
# Returns None in WebSocket terminal (TTY check fails)

mongodb-manager connect remove
# Shows selection menu in native terminal
# Returns None in WebSocket terminal
```

**WebSocket Terminal (use HTTP API):**
- Frontend provides forms/dialogs
- Forms submit to API routes
- API executes CLI in direct mode with parameters
