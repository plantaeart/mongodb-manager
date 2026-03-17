# 10 - Stepper Forms Reference

Quick reference for multi-step (stepper) forms. For full implementation guide see [09-form-implementation-guide.md](09-form-implementation-guide.md).

---

## Data Flow

```
User runs command
  → useTerminal fetches GET /api/forms/{path}
  → Backend returns FormSchema with step + total_steps
  → useTerminal builds FormRequestMessage (includes command, step, total_steps)
  → TerminalForm.vue detects step/total_steps → loads TerminalFormStepper
  → Stepper calls loadData() per step (subsequent GET requests)
  → Final step submits via useTerminal.submitForm()
```

---

## Key Files

| File | Role |
|------|------|
| `backend/app/core/form_definitions.py` | Form schemas with `step` / `total_steps` |
| `backend/app/routers/forms.py` | HTTP GET/POST endpoints per step |
| `frontend/app/composables/useTerminal.ts` | Fetches form, builds `FormRequestMessage` |
| `frontend/app/config/terminalForms.ts` | Maps commands → API paths |
| `frontend/app/config/stepperRegistry.ts` | Maps commands → stepper configs |
| `frontend/app/config/steppers/*.ts` | Per-command stepper definitions |
| `frontend/app/components/Terminal/Forms/TerminalForm.vue` | Detects stepper, delegates rendering |
| `frontend/app/components/Terminal/Forms/TerminalFormStepper.vue` | Stepper UI + navigation logic |

---

## Backend — Form Schema

```python
# form_definitions.py
class FormSchema(BaseModel):
    title: str
    description: str | None = None
    step: int | None = None          # 1-indexed step number
    total_steps: int | None = None   # total steps in flow
    fields: list[FormField]
    actions: list[FormAction]

# Step 1 of 2 example
MY_FORM_STEP1 = FormSchema(
    title="Select Connection",
    description="Choose the connection to update",
    step=1,
    total_steps=2,
    fields=[...],
    actions=[FormAction(label="Next", style="primary", action="next")]
)
```

**Serialization rule:** multi-step endpoints must use `.model_dump()` (NOT `.model_dump(exclude_none=True)`) so `step` and `total_steps` are never stripped.

```python
# forms.py — correct for multi-step endpoints
return MY_FORM_STEP1.model_dump()      # ✅ preserves step/total_steps

# Wrong — silently drops step/total_steps when they're integers
return MY_FORM_STEP1.model_dump(exclude_none=True)  # ❌
```

---

## Frontend — Command Registration

**1. Register API paths** (`terminalForms.ts`):
```ts
export const COMMAND_TO_API_PATH: Record<string, string> = {
  'my command': 'my/command/step1',   // Step 1 GET path
}
export const COMMAND_TO_POST_API_PATH: Record<string, string> = {
  'my command': 'my/command/step2',   // Final step POST path
}
```

**2. Register stepper config** (`stepperRegistry.ts`):
```ts
import { createMyCommandStepper } from './steppers/myCommand'

export function getStepperConfig(command: string, formId: string) {
  switch (command) {
    case 'my command': return createMyCommandStepper(formId)
    // ...
  }
}
```

---

## Stepper Config (`steppers/myCommand.ts`)

```ts
import type { StepperFormConfig, StepDefinition } from '~/types/stepper'
import { createStep } from '~/types/stepper'

export function createMyCommandStepper(formId: string): StepperFormConfig {
  const step1: StepDefinition = {
    ...createStep('step1_id', 'Step 1 Title', 'Step 1 description', 'i-lucide-database'),
    // Optional: override with custom Vue component name
    // component: 'CommandsMyCommandStep1',
    loadData: async (allSteps, context) => {
      const schema = await $fetch(`${context.baseUrl}/api/forms/my/command/step1`, {
        headers: { Authorization: `Bearer ${context.token}` }
      })
      allSteps[0].formData = schema as any
    },
    validate: (data, allSteps) => !!data.selected_value
  }

  const step2: StepDefinition = {
    ...createStep('step2_id', 'Step 2 Title', 'Step 2 description', 'i-lucide-settings'),
    loadData: async (allSteps, context) => {
      const schema = await $fetch(`${context.baseUrl}/api/forms/my/command/step2`, {
        headers: { Authorization: `Bearer ${context.token}` }
      })
      allSteps[1].formData = schema as any
      // Optionally pre-populate from step 1 data:
      allSteps[1].data = { name: allSteps[0].data.selected_value }
    },
    validate: (data, allSteps) => !!data.name && !!data.host
  }

  return {
    formId,
    command: 'my command',
    steps: [step1, step2],
    onSubmit: async (allData) => { /* optional pre-submit hook */ }
  }
}
```

---

## StepDefinition Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique step identifier |
| `config.title` | `string` | Step label shown in stepper UI |
| `config.description` | `string` | Step subtitle |
| `config.icon` | `string` | Iconify icon name |
| `config.disabled` | `boolean?` | Force-disable step tab |
| `component` | `string?` | Custom Vue component name (from registry) |
| `loadData` | `async fn?` | Fetches form schema + pre-populates data |
| `validate` | `fn` | Returns `true` if step is valid |
| `formData` | `FormRequestMessage?` | Set by `loadData`, drives field rendering |
| `data` | `Record<string, any>` | Current field values for this step |
| `errors` | `Record<string, string>` | Field validation errors |
| `isLoading` | `boolean` | Loading spinner state |

---

## Custom Step Components

For steps needing custom UI (e.g. mode toggles), register a Vue component:

**1. Create the component** in `components/Commands/MyCommand/Step1.vue`  
**2. Register it** in `TerminalFormStepper.vue`:
```ts
import MyStep1 from '~/components/Commands/MyCommand/Step1.vue'

const customComponentRegistry = {
  CommandsMyCommandStep1: MyStep1,
  // ...
}
```
**3. Reference by name** in the stepper config:
```ts
component: 'CommandsMyCommandStep1'
```

The custom component receives `:step`, `:config`, `:disabled`, `:readonly` props and emits `@update:data` / `@update:errors`.

---

## How Detection Works

`TerminalForm.vue` checks `formData.step && formData.total_steps` to decide whether to render the stepper. The `command` field (set by `useTerminal`) is used to look up the correct stepper config — no fragile title matching.

```
formData.step=1, total_steps=2, command='connect update'
  → getStepperConfig('connect update', formId)
  → TerminalFormStepper rendered
```

---

## Existing Multi-Step Commands

| Command | Step 1 GET | Step 2 GET | POST |
|---------|-----------|-----------|------|
| `connect update` | `connect/update/select` | `connect/update/details` | WebSocket |
| `backup folder add` | `backup/folder/add/configure` | `backup/folder/add/select` | `backup/folder/add/configure` |
| `backup create` | `backup/create/select` | `backup/create/configure` | `backup/create/configure` |
| `backup restore` | `backup/restore/select` | `backup/restore/configure` | `backup/restore/configure` |

---

## Related Docs

- [07 - Terminal Forms System](07-terminal-forms.md)
- [09 - Form Implementation Guide](09-form-implementation-guide.md)
