# Terminal Forms System

## Overview

The Terminal Forms System provides an interactive, form-based interface for CLI commands in the WebSocket terminal. Instead of typing command arguments manually, users interact with rich, validated forms that guide them through complex operations.

## Architecture

### Components

The terminal forms system consists of four main layers:

1. **Frontend Configuration** (`frontend/app/config/terminalForms.ts`)
   - Centralized form configurations
   - Form registry with all available forms
   - Multi-mode form support (simple/advanced)

2. **Backend Form Definitions** (`backend/app/core/form_definitions.py`)
   - Pydantic schemas for form structure
   - Field validation rules
   - Form actions (submit, cancel, etc.)

3. **Form Components** (`frontend/app/components/Terminal/Forms/`)
   - `TerminalForm.vue` - Base form component
   - Field components (`TerminalTextField.vue`, `TerminalCheckboxListField.vue`, etc.)
   - Form actions component

4. **WebSocket Communication** (`backend/app/websocket/`)
   - `FormManager` - Handles form requests/responses
   - WebSocket terminal handler - Routes messages
   - Context variables for CLI access

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User types command in terminal                              │
│    Example: "connect remove"                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. WebSocket sends execute message to backend                  │
│    { type: "execute", command: "connect remove" }               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. CLI command detects WebSocket context                       │
│    - get_websocket_context() returns WebSocket                  │
│    - get_form_manager() returns FormManager                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CLI builds form schema with dynamic data                    │
│    - Populate select/checkbox options from database             │
│    - Set field defaults, validation rules                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. FormManager sends form to frontend                          │
│    await form_manager.request_form(websocket, form_schema)      │
│    Creates Future and waits for response                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Frontend displays form in terminal                          │
│    - TerminalForm renders fields                                │
│    - User fills out form and clicks submit                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Frontend sends form_submit message                          │
│    { type: "form_submit", form_id: "...", data: {...} }        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. FormManager resolves Future with form data                  │
│    - handle_form_submit() sets result on Future                 │
│    - CLI receives form data and continues execution             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. CLI processes form data and returns output                  │
│    - Validates data                                              │
│    - Performs operation                                          │
│    - Sends success/error messages to terminal                   │
└─────────────────────────────────────────────────────────────────┘
```

## Form Configuration

### Frontend Configuration (`terminalForms.ts`)

**Backend is the single source of truth** for all form definitions. The frontend only maps commands to API endpoints:

```typescript
/**
 * Command to API Path Registry
 * 
 * Maps terminal commands to their form API endpoints.
 */
export const COMMAND_TO_API_PATH: Record<string, string> = {
  // Connection Management Commands
  'connect add': 'connect/add',
  'connect remove': 'connect/remove',
  'connect list': 'connect/list',
  'connect test': 'connect/test',
}

/**
 * Get API path for a given command
 */
export function getApiPathForCommand(command: string): string | undefined {
  return COMMAND_TO_API_PATH[command]
}

/**
 * Check if a command has a form
 */
export function hasForm(command: string): boolean {
  return command in COMMAND_TO_API_PATH
}
```

**Key Points:**
- ✅ No form field definitions in frontend
- ✅ No duplicate validation rules
- ✅ Backend API returns complete form schemas
- ✅ Frontend only handles command→API path mapping

### Backend Definition (`form_definitions.py`)

Backend schemas define the complete form structure with validation:

```python
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

CONNECT_REMOVE_FORM = FormSchema(
    title="Remove MongoDB Connection(s)",
    description="Select one or more connections to remove. This action cannot be undone.",
    fields=[
        FormField(
            id="connections",
            label="Connections to Remove",
            type="checkbox-list",
            required=True,
            help_text="Select at least one connection to remove",
            options=[]  # Populated dynamically in CLI
        )
    ],
    actions=[
        FormAction(label="Remove Selected", style="danger", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
```

**Key Components:**
- `FormField` - Individual field definition
- `SelectOption` - Options for select/checkbox-list fields
- `FormAction` - Buttons (submit, cancel, etc.)
- `FormSchema` - Complete form definition
- `ValidationRule` - Field validation (pattern, min, max, etc.)

## Field Types

### Text Field (`text`)

Single-line text input with validation support.

```python
FormField(
    id="name",
    label="Connection Name",
    type="text",
    required=True,
    placeholder="my-mongodb",
    validation=ValidationRule(
        pattern=r"^[a-zA-Z0-9_-]+$",
        message="Only letters, numbers, - and _ allowed"
    ),
    help_text="Unique name for this connection"
)
```

**Props:**
- `placeholder` - Placeholder text
- `validation` - Pattern, min/max length
- `default` - Default value
- `tooltip` - Optional tooltip text (displayed as info icon)

**Frontend Component:** `TerminalTextField.vue`

**Example with Tooltip:**
```python
FormField(
    id="uri",
    label="Connection URI",
    type="text",
    required=True,
    placeholder="mongodb://localhost:27017",
    help_text="Full MongoDB connection string",
    tooltip="Docker: Use host.docker.internal for cross-network connections"
)
```

### Password Field (`password`)

Masked text input for sensitive data.

```python
FormField(
    id="password",
    label="Password",
    type="password",
    required=False,
    placeholder="••••••••",
    help_text="Required if username is provided"
)
```

**Props:**
- Same as text field
- Renders as masked input
- `tooltip` - Optional tooltip text

**Frontend Component:** `TerminalPasswordField.vue`

### Number Field (`number`)

Numeric input with min/max validation.

```python
FormField(
    id="port",
    label="Port",
    type="number",
    required=True,
    default=27017,
    min=1,
    max=65535,
    help_text="MongoDB server port (default: 27017)"
)
```

**Props:**
- `min` - Minimum value
- `max` - Maximum value
- `step` - Increment step
- `default` - Default value

**Frontend Component:** `TerminalNumberField.vue`

### Checkbox List Field (`checkbox-list`)

Multi-select checkbox list for selecting multiple options.

```python
FormField(
    id="connections",
    label="Connections to Remove",
    type="checkbox-list",
    required=True,
    help_text="Select at least one connection to remove",
    options=[
        SelectOption(
            value="prod-db",
            label="prod-db",
            description="mongodb://prod:27017",
            metadata={
                "uri": "mongodb://prod:27017",
                "added_at": "2024-01-15 10:30"
            }
        )
    ]
)
```

**Props:**
- `options` - List of `SelectOption` objects
- `required` - If true, at least 1 must be selected
- Returns array of selected values

**Frontend Component:** `TerminalCheckboxListField.vue`

**Features:**
- "Select All" / "Clear Selection" buttons
- Selection count display
- Table-like layout with metadata
- Terminal-themed checkboxes
- Hover effects

### Select Field (`select`)

Dropdown selection (single value).

```python
FormField(
    id="mode",
    label="Connection Mode",
    type="select",
    required=True,
    options=[
        SelectOption(value="simple", label="Simple Mode"),
        SelectOption(value="advanced", label="Advanced Mode")
    ]
)
```

**Props:**
- `options` - List of `SelectOption` objects
- Returns single selected value

**Frontend Component:** `TerminalSelectField.vue` (to be implemented)

### Textarea Field (`textarea`)

Multi-line text input.

```python
FormField(
    id="description",
    label="Description",
    type="textarea",
    rows=3,
    placeholder="Enter description..."
)
```

**Props:**
- `rows` - Number of visible rows

**Frontend Component:** `TerminalTextareaField.vue` (to be implemented)

### Readonly Field (`readonly`)

Display-only text field for showing formatted plain text information.

```python
FormField(
    id="info",
    label="Information",
    type="readonly",
    content="This is read-only information."
)
```

**Props:**
- `content` - Plain text to display (supports multi-line with `\n`)

**Frontend Component:** `TerminalReadonlyField.vue`

**Use Cases:**
- Display simple text messages
- Show plain text reports
- Present unformatted information

**Example: Simple Message**
```python
FormField(
    id="message",
    label="",
    type="readonly",
    content="No connections configured.\n\nUse 'connect add' to create your first connection."
)
```

### List Field (`list`)

**IMPORTANT:** Use this field type to display structured data as formatted panels in form mode. This is NOT for CLI output - it's for rendering rich UI components within terminal forms.

Display structured data as interactive panels with icons, labels, and organized information.

```python
FormField(
    id="connections_list",
    label="Connections",
    type="list",
    items=[
        {
            "name": "prod-db",
            "uri": "mongodb://****@prod:27017",
            "description": "Production database",
            "added_at": "2024-01-15T10:30:00Z"
        },
        {
            "name": "dev-db",
            "uri": "mongodb://localhost:27017",
            "description": "Development environment",
            "added_at": "2024-01-16T14:20:00Z"
        }
    ]
)
```

**Props:**
- `items` - Array of objects to display as panels
- Each item can have any properties (name, uri, description, etc.)
- Frontend component renders items as styled panels

**Frontend Component:** `TerminalListField.vue`

**Use Cases:**
- **Display connection lists** (`connect list` command) - Shows connections as panels
- **Show database lists** - Display available databases
- **List backups** - Show backup history with metadata
- **Display any structured data** in form mode

**Rendering:**
- Each item is displayed as a bordered panel/card
- Panel header shows the item name with icon
- Panel body shows all properties as labeled rows
- Automatic formatting with icons (🔗 for URI, 📝 for description, 📅 for dates)
- Responsive design with hover effects
- Total count displayed at bottom

**Example: Connection List Form (Complete)**
```python
# Backend - Populate items dynamically
CONNECT_LIST_FORM = FormSchema(
    title="MongoDB Connections",
    description="Configured MongoDB connections",
    fields=[
        FormField(
            id="connections_list",
            label="",
            type="list",
            items=[]  # Populated dynamically from ConnectionManager
        )
    ],
    actions=[
        FormAction(label="Close", style="secondary", action="cancel")
    ]
)

# Backend route handler - Populate with data
@router.get("/forms/connect/list")
async def get_connect_list_form():
    conn_mgr = ConnectionManager()
    connections = conn_mgr.list_connections()
    
    form_dict = CONNECT_LIST_FORM.dict()
    
    # Build items from connections
    items = []
    for conn in connections:
        items.append({
            "name": conn["name"],
            "uri": mask_password_in_uri(conn["uri"]),
            "description": conn.get("description", ""),
            "added_at": conn.get("added_at", "")
        })
    
    # Populate field items
    form_dict["fields"][0]["items"] = items
    
    return form_dict
```

**Frontend Display:**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 📌 prod-db                                                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ 🔗 URI: mongodb://****@prod:27017                                            │
│ 📝 Description: Production database                                          │
│ 📅 Added: 01/15/2024, 10:30:00 AM                                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ 📌 dev-db                                                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ 🔗 URI: mongodb://localhost:27017                                            │
│ 📝 Description: Development environment                                      │
│ 📅 Added: 01/16/2024, 02:20:00 PM                                            │
└──────────────────────────────────────────────────────────────────────────────┘

Total: 2 connection(s)
```

**Key Differences from `readonly`:**
- `readonly` - Plain text display (use for messages, unformatted text)
- `list` - Structured data panels (use for displaying collections of objects in form mode)

**When to use `list` field type:**
✅ Displaying arrays of structured objects (connections, databases, backups, etc.)
✅ Need formatted panels with icons and labels
✅ Want interactive hover effects and modern UI
✅ Showing data in **form mode** within the terminal

**When NOT to use `list` field type:**
❌ CLI text output (use rich console formatting instead)
❌ Simple messages (use `readonly` instead)
❌ Single values (use appropriate input field types)

## Field Tooltips

All field types support **optional tooltips** to provide contextual help without cluttering the UI.

### Backend Definition

Add `tooltip` to any `FormField`:

```python
FormField(
    id="host",
    label="Host",
    type="text",
    required=True,
    placeholder="localhost",
    help_text="MongoDB server hostname or IP",
    tooltip="Docker: Use container name (same network) or host.docker.internal"
)
```

### Frontend Display

- **Info icon** (ℹ️) appears next to field label
- **Tooltip shows on hover** above the icon
- **Smart positioning**: 
  - Centered when space allows
  - Left-aligned when near screen edges
  - Right-aligned when on right side
- **Pure CSS**: No JavaScript, lightweight
- **Responsive**: Adapts on mobile screens

### Tooltip Guidelines

**Length**: Keep tooltips concise (40-70 characters)
**Content**: Focus on context-specific tips (e.g., Docker networking, special cases)
**Purpose**: Supplement `help_text`, don't duplicate it

**Good Example:**
```python
tooltip="Docker: Use host.docker.internal for cross-network connections"
```

**Bad Example:**
```python
tooltip="This is the port field where you enter the port number for MongoDB"
```

### Supported Field Types

All field types support tooltips:
- ✅ `text`
- ✅ `password`
- ✅ `number`
- ✅ `checkbox-list`
- ✅ `select` (when implemented)
- ✅ `textarea` (when implemented)

## Creating Custom Field Components

### Component Interface

All field components must follow this interface:

**Props:**
```typescript
interface FieldProps {
  field: FormField        // Field definition from backend
  modelValue: any         // Current value
  disabled?: boolean      // Form is disabled
  readonly?: boolean      // Field is read-only
}
```

**Emits:**
```typescript
{
  'update:modelValue': (value: any) => void    // Value changed
  'valid': () => void                          // Field is valid
  'invalid': () => void                        // Field is invalid
  'blur': () => void                           // Field lost focus
  'enter': () => void                          // Enter key pressed
}
```

### Example Implementation

```vue
<template>
  <div class="terminal-field">
    <label :for="field.id" class="field-label">
      {{ field.label }}
      <span v-if="field.required" class="required">*</span>
    </label>
    
    <input
      :id="field.id"
      :type="field.type"
      :value="modelValue"
      :placeholder="field.placeholder"
      :disabled="disabled"
      :readonly="readonly"
      @input="handleInput"
      @blur="handleBlur"
      @keydown.enter="handleEnter"
      class="field-input"
    />
    
    <p v-if="field.help_text" class="field-help">
      {{ field.help_text }}
    </p>
    
    <p v-if="errorMessage" class="field-error">
      {{ errorMessage }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FormField } from '~/types/terminal'

interface Props {
  field: FormField
  modelValue: any
  disabled?: boolean
  readonly?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any]
  'valid': []
  'invalid': []
  'blur': []
  'enter': []
}>()

const errorMessage = ref('')

const handleInput = (event: Event) => {
  const value = (event.target as HTMLInputElement).value
  emit('update:modelValue', value)
  validate(value)
}

const handleBlur = () => {
  emit('blur')
}

const handleEnter = () => {
  emit('enter')
}

const validate = (value: any) => {
  // Validation logic
  if (props.field.required && !value) {
    errorMessage.value = 'This field is required'
    emit('invalid')
    return false
  }
  
  if (props.field.validation?.pattern) {
    const regex = new RegExp(props.field.validation.pattern)
    if (!regex.test(value)) {
      errorMessage.value = props.field.validation.message
      emit('invalid')
      return false
    }
  }
  
  errorMessage.value = ''
  emit('valid')
  return true
}

watch(() => props.modelValue, (newValue) => {
  validate(newValue)
}, { immediate: true })
</script>

<style scoped>
/* Terminal-themed styles */
.terminal-field {
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gb-fg);
  margin-bottom: 0.5rem;
}

.required {
  color: var(--gb-red);
}

.field-input {
  width: 100%;
  padding: 0.5rem;
  background: var(--gb-bg);
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  border-radius: 4px;
}

.field-input:focus {
  outline: none;
  border-color: var(--gb-blue);
}

.field-help {
  font-size: 12px;
  color: var(--gb-fg-dim);
  margin-top: 0.25rem;
}

.field-error {
  font-size: 12px;
  color: var(--gb-red);
  margin-top: 0.25rem;
}
</style>
```

### Registering the Component

Add your component to `TerminalForm.vue`:

```typescript
const getFieldComponent = (type: string): any => {
  switch (type) {
    case 'text':
      return TerminalTextField
    case 'password':
      return TerminalPasswordField
    case 'number':
      return TerminalNumberField
    case 'checkbox-list':
      return TerminalCheckboxListField
    case 'my-custom-type':  // Add your type
      return MyCustomField
    default:
      return TerminalTextField
  }
}
```

## Backend Integration

### CLI Command Pattern

```python
from app.websocket.terminal import get_websocket_context, get_form_manager
from app.core.form_definitions import MY_FORM_SCHEMA, SelectOption
import asyncio

def my_command():
    """Command with form support"""
    websocket = get_websocket_context()
    form_manager = get_form_manager()
    
    if websocket and form_manager:
        # WebSocket mode: use form
        asyncio.run(_show_form_websocket(websocket, form_manager))
    else:
        # Terminal mode: fallback to questionary or direct args
        _show_form_terminal()


async def _show_form_websocket(websocket, form_manager):
    """Show form in WebSocket terminal"""
    # Build form with dynamic data
    form_schema = MY_FORM_SCHEMA.copy(deep=True)
    
    # Populate dynamic options
    options = []
    for item in get_items_from_db():
        options.append(SelectOption(
            value=item.id,
            label=item.name,
            description=item.description,
            metadata={
                "created_at": item.created_at,
                "status": item.status
            }
        ))
    
    form_schema.fields[0].options = options
    
    # Send form and wait for response
    result = await form_manager.request_form(websocket, form_schema)
    
    if not result:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Process form data
    name = result.get("name")
    selected_items = result.get("items", [])  # Array for checkbox-list
    
    # Execute operation
    perform_operation(name, selected_items)
    
    console.print("[green]✓[/green] Operation completed successfully")


def _show_form_terminal():
    """Fallback for non-WebSocket terminals"""
    # Use questionary or require CLI arguments
    pass
```

### Dynamic Option Population

```python
# Populate select/checkbox-list options from database
from datetime import datetime

connections = conn_mgr.list_connections()
options = []

for conn in connections:
    uri_display = mask_password_in_uri(conn["uri"])
    desc = conn.get("description", "")
    added_at = conn.get("added_at", "")
    
    # Format date if available
    date_display = ""
    if added_at:
        try:
            dt = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
            date_display = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date_display = added_at
    
    options.append(SelectOption(
        value=conn["name"],
        label=conn["name"],
        description=desc or uri_display,
        metadata={
            "uri": uri_display,
            "description": desc,
            "added_at": date_display
        }
    ))

# Update form field
form_schema.fields[0].options = options
```

### Multi-Mode Forms

For forms with simple/advanced modes (like `connect add`):

```python
# Frontend determines which fields to show based on mode
# Backend receives all fields, processes only relevant ones

# Simple mode: frontend shows only 'uri' field
# Advanced mode: frontend shows 'host', 'port', 'username', etc.

# Backend processes based on which fields are present
if "uri" in result:
    # Simple mode
    uri = result["uri"]
else:
    # Advanced mode - build URI from components
    uri = build_mongodb_uri(
        host=result["host"],
        port=result["port"],
        username=result.get("username"),
        password=result.get("password")
    )
```

## Validation System

### Field-Level Validation

Defined in `FormField.validation`:

```python
validation=ValidationRule(
    pattern=r"^mongodb://.*",
    message="Must start with mongodb://",
    min=10,  # For numbers: minimum value
    max=100  # For numbers: maximum value
)
```

**Frontend Validation:**
- Runs on input change
- Shows inline error messages
- Prevents submission if invalid
- Emits `valid`/`invalid` events

**Backend Validation:**
- Additional validation after form submission
- Can return errors to frontend
- Pydantic model validation

### Form-Level Validation

Defined in `TerminalForm.vue`:

```typescript
const canSubmit = computed(() => {
  // All required fields must have values
  const requiredFieldsValid = formFields.value.every(field => {
    if (!field.required) return true
    
    const value = formData.value[field.id]
    
    // Checkbox-list: array must have at least 1 item
    if (field.type === 'checkbox-list') {
      return Array.isArray(value) && value.length > 0
    }
    
    // Other fields: must be non-empty
    return value !== null && value !== undefined && value !== ''
  })
  
  // All fields must be valid (no validation errors)
  const allFieldsValid = invalidFields.value.size === 0
  
  return requiredFieldsValid && allFieldsValid && !isSubmitting.value
})
```

### Custom Validation

Add custom validation in field components:

```typescript
const validate = (value: any) => {
  // Required field check
  if (props.field.required && !value) {
    errorMessage.value = 'This field is required'
    emit('invalid')
    return false
  }
  
  // Custom validation logic
  if (props.field.id === 'email' && !isValidEmail(value)) {
    errorMessage.value = 'Invalid email address'
    emit('invalid')
    return false
  }
  
  // Pattern validation
  if (props.field.validation?.pattern) {
    const regex = new RegExp(props.field.validation.pattern)
    if (!regex.test(value)) {
      errorMessage.value = props.field.validation.message
      emit('invalid')
      return false
    }
  }
  
  // Min/max for numbers
  if (props.field.type === 'number') {
    const num = Number(value)
    if (props.field.min !== undefined && num < props.field.min) {
      errorMessage.value = `Minimum value is ${props.field.min}`
      emit('invalid')
      return false
    }
    if (props.field.max !== undefined && num > props.field.max) {
      errorMessage.value = `Maximum value is ${props.field.max}`
      emit('invalid')
      return false
    }
  }
  
  errorMessage.value = ''
  emit('valid')
  return true
}
```

## Styling Guidelines

### Terminal Color Scheme (Gruvbox-inspired)

```css
/* Background colors */
--gb-bg-hard: #1d2021      /* Darkest background */
--gb-bg: #282828            /* Normal background */
--gb-bg-soft: #32302f       /* Lighter background */

/* Foreground colors */
--gb-fg: #ebdbb2            /* Normal text */
--gb-fg-dim: #a89984        /* Dimmed text */
--gb-gray: #928374          /* Gray text/borders */

/* Accent colors */
--gb-red: #fb4934
--gb-green: #b8bb26
--gb-yellow: #fabd2f
--gb-blue: #83a598
--gb-purple: #d3869b
--gb-aqua: #8ec07c
--gb-orange: #fe8019
```

### Component Styling Pattern

```css
/* Container */
.terminal-field {
  margin-bottom: 1rem;
  font-family: 'JetBrains Mono', monospace;
}

/* Labels */
.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gb-fg);
  margin-bottom: 0.5rem;
}

/* Inputs */
.field-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--gb-bg);
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  border-radius: 4px;
  transition: border-color 0.2s;
}

.field-input:focus {
  outline: none;
  border-color: var(--gb-blue);
  background: var(--gb-bg-soft);
}

.field-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Help text */
.field-help {
  font-size: 12px;
  color: var(--gb-fg-dim);
  margin-top: 0.25rem;
  line-height: 1.4;
}

/* Error messages */
.field-error {
  font-size: 12px;
  color: var(--gb-red);
  margin-top: 0.25rem;
  font-weight: 500;
}

/* Success state */
.field-success {
  border-color: var(--gb-green);
}

/* Buttons */
.terminal-button {
  padding: 0.5rem 1rem;
  background: var(--gb-bg-soft);
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.terminal-button:hover {
  background: var(--gb-bg);
  border-color: var(--gb-fg-dim);
}

.terminal-button.primary {
  background: var(--gb-blue);
  border-color: var(--gb-blue);
  color: var(--gb-bg-hard);
}

.terminal-button.danger {
  background: var(--gb-red);
  border-color: var(--gb-red);
  color: var(--gb-bg-hard);
}
```

### Responsive Design

Forms should work on mobile and desktop:

```css
@media (max-width: 768px) {
  .field-label {
    font-size: 13px;
  }
  
  .field-input {
    font-size: 13px;
    padding: 0.4rem 0.6rem;
  }
  
  .field-help,
  .field-error {
    font-size: 11px;
  }
  
  .terminal-button {
    font-size: 13px;
    padding: 0.4rem 0.8rem;
  }
}
```

## Examples

### Simple Text Form

```python
# Backend
GREETING_FORM = FormSchema(
    title="Enter Your Name",
    description="Tell us who you are",
    fields=[
        FormField(
            id="name",
            label="Your Name",
            type="text",
            required=True,
            placeholder="John Doe",
            help_text="Enter your full name"
        )
    ],
    actions=[
        FormAction(label="Submit", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
```

### Multi-Select with Metadata

```python
# Backend
SELECT_DATABASES_FORM = FormSchema(
    title="Select Databases to Backup",
    description="Choose one or more databases",
    fields=[
        FormField(
            id="databases",
            label="Databases",
            type="checkbox-list",
            required=True,
            help_text="Select databases to include in backup",
            options=[
                SelectOption(
                    value="users",
                    label="users",
                    description="User data database",
                    metadata={
                        "size": "1.2 GB",
                        "collections": "5",
                        "documents": "10,245"
                    }
                ),
                SelectOption(
                    value="products",
                    label="products",
                    description="Product catalog",
                    metadata={
                        "size": "856 MB",
                        "collections": "3",
                        "documents": "5,432"
                    }
                )
            ]
        )
    ],
    actions=[
        FormAction(label="Create Backup", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
```

### Form with Validation

```python
# Backend
CONNECTION_FORM = FormSchema(
    title="Add Connection",
    fields=[
        FormField(
            id="name",
            label="Name",
            type="text",
            required=True,
            validation=ValidationRule(
                pattern=r"^[a-zA-Z0-9_-]+$",
                message="Only alphanumeric, dash, and underscore allowed"
            )
        ),
        FormField(
            id="port",
            label="Port",
            type="number",
            required=True,
            min=1,
            max=65535,
            default=27017
        ),
        FormField(
            id="password",
            label="Password",
            type="password",
            required=False,
            help_text="Leave empty for no authentication"
        )
    ],
    actions=[
        FormAction(label="Connect", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
```

## Troubleshooting

### Form Not Displaying

**Problem:** Form doesn't appear in terminal after command execution.

**Solutions:**
1. Check WebSocket connection: `isConnected` should be true
2. Verify form is registered in `FORM_REGISTRY` (`backend/app/routers/forms.py`)
3. Check browser console for errors
4. Verify FormManager is sending form via WebSocket
5. Check that CLI command is using `get_websocket_context()` and `get_form_manager()`

### Form Data Not Submitting

**Problem:** Clicking submit doesn't send data to backend.

**Solutions:**
1. Check that all required fields are filled
2. Verify no validation errors (red error messages)
3. Check browser console for WebSocket errors
4. Verify `submitForm()` is called correctly
5. Check backend FormManager receives `form_submit` message

### Checkbox List Not Working

**Problem:** Checkbox list field doesn't accept selections.

**Solutions:**
1. Verify `options` array is populated in form schema
2. Check that `modelValue` is initialized as empty array `[]`
3. Verify `update:modelValue` emits array, not single value
4. Check that validation allows empty array for non-required fields
5. Ensure `getFieldComponent()` returns `TerminalCheckboxListField`

### Validation Errors Not Showing

**Problem:** Invalid input doesn't show error messages.

**Solutions:**
1. Verify `ValidationRule` is defined in backend schema
2. Check that field component emits `invalid` event
3. Verify error message is set in component's `errorMessage` ref
4. Check CSS: `.field-error` should be visible
5. Ensure validation runs on input change

### Form Timeout

**Problem:** Form times out after 5 minutes.

**Solutions:**
1. This is expected behavior (prevents abandoned forms)
2. User should resubmit the command to get a new form
3. If needed, increase timeout in `FormManager.request_form()` (line 52):
   ```python
   result = await asyncio.wait_for(future, timeout=600)  # 10 minutes
   ```

### Styling Issues

**Problem:** Form doesn't match terminal theme.

**Solutions:**
1. Verify CSS uses Gruvbox color variables (`--gb-*`)
2. Check that `scoped` styles aren't being overridden
3. Use browser dev tools to inspect element styles
4. Ensure font-family is 'JetBrains Mono' for consistency
5. Check that dark mode colors are used (not light mode)

## Best Practices

1. **Always validate on both frontend and backend**
   - Frontend: instant feedback, better UX
   - Backend: security, data integrity

2. **Use meaningful help text**
   - Explain field purpose
   - Show examples
   - Clarify requirements

3. **Populate options dynamically**
   - Fetch from database
   - Include metadata for context
   - Sort logically (alphabetical, by date, etc.)

4. **Handle errors gracefully**
   - Show clear error messages
   - Provide actionable feedback
   - Don't crash on invalid input

5. **Test all scenarios**
   - Empty form submission
   - Invalid input
   - Form cancellation
   - WebSocket disconnection
   - Multiple forms simultaneously

6. **Keep forms focused**
   - One form = one task
   - Don't overload with too many fields
   - Use multi-step forms for complex flows

7. **Follow terminal aesthetics**
   - Monospace fonts
   - Terminal color scheme
   - Minimalist design
   - Keyboard-friendly (Enter to submit, Esc to cancel)

8. **Document your forms**
   - Add to `TERMINAL_FORMS` config
   - Register in `FORM_REGISTRY`
   - Create backend schema
   - Update this documentation

---

**Last Updated:** 2026-02-17
**Version:** 1.1.4
