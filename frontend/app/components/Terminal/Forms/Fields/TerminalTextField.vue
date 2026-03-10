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
import { buildMongoUri } from '~/utils/formHelpers'
import type { ConnectionComponents } from '~/utils/formHelpers'
import { createLogger } from '~/services/logger'

const logger = createLogger('TerminalTextField')

interface Props {
  field: FormField
  modelValue: any
  disabled?: boolean
  readonly?: boolean
  uriComponents?: ConnectionComponents  // For building URI dynamically (no regex!)
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

// Check if this is a URI field
const isUriField = computed(() => props.field.id === 'uri')

// Check if we have URI components (for building URI without regex)
const hasUriComponents = computed(() => {
  return isUriField.value && 
         props.uriComponents && 
         props.uriComponents.host && 
         props.uriComponents.port
})

// Check if URI has password (only true if we have components with password)
const hasPasswordInUri = computed(() => {
  return hasUriComponents.value && !!props.uriComponents?.password
})

// Build URI dynamically from components (NO REGEX!)
const buildUriFromComponents = (maskPassword: boolean): string => {
  if (!props.uriComponents) return ''
  
  // Always use forDisplay=true for UI display
  return buildMongoUri(props.uriComponents, maskPassword, true)
}

// Display value for URI field
const displayValue = computed({
  get() {
    // If we have URI components, build URI dynamically
    if (hasUriComponents.value) {
      const uri = buildUriFromComponents(!showPassword.value)
      logger.debug(`[uri] Built URI (masked=${!showPassword.value}): ${uri.substring(0, 60)}...`)
      return uri
    }
    
    // Fallback to internal value for non-URI fields or fields without components
    return internalValue.value
  },
  set(newValue: string) {
    // User is typing - update internal value
    internalValue.value = newValue
  }
})

// Toggle password visibility in URI
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
  logger.debug(`[uri] Password visibility toggled: ${showPassword.value ? 'visible' : 'hidden'}`)
}

// Handle input changes for URI field
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const newValue = target.value
  
  // For URI fields with components, user is editing the URI directly
  // We'll store it as internal value
  internalValue.value = newValue
  emit('update:modelValue', newValue)
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalValue.value) {
    internalValue.value = newValue || ''
  }
})

// Watch internal changes (for non-URI fields or URI without components)
watch(internalValue, (newValue) => {
  if (!hasUriComponents.value) {
    emit('update:modelValue', newValue)
  }
})

const hasError = computed(() => touched.value && !!errorMessage.value)
const isValid = computed(() => touched.value && !errorMessage.value && internalValue.value !== '')

const validate = (): boolean => {
  errorMessage.value = ''
  
  // Get the actual value to validate
  const valueToValidate = hasUriComponents.value 
    ? buildUriFromComponents(false)  // Validate full URI with password
    : internalValue.value
  
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
