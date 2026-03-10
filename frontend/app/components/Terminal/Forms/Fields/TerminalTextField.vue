<template>
  <div class="terminal-field" :class="{ 'error': hasError, 'valid': isValid && !hasError }">
    <div class="field-label-row">
      <label :for="field.id" class="field-label">
        {{ field.label }}
        <span v-if="field.required" class="required">*</span>
      </label>
      <FieldTooltip :text="field.tooltip" />
    </div>
    
    <div v-if="isUriField && hasPasswordInUri" class="password-input-wrapper">
      <input
        :id="field.id"
        type="text"
        v-model="displayValue"
        :placeholder="field.placeholder"
        :disabled="disabled"
        :readonly="readonly"
        class="field-input"
        @input="handleInput"
        @blur="handleBlur"
        @keydown.enter="handleEnter"
      />
      <button
        v-if="displayValue"
        type="button"
        class="toggle-password-btn"
        @click="togglePasswordVisibility"
        :disabled="disabled || readonly"
        :title="showPassword ? 'Hide password' : 'Show password'"
      >
        <Icon :name="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'" class="eye-icon" />
      </button>
    </div>
    
    <input
      v-else
      :id="field.id"
      type="text"
      v-model="internalValue"
      :placeholder="field.placeholder"
      :disabled="disabled"
      :readonly="readonly"
      class="field-input"
      @blur="handleBlur"
      @keydown.enter="handleEnter"
    />
    
    <span v-if="field.help_text" class="help-text">{{ field.help_text }}</span>
    <span v-if="errorMessage" class="error-message">{{ errorMessage }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import type { FormField } from '~/types/terminal'
import FieldTooltip from '../FieldTooltip.vue'
import { maskMongoUriPassword } from '~/utils/formHelpers'

interface Props {
  field: FormField
  modelValue: any
  disabled?: boolean
  readonly?: boolean
  originalValue?: string  // For URI password masking
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
  valid: []
  invalid: [error: string]
  enter: []
}>()

const internalValue = ref<string>(props.modelValue || props.field.default || '')
const errorMessage = ref<string>('')
const touched = ref<boolean>(false)
const showPassword = ref<boolean>(false)

// Store the original unmasked URI
const originalUri = ref<string>('')
const maskedUri = ref<string>('')

// Check if this is a URI field (for password masking)
const isUriField = computed(() => props.field.id === 'uri')

// Helper function to check if URI has password
const hasPasswordInUri = computed(() => {
  if (!internalValue.value) return false
  const passwordRegex = /^mongodb:\/\/[^:]+:([^@]+)@/
  return passwordRegex.test(internalValue.value)
})

// Initialize URIs on mount
onMounted(() => {
  if (isUriField.value && props.originalValue) {
    // originalValue is the decoded URI (from _originalUri)
    originalUri.value = props.originalValue
    // modelValue is already masked from the stepper config
    maskedUri.value = props.modelValue
    internalValue.value = maskedUri.value
  }
})

// Display value for URI field
const displayValue = computed({
  get() {
    if (!isUriField.value || !hasPasswordInUri.value) {
      return internalValue.value
    }
    
    return showPassword.value ? originalUri.value : maskedUri.value
  },
  set(newValue: string) {
    // User is typing
    if (isUriField.value && showPassword.value) {
      // Update original when showing password
      originalUri.value = newValue
      maskedUri.value = maskMongoUriPassword(newValue)
      internalValue.value = newValue
    } else {
      internalValue.value = newValue
    }
  }
})

// Toggle password visibility in URI
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
  
  // Emit the current correct value
  if (showPassword.value) {
    emit('update:modelValue', originalUri.value)
  } else {
    emit('update:modelValue', maskedUri.value)
  }
}

// Handle input changes
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const newValue = target.value
  
  if (showPassword.value) {
    // User is typing with password visible
    originalUri.value = newValue
    maskedUri.value = maskMongoUriPassword(newValue)
    internalValue.value = newValue
  } else {
    // User is typing with password masked
    internalValue.value = newValue
  }
  
  emit('update:modelValue', internalValue.value)
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalValue.value) {
    internalValue.value = newValue || ''
  }
})

// Watch for originalValue prop changes (for URI field)
watch(() => props.originalValue, (newValue) => {
  if (isUriField.value && newValue) {
    originalUri.value = newValue
    maskedUri.value = maskMongoUriPassword(newValue)
    if (!showPassword.value) {
      internalValue.value = maskedUri.value
    }
  }
})

// Watch internal changes
watch(internalValue, (newValue) => {
  if (!isUriField.value || !hasPasswordInUri.value) {
    emit('update:modelValue', newValue)
  }
})

const hasError = computed(() => touched.value && !!errorMessage.value)
const isValid = computed(() => touched.value && !errorMessage.value && internalValue.value !== '')

const validate = (): boolean => {
  errorMessage.value = ''
  
  // Get the actual value to validate (original URI if showing password)
  const valueToValidate = (isUriField.value && showPassword.value) ? originalUri.value : internalValue.value
  
  // Required validation
  if (props.field.required && !valueToValidate) {
    errorMessage.value = `${props.field.label} is required`
    emit('invalid', errorMessage.value)
    return false
  }
  
  // Pattern validation
  if (props.field.validation?.pattern && valueToValidate) {
    const regex = new RegExp(props.field.validation.pattern)
    if (!regex.test(valueToValidate)) {
      errorMessage.value = props.field.validation.message || 'Invalid format'
      emit('invalid', errorMessage.value)
      return false
    }
  }
  
  emit('valid')
  return true
}

const handleBlur = () => {
  touched.value = true
  validate()
  emit('blur')
}

const handleEnter = () => {
  touched.value = true
  if (validate()) {
    emit('enter')
  }
}

// Initialize with default value
if (props.field.default && !internalValue.value) {
  internalValue.value = props.field.default
}
</script>

<style scoped>
.terminal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.field-label {
  color: var(--color-text-primary, #ebdbb2);
  font-size: 13px;
  font-weight: 500;
}

.field-label .required {
  color: var(--color-danger, #fb4934);
  margin-left: 2px;
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-wrapper .field-input {
  padding-right: 40px; /* Space for the eye icon */
}

.field-input {
  background: var(--color-bg-tertiary, #282828);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 3px;
  padding: 8px 10px;
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  transition: border-color 0.2s;
  width: 100%;
}

.field-input:focus {
  outline: none;
  border-color: var(--color-primary, #83a598);
}

.field-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.terminal-field.error .field-input {
  border-color: var(--color-danger, #fb4934);
}

.terminal-field.valid .field-input {
  border-color: var(--color-success, #b8bb26);
}

.toggle-password-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary, #928374);
  transition: color 0.2s;
}

.toggle-password-btn:hover:not(:disabled) {
  color: var(--color-text-primary, #ebdbb2);
}

.toggle-password-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.eye-icon {
  width: 18px;
  height: 18px;
}

.help-text {
  font-size: 12px;
  color: var(--color-text-tertiary, #928374);
  font-style: italic;
}

.error-message {
  font-size: 12px;
  color: var(--color-danger, #fb4934);
}
</style>
