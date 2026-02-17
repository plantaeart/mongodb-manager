# Generic Stepper Form System

A reusable, data-driven multi-step form system for terminal commands.

## Overview

The generic stepper system allows you to create N-step forms with custom validation, lazy data loading, and flexible rendering. Steps are defined as configuration objects, making it easy to add new multi-step workflows.

## Architecture

```
frontend/app/
├── types/
│   └── stepper.ts                    # Type definitions
├── config/
│   ├── stepperRegistry.ts            # Command → Config mapping
│   └── steppers/
│       ├── connectUpdate.ts          # 2-step: connect update
│       ├── backupCreate.ts           # 3-step: backup create (example)
│       └── _example.ts               # Documentation examples
└── components/Terminal/Forms/
    ├── TerminalFormStepper.vue       # Generic stepper component
    └── TerminalCustomStepper.vue       # UI stepper (circles, lines)
```

## Core Concepts

### 1. Step Definition

Each step is defined by a `StepDefinition` object:

```typescript
interface StepDefinition {
  id: string                          // Unique identifier
  config: StepConfig                  // UI configuration (title, icon, etc.)
  formData?: FormRequestMessage       // Form schema (can be lazy-loaded)
  data: Record<string, any>           // Step's form data
  errors: Record<string, string>      // Validation errors
  isLoading: boolean                  // Loading state
  validate?: (data, allSteps) => boolean        // Custom validation
  loadData?: (allSteps, context) => Promise<void>  // Lazy data loading
  component?: string                  // Custom component (optional)
}
```

### 2. Stepper Configuration

A complete stepper is defined by `StepperFormConfig`:

```typescript
interface StepperFormConfig {
  formId: string
  command: string
  steps: StepDefinition[]
  onSubmit?: (allData) => Promise<void>
  onCancel?: () => void
}
```

### 3. Step Context

Context passed to step handlers:

```typescript
interface StepContext {
  currentStepIndex: number
  totalSteps: number
  token: string                       // Auth token
  baseUrl: string                     // API base URL
  goToStep: (index: number) => void
  next: () => void
  prev: () => void
}
```

## Creating a New Stepper

### Step 1: Define Your Steps

Create `frontend/app/config/steppers/yourCommand.ts`:

```typescript
import { createStep } from '~/types/stepper'
import type { StepDefinition, StepperFormConfig } from '~/types/stepper'

export function createYourCommandStepper(formId: string): StepperFormConfig {
  // Step 1: Selection
  const step1: StepDefinition = {
    ...createStep(
      'step1_id',
      'Step 1 Title',
      'Step 1 description',
      'i-lucide-database'
    ),
    validate: (data, allSteps) => {
      // Return true if step is valid
      return !!data.selectedItem
    }
  }

  // Step 2: Configuration (with lazy loading)
  const step2: StepDefinition = {
    ...createStep(
      'step2_id',
      'Step 2 Title',
      'Step 2 description',
      'i-lucide-settings'
    ),
    loadData: async (allSteps, context) => {
      // Fetch form schema
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/your/endpoint`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })
      
      // Update current step
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema
        currentStep.data = { /* default values */ }
      }
    },
    validate: (data) => {
      return !!data.requiredField
    }
  }

  // Step 3: Review
  const step3: StepDefinition = {
    ...createStep('step3_id', 'Review', 'Confirm', 'i-lucide-check'),
    component: 'YourCustomReviewComponent',  // Optional custom component
    validate: (data) => !!data.confirmed
  }

  return {
    formId,
    command: 'your command',
    steps: [step1, step2, step3]
  }
}
```

### Step 2: Register in Stepper Registry

Add to `frontend/app/config/stepperRegistry.ts`:

```typescript
import { createYourCommandStepper } from './steppers/yourCommand'

export function getStepperConfig(command: string, formId: string): StepperFormConfig | null {
  switch (command) {
    case 'your command':
      return createYourCommandStepper(formId)
    
    // ... other commands
    
    default:
      return null
  }
}
```

### Step 3: Done!

The `TerminalFormStepperGeneric` component automatically handles:
- ✅ Step navigation (Next/Previous buttons)
- ✅ Validation (disables Next until valid)
- ✅ Lazy data loading (calls `loadData` when navigating to step)
- ✅ Form field rendering (auto-renders fields from schema)
- ✅ Submit logic (collects all step data)
- ✅ Loading states
- ✅ Error handling

## Features

### Automatic Field Rendering

By default, steps render fields from `formData.fields`:

```typescript
const step: StepDefinition = {
  ...createStep('my_step', 'My Step', 'Description'),
  // formData will be loaded via loadData or provided upfront
  // Fields automatically render based on type (text, password, number, checkbox-list)
}
```

### Custom Components

For complex UIs (like review screens), use a custom component:

```typescript
const step: StepDefinition = {
  ...createStep('review', 'Review', 'Confirm'),
  component: 'MyReviewComponent'
}
```

Your component receives:

```vue
<template>
  <div>
    <h3>Review Your Submission</h3>
    <!-- Custom UI here -->
  </div>
</template>

<script setup>
const props = defineProps<{
  step: StepDefinition
  config: StepperFormConfig
  disabled: boolean
  readonly: boolean
}>()

const emit = defineEmits<{
  'update:data': [Record<string, any>]
  'update:errors': [Record<string, string>]
}>()
</script>
```

### Lazy Data Loading

Steps can load data only when navigated to:

```typescript
loadData: async (allSteps, context) => {
  // Access previous step data
  const selection = allSteps[0]?.data.selectedItem
  
  // Fetch data based on previous selections
  const details = await $fetch(`${context.baseUrl}/api/items/${selection}`, {
    headers: { 'Authorization': `Bearer ${context.token}` }
  })
  
  // Update current step
  const currentStep = allSteps[1]
  if (currentStep) {
    currentStep.data = details
  }
}
```

### Cross-Step Validation

Validation can access all steps:

```typescript
validate: (data, allSteps) => {
  // Access other step data
  const previousSelection = allSteps[0]?.data.selectedItem
  
  // Validate based on previous selections
  return data.value !== previousSelection
}
```

### Submit All Data

On submit, all step data is merged and emitted:

```typescript
const handleSubmit = () => {
  // Automatically merges: { ...step1.data, ...step2.data, ...step3.data }
  emit('submit', allData)
}
```

## Examples

### 2-Step Form (connect update)

See: `frontend/app/config/steppers/connectUpdate.ts`

```
Step 1: Select connection (checkbox-list)
Step 2: Update details (dynamic form with Simple/Advanced modes)
```

### 3-Step Form (backup create)

See: `frontend/app/config/steppers/_example.ts`

```
Step 1: Select databases
Step 2: Configure backup options (lazy-loaded)
Step 3: Review and confirm (custom component)
```

### 4-Step Form (user register)

See: `frontend/app/config/steppers/_example.ts`

```
Step 1: Basic information
Step 2: Permissions
Step 3: Database access
Step 4: Review
```

## Helper Functions

```typescript
import { 
  createStep,           // Create basic step
  getAllStepData,       // Get merged data from all steps
  isStepValid,          // Check if step is valid
  canProceedFromStep    // Check if can proceed from step
} from '~/types/stepper'
```

## Migration Guide

### From Hardcoded to Generic

**Before (hardcoded for 2 steps):**

```vue
<div v-if="currentStep === 0">Step 1 fields</div>
<div v-if="currentStep === 1">Step 2 fields</div>
```

**After (generic for N steps):**

```typescript
// 1. Create stepper config
const config = createYourCommandStepper(formId)

// 2. Use generic component
<TerminalFormStepperGeneric 
  :config="config"
  @submit="handleSubmit"
  @cancel="handleCancel"
/>
```

## Best Practices

1. **Keep steps focused**: Each step should have a single purpose
2. **Use lazy loading**: Only load data when needed
3. **Validate progressively**: Disable Next button until current step is valid
4. **Provide feedback**: Use loading states and error messages
5. **Make steps independent**: Each step should be self-contained
6. **Use custom components sparingly**: Default field rendering works for most cases

## API Reference

See:
- `frontend/app/types/stepper.ts` - Full type definitions
- `frontend/app/config/stepperRegistry.ts` - Command registry
- `frontend/app/components/Terminal/Forms/TerminalFormStepperGeneric.vue` - Generic component
