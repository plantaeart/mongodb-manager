<template>
  <!-- Stepper Form (for multi-step forms like connect update) -->
  <TerminalFormStepper
    v-if="stepperConfig"
    :config="stepperConfig"
    :readonly="readonly"
    :status="status"
    :submit-button-text="getSubmitButtonText()"
    @submit="handleStepperSubmit"
    @cancel="handleCancel"
  />
  
  <!-- Regular Form (single-step forms) -->
  <div v-else class="terminal-form" :class="{ 'readonly': isReadonly }">
    <!-- Header -->
    <div class="form-header">
      <div class="form-header-title">
        <h3>{{ formData.title }}</h3>
        <UBadge v-if="formData.step && formData.total_steps" color="primary" variant="subtle" size="sm" class="step-badge">
          Step {{ formData.step }} of {{ formData.total_steps }}
        </UBadge>
      </div>
      <p v-if="formData.description">{{ formData.description }}</p>
    </div>
    
    <!-- Fields -->
    <div class="form-body" :class="{ 'two-columns': shouldUseTwoColumns }">
      <component
        v-for="field in displayedFields"
        :key="field.id"
        :is="getFieldComponent(field)"
        :field="field"
        v-model="fieldValues[field.id]"
        :disabled="isSubmitting"
        :readonly="isReadonly"
        @blur="handleFieldBlur(field.id)"
        @valid="handleFieldValid(field.id)"
        @invalid="handleFieldInvalid(field.id, $event)"
        @enter="handleEnter"
      />
    </div>
    
    <!-- Actions (hidden in readonly) -->
    <TerminalFormActions
      v-if="!isReadonly"
      :actions="formData.actions"
      :can-submit="canSubmit"
      :is-submitting="isSubmitting"
      @submit="handleSubmit"
      @cancel="handleCancel"
    />
    
    <!-- Status (shown in readonly) -->
    <div v-if="isReadonly" class="form-status">
      <span v-if="status === CommandStatus.ERROR" class="status-cancelled">
        ✗ Cancelled
      </span>
      <span v-else-if="status === CommandStatus.SUCCESS" class="status-submitted">
        ✓ Submitted
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import TerminalTextField from './Fields/TerminalTextField.vue'
import TerminalPasswordField from './Fields/TerminalPasswordField.vue'
import TerminalNumberField from './Fields/TerminalNumberField.vue'
import TerminalCheckboxField from './Fields/TerminalCheckboxField.vue'
import TerminalCheckboxListField from './Fields/TerminalCheckboxListField.vue'
import TerminalReadonlyField from './Fields/TerminalReadonlyField.vue'
import TerminalListField from './Fields/TerminalListField.vue'
import TerminalSelectField from './Fields/TerminalSelectField.vue'
import TerminalFormActions from './TerminalFormActions.vue'
import TerminalFormStepper from './TerminalFormStepper.vue'
import type { FormRequestMessage, FormField } from '~/types/terminal'
import { CommandStatus } from '~/enums'
import { getStepperConfig } from '~/config/stepperRegistry'

interface Props {
  formData: FormRequestMessage
  formId: string
  readonly?: boolean
  status?: CommandStatus
}

const props = defineProps<Props>()
const emit = defineEmits<{
  submit: [data: Record<string, any>]
  cancel: []
}>()

// Detect if this is a stepper form and get its config
const stepperConfig = computed(() => {
  // Check if this is a multi-step form
  if (props.formData.step && props.formData.total_steps) {
    // Use the command field directly (set by useTerminal when form was fetched)
    const command = props.formData.command || null
    
    if (command) {
      const config = getStepperConfig(command, props.formId)
      
      if (config && config.steps[0]) {
        // Initialize the current step with the provided formData
        const stepIndex = (props.formData.step || 1) - 1
        
        if (config.steps[stepIndex]) {
          config.steps[stepIndex].formData = props.formData
          return config
        }
      }
    }
  }
  
  return null
})

// State - MUST be declared before watch statements that reference them
const fieldValues = ref<Record<string, any>>({})
const fieldErrors = ref<Record<string, string>>({})
const isSubmitting = ref(false)
const isReadonly = computed(() => 
  props.readonly || props.status === CommandStatus.SUCCESS || props.status === CommandStatus.ERROR
)

// Detect if this is a read-only form (all fields are readonly)
const isReadOnlyForm = computed(() => {
  return props.formData.fields.every(f => f.type === 'readonly')
})

// Two-column layout for forms with many fields
const shouldUseTwoColumns = computed(() => {
  return props.formData.fields.length > 4
})

// Show all fields (no filtering)
const displayedFields = computed(() => {
  return props.formData.fields
})

// Get appropriate component for field type
const getFieldComponent = (field: FormField) => {
  switch (field.type) {
    case 'password':
      return TerminalPasswordField
    case 'number':
      return TerminalNumberField
    case 'checkbox':
      return TerminalCheckboxField
    case 'checkbox-list':
      return TerminalCheckboxListField
    case 'readonly':
      return TerminalReadonlyField
    case 'list':
      return TerminalListField
    case 'textarea':
      // TODO: Create TerminalTextAreaField when needed
      return TerminalTextField
    case 'select':
      return TerminalSelectField
    default:
      return TerminalTextField
  }
}

// Timeout warning (5 min timeout, warn at 4 min = 240 seconds)
const FORM_TIMEOUT = 300 * 1000 // 5 minutes in ms
const WARNING_TIME = 240 * 1000 // 4 minutes in ms
let timeoutWarningTimer: NodeJS.Timeout | null = null

// Initialize field values with defaults
watch(() => props.formData, (formData) => {
  formData.fields.forEach(field => {
    if (field.default !== undefined && fieldValues.value[field.id] === undefined) {
      fieldValues.value[field.id] = field.default
    }
  })
}, { immediate: true })

// Unified validation for all forms
const canSubmit = computed(() => {
  // Read-only forms cannot be submitted
  if (isReadOnlyForm.value) {
    return false
  }
  
  // Require all required fields
  const requiredFields = props.formData.fields.filter(f => f.required)
  const allRequiredFilled = requiredFields.every(f => {
    const value = fieldValues.value[f.id]
    // For checkbox-list fields (arrays), check if at least one item is selected
    if (f.type === 'checkbox-list' && Array.isArray(value)) {
      return value.length > 0
    }
    // For other fields, check if value exists and is not empty
    return value !== undefined && value !== ''
  })
  
  const hasErrors = Object.keys(fieldErrors.value).length > 0
  return allRequiredFilled && !hasErrors && !isSubmitting.value
})

// Handlers
const handleFieldBlur = (fieldId: string) => {
  // Validation happens in field component
}

const handleFieldValid = (fieldId: string) => {
  delete fieldErrors.value[fieldId]
}

const handleFieldInvalid = (fieldId: string, error: string) => {
  fieldErrors.value[fieldId] = error
}

const handleEnter = () => {
  // Enter on last field submits form if valid
  if (canSubmit.value) {
    handleSubmit('submit')
  }
}

const handleSubmit = async (action: string) => {
  if (!canSubmit.value) return
  
  isSubmitting.value = true
  
  // Submit all field values
  const submitData = { ...fieldValues.value }
  
  emit('submit', submitData)
}

const handleStepperSubmit = (data: Record<string, any>) => {
  // Stepper already prepared the data, just emit it
  emit('submit', data)
}

const handleCancel = () => {
  emit('cancel')
}

// Get submit button text based on command
const getSubmitButtonText = (): string => {
  if (!stepperConfig.value) return 'Submit'
  
  const command = stepperConfig.value.command
  if (command === 'connect update') {
    return 'Update Connection'
  }
  
  // Add more command-specific labels here
  return 'Submit'
}

// Keyboard shortcuts
const handleKeydown = (event: KeyboardEvent) => {
  // Ctrl+Enter or Cmd+Enter: Submit form
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    if (canSubmit.value && !isReadonly.value) {
      handleSubmit('submit')
    }
  }
  
  // Escape: Cancel form
  if (event.key === 'Escape') {
    event.preventDefault()
    if (!isReadonly.value) {
      handleCancel()
    }
  }
}

// Mount/unmount keyboard listeners
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  
  // Set timeout warning
  if (!isReadonly.value) {
    timeoutWarningTimer = setTimeout(() => {
      // Form will timeout in 1 minute
      // You could show a toast notification here if you have a toast system
    }, WARNING_TIME)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  
  // Clear timeout warning timer
  if (timeoutWarningTimer) {
    clearTimeout(timeoutWarningTimer)
    timeoutWarningTimer = null
  }
})
</script>

<style scoped>
.terminal-form {
  background: var(--color-bg-primary, #1d2021);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  padding: 16px;
  margin: 12px 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.terminal-form.readonly {
  opacity: 0.7;
  pointer-events: none;
}

.form-header {
  border-bottom: 1px solid var(--color-border-secondary, #504945);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.form-header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.form-header h3 {
  color: var(--color-primary, #83a598);
  font-size: 16px;
  margin: 0;
  font-weight: 600;
}

.step-badge {
  font-size: 11px;
  font-weight: 500;
}

.form-header p {
  color: var(--color-text-tertiary, #928374);
  font-size: 13px;
  margin: 0;
}

.form-mode-toggle {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.mode-button {
  padding: 8px 16px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
}

.mode-button:hover {
  background: var(--color-bg-secondary, #3c3836);
}

.mode-button.active {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
  border-color: var(--color-primary, #83a598);
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-body.two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-status {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-secondary, #504945);
  font-size: 13px;
}

.status-cancelled {
  color: var(--color-warning, #fe8019);
}

.status-submitted {
  color: var(--color-success, #b8bb26);
}

@media (max-width: 768px) {
  .terminal-form {
    padding: 12px;
  }
}
</style>
