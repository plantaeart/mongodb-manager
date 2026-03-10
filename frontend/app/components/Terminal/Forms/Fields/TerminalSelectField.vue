<template>
  <div class="terminal-select-field" :class="{ 'error': hasError, 'valid': isValid && !hasError }">
    <div class="field-label-row">
      <label :for="field.id" class="field-label">
        {{ field.label }}
        <span v-if="field.required" class="required">*</span>
      </label>
      <FieldTooltip :text="field.tooltip" />
    </div>
    
    <div class="select-wrapper">
      <select
        :id="field.id"
        v-model="internalValue"
        :disabled="disabled"
        :readonly="readonly"
        class="field-select"
        @change="handleChange"
        @blur="handleBlur"
      >
        <option value="" disabled>{{ placeholder }}</option>
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :title="option.description || ''"
        >
          {{ option.label }}
        </option>
      </select>
      <Icon name="i-lucide-chevron-down" class="select-icon" />
    </div>
    
    <!-- Selected option details (shown below dropdown) -->
    <div v-if="selectedOption && selectedOption.description" class="selected-details">
      <div class="detail-row">
        <span class="detail-icon">🔗</span>
        <div class="detail-content">
          <span class="detail-label">Connection URI:</span>
          <span class="detail-value">{{ selectedOption.description }}</span>
        </div>
      </div>
    </div>
    
    <span v-if="field.help_text" class="help-text">{{ field.help_text }}</span>
    <span v-if="errorMessage" class="error-message">{{ errorMessage }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
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

// Computed properties
const options = computed(() => props.field.options || [])
const placeholder = computed(() => props.field.placeholder || 'Select an option...')

const selectedOption = computed(() => {
  return options.value.find(opt => opt.value === internalValue.value)
})

const hasError = computed(() => !!errorMessage.value && touched.value)
const isValid = computed(() => !errorMessage.value && touched.value && internalValue.value !== '')

// Validation
const validate = (): boolean => {
  if (props.field.required && !internalValue.value) {
    errorMessage.value = `${props.field.label} is required`
    return false
  }
  
  errorMessage.value = ''
  return true
}

// Handlers
const handleChange = () => {
  touched.value = true
  emit('update:modelValue', internalValue.value)
  
  if (validate()) {
    emit('valid')
  } else {
    emit('invalid', errorMessage.value)
  }
}

const handleBlur = () => {
  touched.value = true
  emit('blur')
  
  if (validate()) {
    emit('valid')
  } else {
    emit('invalid', errorMessage.value)
  }
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalValue.value) {
    internalValue.value = newValue || ''
  }
})

// Initialize validation on mount if field has default value
onMounted(() => {
  if (internalValue.value) {
    validate()
  }
})
</script>

<style scoped>
.terminal-select-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.field-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-label {
  color: var(--color-text-secondary, #d5c4a1);
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.required {
  color: var(--color-error, #fb4934);
  font-weight: bold;
}

.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.field-select {
  width: 100%;
  padding: 8px 32px 8px 10px;
  background: var(--color-bg-secondary, #282828);
  border: 1px solid var(--color-border-primary, #665c54);
  border-radius: 3px;
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  appearance: none;
  cursor: pointer;
  transition: all 0.2s;
}

.field-select:hover:not(:disabled) {
  border-color: var(--color-primary, #83a598);
  background: var(--color-bg-tertiary, #3c3836);
}

.field-select:focus {
  outline: none;
  border-color: var(--color-primary, #83a598);
  box-shadow: 0 0 0 2px rgba(131, 165, 152, 0.2);
}

.field-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field-select option {
  background: var(--color-bg-secondary, #282828);
  color: var(--color-text-primary, #ebdbb2);
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.5;
}

.field-select option:hover {
  background: var(--color-bg-tertiary, #3c3836);
}

.field-select option:checked {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
}

.select-icon {
  position: absolute;
  right: 10px;
  width: 16px;
  height: 16px;
  color: var(--color-text-tertiary, #928374);
  pointer-events: none;
}

.selected-details {
  padding: 10px 12px;
  background: var(--color-bg-tertiary, #3c3836);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 3px;
  margin-top: 4px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.detail-icon {
  font-size: 16px;
  line-height: 1;
  margin-top: 2px;
  flex-shrink: 0;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0; /* Allow text to wrap/truncate */
}

.detail-label {
  color: var(--color-text-tertiary, #928374);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  word-break: break-all;
  line-height: 1.5;
  background: var(--color-bg-secondary, #282828);
  padding: 6px 8px;
  border-radius: 2px;
  border: 1px solid var(--color-border-primary, #665c54);
}

.help-text {
  color: var(--color-text-tertiary, #928374);
  font-size: 12px;
  font-style: italic;
}

.error-message {
  color: var(--color-error, #fb4934);
  font-size: 12px;
  font-weight: 500;
}

.terminal-select-field.error .field-select {
  border-color: var(--color-error, #fb4934);
}

.terminal-select-field.valid .field-select {
  border-color: var(--color-success, #b8bb26);
}
</style>
