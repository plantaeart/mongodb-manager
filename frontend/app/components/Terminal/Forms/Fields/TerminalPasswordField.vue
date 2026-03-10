<template>
  <div class="terminal-field" :class="{ 'error': hasError, 'valid': isValid && !hasError }">
    <div class="field-label-row">
      <label :for="field.id" class="field-label">
        {{ field.label }}
        <span v-if="field.required" class="required">*</span>
      </label>
      <FieldTooltip :text="field.tooltip" />
    </div>
    
    <div class="password-input-wrapper">
      <input
        :id="field.id"
        :type="showPassword ? 'text' : 'password'"
        v-model="internalValue"
        :placeholder="field.placeholder"
        :disabled="disabled"
        :readonly="readonly"
        class="field-input"
        autocomplete="new-password"
        @blur="handleBlur"
        @keydown.enter="handleEnter"
      />
      <button
        v-if="internalValue"
        type="button"
        class="toggle-password-btn"
        @click="togglePasswordVisibility"
        :disabled="disabled || readonly"
        :title="showPassword ? 'Hide password' : 'Show password'"
      >
        <Icon :name="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'" class="eye-icon" />
      </button>
    </div>
    
    <span v-if="field.help_text" class="help-text">{{ field.help_text }}</span>
    <span v-if="errorMessage" class="error-message">{{ errorMessage }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { FormField } from '~/types/terminal'
import FieldTooltip from '../FieldTooltip.vue'

interface Props {
  field: FormField
  modelValue: any
  disabled?: boolean
  readonly?: boolean
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

// Toggle password visibility
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalValue.value) {
    internalValue.value = newValue || ''
  }
})

// Watch internal changes
watch(internalValue, (newValue) => {
  emit('update:modelValue', newValue)
})

const hasError = computed(() => touched.value && !!errorMessage.value)
const isValid = computed(() => touched.value && !errorMessage.value && internalValue.value !== '')

const validate = (): boolean => {
  errorMessage.value = ''
  
  // Required validation
  if (props.field.required && !internalValue.value) {
    errorMessage.value = `${props.field.label} is required`
    emit('invalid', errorMessage.value)
    return false
  }
  
  // Pattern validation
  if (props.field.validation?.pattern && internalValue.value) {
    const regex = new RegExp(props.field.validation.pattern)
    if (!regex.test(internalValue.value)) {
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

// Expose validate for parent components
defineExpose({ validate })
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

.field-input {
  background: var(--color-bg-tertiary, #282828);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 3px;
  padding: 8px 10px;
  padding-right: 40px; /* Make room for eye icon */
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
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary, #a89984);
  transition: color 0.2s;
}

.toggle-password-btn:hover:not(:disabled) {
  color: var(--color-text-primary, #ebdbb2);
}

.toggle-password-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
