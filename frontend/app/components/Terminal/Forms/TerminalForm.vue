<template>
  <div class="terminal-form" :class="{ 'readonly': isReadonly }">
    <!-- Header -->
    <div class="form-header">
      <h3>{{ formData.title }}</h3>
      <p v-if="formData.description">{{ formData.description }}</p>
    </div>
    
    <!-- Mode Toggle (only for connection add form) -->
    <div v-if="isConnectionForm" class="form-mode-toggle">
      <button 
        type="button"
        class="mode-button" 
        :class="{ 'active': !isAdvancedMode }"
        @click="isAdvancedMode = false"
      >
        Simple
      </button>
      <button 
        type="button"
        class="mode-button" 
        :class="{ 'active': isAdvancedMode }"
        @click="isAdvancedMode = true"
      >
        Advanced
      </button>
    </div>
    
    <!-- Fields -->
    <div class="form-body" :class="{ 'two-columns': isConnectionForm && isAdvancedMode }">
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
import TerminalFormActions from './TerminalFormActions.vue'
import type { FormRequestMessage, FormField } from '~/types/terminal'
import { CommandStatus } from '~/enums'

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

// State - MUST be declared before watch statements that reference them
const fieldValues = ref<Record<string, any>>({})
const fieldErrors = ref<Record<string, string>>({})
const isSubmitting = ref(false)
const isAdvancedMode = ref(false)
const isReadonly = computed(() => 
  props.readonly || props.status === CommandStatus.SUCCESS || props.status === CommandStatus.ERROR
)

// Detect if this is the connection add form
const isConnectionForm = computed(() => {
  return props.formData.title === "Add MongoDB Connection"
})

// Dynamic field filtering based on mode
const displayedFields = computed(() => {
  if (!isConnectionForm.value) {
    // Not a connection form, show all fields
    return props.formData.fields
  }
  
  if (!isAdvancedMode.value) {
    // Simple mode: show name, uri, description
    return props.formData.fields.filter(f => 
      ['name', 'uri', 'description'].includes(f.id)
    )
  } else {
    // Advanced mode: show all except uri
    return props.formData.fields.filter(f => f.id !== 'uri')
  }
})

// Get appropriate component for field type
const getFieldComponent = (field: FormField) => {
  switch (field.type) {
    case 'password':
      return TerminalPasswordField
    case 'number':
      return TerminalNumberField
    case 'textarea':
      // TODO: Create TerminalTextAreaField when needed
      return TerminalTextField
    case 'select':
      // TODO: Create TerminalSelectField when needed
      return TerminalTextField
    default:
      return TerminalTextField
  }
}

// Timeout warning (5 min timeout, warn at 4 min = 240 seconds)
const FORM_TIMEOUT = 300 * 1000 // 5 minutes in ms
const WARNING_TIME = 240 * 1000 // 4 minutes in ms
let timeoutWarningTimer: NodeJS.Timeout | null = null

// Debug: Log form data on mount and changes
watch(() => props.formData, (data) => {
  console.log('[TerminalForm] Form data received:', data)
  console.log('[TerminalForm] Actions:', data.actions)
  console.log('[TerminalForm] Fields:', data.fields)
  console.log('[TerminalForm] isReadonly:', isReadonly.value)
  console.log('[TerminalForm] status:', props.status)
}, { immediate: true })

// Initialize field values with defaults
watch(() => props.formData, (formData) => {
  formData.fields.forEach(field => {
    if (field.default !== undefined && fieldValues.value[field.id] === undefined) {
      fieldValues.value[field.id] = field.default
    }
  })
}, { immediate: true })

// Mode-aware validation
const canSubmit = computed(() => {
  if (!isConnectionForm.value) {
    // Non-connection form: require all required fields
    const requiredFields = props.formData.fields.filter(f => f.required)
    const allRequiredFilled = requiredFields.every(
      f => fieldValues.value[f.id] !== undefined && fieldValues.value[f.id] !== ''
    )
    const hasErrors = Object.keys(fieldErrors.value).length > 0
    return allRequiredFilled && !hasErrors && !isSubmitting.value
  }
  
  if (isAdvancedMode.value) {
    // Advanced mode: require name, host, port
    const required = ['name', 'host', 'port']
    const allRequiredFilled = required.every(
      id => fieldValues.value[id] !== undefined && fieldValues.value[id] !== ''
    )
    
    // If username provided, password should be too
    const hasUsername = !!fieldValues.value.username
    const hasPassword = !!fieldValues.value.password
    const authValid = hasUsername === hasPassword // both or neither
    
    const hasErrors = Object.keys(fieldErrors.value).length > 0
    
    return allRequiredFilled && authValid && !hasErrors && !isSubmitting.value
  } else {
    // Simple mode: require name, uri
    const required = ['name', 'uri']
    const allRequiredFilled = required.every(
      id => fieldValues.value[id] !== undefined && fieldValues.value[id] !== ''
    )
    
    const hasErrors = Object.keys(fieldErrors.value).length > 0
    
    return allRequiredFilled && !hasErrors && !isSubmitting.value
  }
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
  
  // For connection forms, only submit relevant fields based on mode
  let submitData: Record<string, any>
  
  if (isConnectionForm.value) {
    if (isAdvancedMode.value) {
      // Advanced mode: submit name, host, port, username, password, auth_source, database, description
      submitData = {
        name: fieldValues.value.name,
        host: fieldValues.value.host,
        port: fieldValues.value.port,
        username: fieldValues.value.username,
        password: fieldValues.value.password,
        auth_source: fieldValues.value.auth_source,
        database: fieldValues.value.database,
        description: fieldValues.value.description,
        _mode: 'advanced'
      }
    } else {
      // Simple mode: submit name, uri, description
      submitData = {
        name: fieldValues.value.name,
        uri: fieldValues.value.uri,
        description: fieldValues.value.description
      }
    }
  } else {
    // Non-connection forms: submit all fields
    submitData = { ...fieldValues.value }
  }
  
  emit('submit', submitData)
}

const handleCancel = () => {
  emit('cancel')
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
      console.warn('[TerminalForm] Form will timeout in 1 minute')
      // You could also show a toast notification here if you have a toast system
      // For now, we'll just log to console as a dev feature
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

.form-header h3 {
  color: var(--color-primary, #83a598);
  font-size: 16px;
  margin: 0 0 4px 0;
  font-weight: 600;
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
