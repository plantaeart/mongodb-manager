# 09 - Form Implementation Guide

This document provides a comprehensive guide to creating terminal forms in the MongoDB Manager application, covering both single-step and multi-step (stepper) forms.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Single-Step Forms](#single-step-forms)
3. [Multi-Step Forms (Steppers)](#multi-step-forms-steppers)
4. [Field Types](#field-types)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)

---

## System Architecture

### Overview

The form system follows a **backend-as-source-of-truth** architecture:

```
User Command → Frontend Maps to API Path → Backend Returns Form Schema → Frontend Renders
```

### Key Components

**Backend:**
- `app/core/form_definitions.py` - Form schema definitions
- `app/routers/forms.py` - Form API endpoints

**Frontend:**
- `app/config/terminalForms.ts` - Command-to-API mapping
- `app/components/Terminal/Forms/TerminalForm.vue` - Single-step form renderer
- `app/components/Terminal/Forms/TerminalFormStepper.vue` - Multi-step form renderer
- `app/config/steppers/` - Stepper configurations
- `app/components/Terminal/Forms/Fields/` - Field components

### Data Flow

```
┌─────────────┐
│  User types │
│  "connect   │
│   add"      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│ terminalForms.ts                    │
│ Maps: 'connect add' → 'connect/add' │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ GET /api/forms/connect/add           │
│ Returns FormSchema JSON              │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ TerminalForm.vue                     │
│ Renders fields based on schema       │
└──────────────────────────────────────┘
```

---

## Single-Step Forms

Single-step forms are the simplest form type - one command, one form, one submission.

### Backend Implementation

#### Step 1: Define Form Schema

**File:** `backend/app/core/form_definitions.py`

```python
from app/core/form_models import FormSchema, FormField, FormAction, ValidationRule

# Example: Connection Add Form
CONNECT_ADD_FORM = FormSchema(
    title="Add MongoDB Connection",
    description="Enter connection details",
    fields=[
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
        ),
        FormField(
            id="uri",
            label="MongoDB URI",
            type="text",
            required=True,
            placeholder="mongodb://localhost:27017",
            help_text="Full MongoDB connection string"
        ),
        FormField(
            id="description",
            label="Description",
            type="text",
            required=False,
            placeholder="Optional description",
            help_text="Notes about this connection"
        )
    ],
    actions=[
        FormAction(label="Add Connection", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
```

#### Step 2: Register Form in Registry

**File:** `backend/app/routers/forms.py`

```python
# Add to FORM_REGISTRY
FORM_REGISTRY = {
    "connect/add": CONNECT_ADD_FORM,
    # ... other forms
}
```

#### Step 3: Create GET Endpoint

**File:** `backend/app/routers/forms.py`

The generic GET endpoint handles all forms automatically if they're in the registry.

**Optional:** Add dynamic data population:

```python
@router.get("/{command_path:path}")
async def get_form(
    command_path: str,
    current_user: dict = Depends(get_current_user)
):
    # ... existing code ...
    
    # Special handling for connect/add with dynamic data
    if command_path == "connect/add":
        # Example: populate dropdown options
        form_dict = form_schema.dict(exclude_none=True)
        
        # Add dynamic options to a select field
        for field in form_dict.get("fields", []):
            if field["id"] == "some_select_field":
                field["options"] = [
                    {"value": "opt1", "label": "Option 1"},
                    {"value": "opt2", "label": "Option 2"}
                ]
        
        return form_dict
    
    return form_schema.dict(exclude_none=True)
```

#### Step 4: Create POST Endpoint

**File:** `backend/app/routers/forms.py`

```python
@router.post("/connect/add")
async def submit_connect_add(
    form_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Handle connection add submission"""
    try:
        name = form_data.get("name")
        uri = form_data.get("uri")
        description = form_data.get("description", "")
        
        # Validation
        if not name or not uri:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Business logic
        conn_mgr = ConnectionManager()
        success = conn_mgr.add_connection(name, uri, description)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add connection")
        
        return {
            "success": True,
            "message": f"Connection '{name}' added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Implementation

#### Step 1: Register Command Mapping

**File:** `frontend/app/config/terminalForms.ts`

```typescript
export const COMMAND_TO_API_PATH: Record<string, string> = {
  'connect add': 'connect/add',
  // ... other commands
}
```

That's it! The frontend automatically:
1. Detects the command
2. Fetches the form schema
3. Renders the appropriate fields
4. Submits to the POST endpoint

---

## Multi-Step Forms (Steppers)

Multi-step forms guide users through a sequence of related inputs with validation between steps.

### When to Use Steppers

Use steppers when:
- ✅ The form has distinct logical sections (e.g., select → configure)
- ✅ Early steps influence later steps (e.g., selected item determines available options)
- ✅ You want to show progress visually
- ✅ Each step can be validated independently

### Backend Implementation

#### Step 1: Define Form Schemas (One Per Step)

**File:** `backend/app/core/form_definitions.py`

```python
# Step 1: Select Connection
CONNECT_UPDATE_SELECT_FORM = FormSchema(
    title="Update MongoDB Connection - Step 1",  # MUST include "Step 1"
    description="Select the connection you want to update",
    fields=[
        FormField(
            id="connection_name",
            label="Connection",
            type="select",
            required=True,
            help_text="Choose a connection to update",
            options=[]  # Populated dynamically
        )
    ],
    actions=[
        FormAction(label="Next", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)

# Step 2: Update Details
CONNECT_UPDATE_DETAILS_FORM = FormSchema(
    title="Update MongoDB Connection - Step 2",  # MUST include "Step 2"
    description="Modify connection settings",
    fields=[
        FormField(
            id="name",
            label="Connection Name",
            type="text",
            required=True
        ),
        FormField(
            id="uri",
            label="MongoDB URI",
            type="text",
            required=True
        ),
        # ... more fields
    ],
    actions=[
        FormAction(label="Update Connection", style="primary", action="submit"),
        FormAction(label="Cancel", style="secondary", action="cancel")
    ]
)
```

**🔴 CRITICAL:** Form titles MUST include "Step 1", "Step 2", etc. for detection.

#### Step 2: Register Both Forms

**File:** `backend/app/routers/forms.py`

```python
FORM_REGISTRY = {
    "connect/update/select": CONNECT_UPDATE_SELECT_FORM,   # Step 1
    "connect/update/details": CONNECT_UPDATE_DETAILS_FORM, # Step 2
    # ... other forms
}
```

#### Step 3: Create GET Endpoints (with dynamic data)

**File:** `backend/app/routers/forms.py`

```python
@router.get("/{command_path:path}")
async def get_form(command_path: str, current_user: dict = Depends(get_current_user)):
    # ... existing code ...
    
    # Step 1: Populate connection options
    if command_path == "connect/update/select":
        conn_mgr = ConnectionManager()
        connections = conn_mgr.list_connections()
        
        form_dict = form_schema.dict(exclude_none=True)
        
        # Build options
        options = []
        for conn in connections:
            options.append({
                "value": conn["name"],
                "label": conn["name"],
                "description": conn.get("uri", "")
            })
        
        # Update field
        for field in form_dict.get("fields", []):
            if field["id"] == "connection_name":
                field["options"] = options
                break
        
        return form_dict
    
    # Step 2: Return form structure (data populated by frontend)
    if command_path == "connect/update/details":
        return form_schema.dict(exclude_none=True)
    
    return form_schema.dict(exclude_none=True)
```

#### Step 4: Create POST Endpoint (final submission only)

**File:** `backend/app/routers/forms.py`

```python
@router.post("/connect/update/details")
async def submit_connect_update(
    form_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Handle connection update submission (final step)"""
    try:
        # Get data from ALL steps (frontend combines them)
        connection_name = form_data.get("connection_name")  # From Step 1
        new_name = form_data.get("name")                     # From Step 2
        new_uri = form_data.get("uri")                       # From Step 2
        
        # Validation
        if not connection_name or not new_name or not new_uri:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Business logic
        conn_mgr = ConnectionManager()
        success = conn_mgr.update_connection(connection_name, new_name, new_uri)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update connection")
        
        return {
            "success": True,
            "message": f"Connection updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Implementation

#### Step 1: Register Initial Command Mapping

**File:** `frontend/app/config/terminalForms.ts`

```typescript
export const COMMAND_TO_API_PATH: Record<string, string> = {
  'connect update': 'connect/update/select',  // Maps to Step 1 endpoint
  // ... other commands
}
```

**🔴 CRITICAL:** Map the command to the **Step 1** endpoint.

#### Step 2: Add Pattern Matching

**File:** `frontend/app/config/terminalForms.ts`

```typescript
export function getCommandFromFormTitle(title: string): string | null {
  // Check if title contains "Step 1"
  if (!title.includes('Step 1')) {
    return null
  }
  
  const titleLower = title.toLowerCase()
  
  // Match "Update MongoDB Connection - Step 1"
  if (titleLower.includes('update') && titleLower.includes('connection')) {
    return 'connect update'
  }
  
  // Add more patterns as needed
  
  return null
}
```

#### Step 3: Create Stepper Configuration

**File:** `frontend/app/config/steppers/connectUpdate.ts`

```typescript
import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'

export function createConnectUpdateStepper(formId: string): StepperFormConfig {
  // Step 1: Select Connection
  const step1: StepDefinition = {
    ...createStep(
      'select_connection',
      'Select Connection',
      'Choose which connection to update',
      'i-lucide-database'
    ),
    loadData: async (allSteps, context) => {
      // Fetch form schema for Step 1
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/connect/update/select`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })
      
      // Update step formData
      const currentStep = allSteps[0]
      if (currentStep) {
        currentStep.formData = formSchema as any
      }
    },
    validate: (data, allSteps) => {
      const hasSelection = !!data.connection_name
      const step = allSteps[0]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false
      
      return hasSelection && !hasErrors
    }
  }

  // Step 2: Update Details
  const step2: StepDefinition = {
    ...createStep(
      'update_details',
      'Update Details',
      'Modify connection settings',
      'i-lucide-edit'
    ),
    loadData: async (allSteps, context) => {
      // Get selected connection from Step 1
      const connectionName = allSteps[0]?.data?.connection_name
      
      if (!connectionName) {
        throw new Error('No connection selected')
      }
      
      // Fetch form schema for Step 2
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/connect/update/details`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })
      
      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
      }
      
      // Fetch connection details to pre-populate
      const connectionDetails = await $fetch(`${context.baseUrl}/api/forms/connection-details/${connectionName}`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })
      
      // Pre-populate step data
      if (currentStep) {
        currentStep.data = {
          name: connectionDetails.name,
          uri: connectionDetails.uri,
          description: connectionDetails.description
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[1]
      if (!step) return false
      
      const hasErrors = Object.keys(step.errors).length > 0
      const required = ['name', 'uri']
      const allRequiredFilled = required.every(id => !!data[id])
      
      return allRequiredFilled && !hasErrors
    }
  }

  return {
    formId,
    command: 'connect update',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      // Optional: custom submission logic
      console.log('Submitting:', allData)
    }
  }
}
```

#### Step 4: Register Stepper

**File:** `frontend/app/config/stepperRegistry.ts`

```typescript
import { createConnectUpdateStepper } from './steppers/connectUpdate'

export function getStepperConfig(command: string, formId: string): StepperFormConfig | null {
  switch (command) {
    case 'connect update':
      return createConnectUpdateStepper(formId)
    // ... other steppers
    default:
      return null
  }
}
```

---

## Field Types

### Available Field Types

| Type | Component | Description | Example |
|------|-----------|-------------|---------|
| `text` | TerminalTextField | Text input | Name, URI |
| `password` | TerminalPasswordField | Password input with hide/show | Password |
| `number` | TerminalNumberField | Numeric input | Port number |
| `select` | TerminalSelectField | Dropdown selection | Connection list |
| `checkbox-list` | TerminalCheckboxListField | Multiple selections | Database list |
| `list` | TerminalListField | Display-only list | Backup list |
| `readonly` | TerminalReadonlyField | Display-only text | Status, info |

### Field Definition Structure

```python
FormField(
    id="field_name",              # Unique identifier (snake_case)
    label="Field Label",          # Display label
    type="text",                  # Field type (see table above)
    required=True,                # Is field required?
    default="default value",      # Default value (optional)
    placeholder="Enter value...", # Placeholder text (optional)
    help_text="Helper text",      # Help text below field (optional)
    tooltip="Tooltip text",       # Tooltip on hover (optional)
    validation=ValidationRule(    # Validation rules (optional)
        pattern=r"^[a-z]+$",
        message="Only lowercase letters"
    ),
    options=[                     # Options for select/checkbox-list (optional)
        {
            "value": "opt1",
            "label": "Option 1",
            "description": "Additional info"
        }
    ]
)
```

### Select Field with Rich Options

```python
FormField(
    id="connection_name",
    label="Connection",
    type="select",
    required=True,
    help_text="Select a connection",
    options=[
        {
            "value": "prod-db",
            "label": "Production DB",
            "description": "mongodb://prod.example.com:27017",  # Shows as URI below dropdown
            "metadata": {
                "user_description": "Main production database"
            }
        }
    ]
)
```

---

## Common Patterns

### Pattern 1: Dependent Dropdowns

When Step 2 options depend on Step 1 selection:

```typescript
// In stepper config - Step 2
loadData: async (allSteps, context) => {
  // Get selection from Step 1
  const selectedItem = allSteps[0]?.data?.item_id
  
  // Fetch form with dynamic options based on selection
  const formSchema = await $fetch(
    `${context.baseUrl}/api/forms/step2?item=${selectedItem}`,
    { headers: { 'Authorization': `Bearer ${context.token}` } }
  )
  
  allSteps[1].formData = formSchema as any
}
```

### Pattern 2: Pre-populating Fields

```typescript
// In stepper config
loadData: async (allSteps, context) => {
  // Fetch form schema
  const formSchema = await $fetch(...)
  allSteps[1].formData = formSchema as any
  
  // Fetch existing data
  const existingData = await $fetch(`${context.baseUrl}/api/data/${id}`)
  
  // Pre-populate
  allSteps[1].data = {
    name: existingData.name,
    value: existingData.value
  }
}
```

### Pattern 3: Combining Step Data on Submit

The stepper automatically combines all step data:

```typescript
onSubmit: async (allData) => {
  // allData contains data from ALL steps
  // {
  //   connection_name: "from step 1",
  //   name: "from step 2",
  //   uri: "from step 2"
  // }
}
```

Backend receives all data in the final POST:

```python
@router.post("/final-step")
async def submit(form_data: dict):
    step1_data = form_data.get("field_from_step1")
    step2_data = form_data.get("field_from_step2")
    # Both are available
```

### Pattern 4: Dynamic Field Options

Populate dropdown/checkbox options dynamically:

```python
# Backend
if command_path == "my/form":
    items = get_items_from_db()
    
    form_dict = form_schema.dict(exclude_none=True)
    
    for field in form_dict.get("fields", []):
        if field["id"] == "item_selector":
            field["options"] = [
                {"value": item.id, "label": item.name}
                for item in items
            ]
    
    return form_dict
```

---

## Troubleshooting

### Issue: Stepper Not Activating

**Symptoms:** Form displays as single-step instead of stepper

**Causes:**
1. ✅ Form title doesn't include "Step 1"
2. ✅ Command not mapped in `getCommandFromFormTitle()`
3. ✅ Stepper config not registered in `stepperRegistry.ts`

**Solution:**
```python
# Backend: Ensure title has "Step 1"
title="My Command - Step 1"

# Frontend: Add pattern matching
if titleLower.includes('my') and titleLower.includes('command'):
    return 'my command'

# Frontend: Register stepper
case 'my command':
    return createMyCommandStepper(formId)
```

### Issue: Step 1 Shows "Complete previous steps first"

**Symptoms:** Step 1 is empty with message to complete previous steps

**Causes:**
1. ✅ `config.steps[0].formData` not initialized
2. ✅ `loadData` function not called

**Solution:**

In `TerminalForm.vue`, the stepper must be initialized with the backend form:

```typescript
if (config && config.steps[0]) {
  // CRITICAL: Initialize Step 1 with backend form
  config.steps[0].formData = props.formData
  return config
}
```

### Issue: Wrong Field Component Rendering

**Symptoms:** Select field shows as text input

**Causes:**
1. ✅ Field type is "select" but TerminalSelectField not registered
2. ✅ Missing import in TerminalForm.vue or TerminalFormStepper.vue

**Solution:**

Register in BOTH files:

```typescript
// TerminalForm.vue AND TerminalFormStepper.vue
import TerminalSelectField from './Fields/TerminalSelectField.vue'

const getFieldComponent = (field: FormField) => {
  switch (field.type) {
    case 'select':
      return TerminalSelectField
    // ...
  }
}
```

### Issue: Step 2 Not Loading

**Symptoms:** Can't proceed to Step 2, button disabled

**Causes:**
1. ✅ Step 1 validation failing
2. ✅ Required fields empty
3. ✅ `validate` function returning false

**Solution:**

Check validation logic:

```typescript
validate: (data, allSteps) => {
  // Ensure all required fields are filled
  const hasSelection = !!data.field_name
  const step = allSteps[0]
  const hasErrors = step ? Object.keys(step.errors).length > 0 : false
  
  console.log('Validation:', { hasSelection, hasErrors })  // Debug
  
  return hasSelection && !hasErrors
}
```

### Issue: Backend Returns Wrong Form

**Symptoms:** Step shows wrong fields

**Causes:**
1. ✅ Form registry has wrong mapping
2. ✅ Command path doesn't match

**Solution:**

Verify mapping:

```python
# Backend: forms.py
FORM_REGISTRY = {
    "my/command/step1": MY_COMMAND_STEP1_FORM,  # Must match
    "my/command/step2": MY_COMMAND_STEP2_FORM
}
```

```typescript
// Frontend: stepper config
await $fetch(`${context.baseUrl}/api/forms/my/command/step1`)  // Must match
```

---

## Checklist

### Creating a Single-Step Form

**Backend:**
- [ ] Define `FormSchema` in `form_definitions.py`
- [ ] Add to `FORM_REGISTRY` in `forms.py`
- [ ] Create POST endpoint in `forms.py`
- [ ] Add dynamic data population if needed (in GET handler)

**Frontend:**
- [ ] Add command mapping in `terminalForms.ts`

### Creating a Multi-Step Form

**Backend:**
- [ ] Define `FormSchema` for EACH step (with "Step 1", "Step 2" in titles)
- [ ] Add ALL step forms to `FORM_REGISTRY`
- [ ] Create POST endpoint for FINAL step
- [ ] Add dynamic data population for each step (in GET handler)

**Frontend:**
- [ ] Map command to Step 1 endpoint in `terminalForms.ts`
- [ ] Add pattern matching in `getCommandFromFormTitle()`
- [ ] Create stepper config file in `config/steppers/`
  - [ ] Define `loadData` for each step
  - [ ] Define `validate` for each step
  - [ ] Define `onSubmit` handler
- [ ] Register stepper in `stepperRegistry.ts`
- [ ] Ensure field components are imported in TerminalFormStepper.vue

---

## Best Practices

1. **✅ Always use descriptive field IDs** (snake_case)
2. **✅ Include help_text for complex fields**
3. **✅ Validate on both frontend and backend**
4. **✅ Use appropriate field types** (don't use text for everything)
5. **✅ Pre-populate fields when editing** (better UX)
6. **✅ Show loading states** during async operations
7. **✅ Provide clear error messages**
8. **✅ Test with empty/invalid data**
9. **✅ Use constants for repeated values** (like `BACKUP_FOLDER_SUFFIX`)
10. **✅ Follow existing patterns** (check similar forms first)

---

## Reference Examples

- **Single-step:** `connect add` - Simple connection creation
- **Multi-step:** `connect update` - Select then edit pattern
- **Multi-step:** `backup folder add` - Configure then select pattern

---

**Questions? Check these files:**
- Backend schemas: `backend/app/core/form_definitions.py`
- Backend endpoints: `backend/app/routers/forms.py`
- Frontend mapping: `frontend/app/config/terminalForms.ts`
- Stepper example: `frontend/app/config/steppers/connectUpdate.ts`
