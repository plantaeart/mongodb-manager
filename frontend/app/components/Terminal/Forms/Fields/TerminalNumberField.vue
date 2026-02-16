<template>
  <div class="terminal-field" :class="{ 'error': hasError, 'valid': isValid && !hasError }">
    <div class="field-label-row">
      <label :for="field.id" class="field-label">
        {{ field.label }}
        <span v-if="field.required" class="required">*</span>
      </label>
      <FieldTooltip :text="field.tooltip" />
    </div>
    
    <input
      :id="field.id"
      type="number"
      v-model.number="internalValue"
      :placeholder="field.placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :min="field.min"
      :max="field.max"
      :step="field.step || 1"
      class="field-input"
      @blur="handleBlur"
      @keydown.enter="handleEnter"
    />
    
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
  'update:modelValue': [value: number]
  blur: []
  valid: []
  invalid: [error: string]
  enter: []
}>()

const internalValue = ref<number>(props.modelValue ?? props.field.default ?? 0)
const errorMessage = ref<string>('')
const touched = ref<boolean>(false)

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalValue.value) {
    internalValue.value = newValue ?? 0
  }
})

// Watch internal changes
watch(internalValue, (newValue) => {
  emit('update:modelValue', newValue)
})

const hasError = computed(() => touched.value && !!errorMessage.value)
const isValid = computed(() => touched.value && !errorMessage.value && internalValue.value !== null)

const validate = (): boolean => {
  errorMessage.value = ''
  
  // Required validation
  if (props.field.required && (internalValue.value === null || internalValue.value === undefined)) {
    errorMessage.value = `${props.field.label} is required`
    emit('invalid', errorMessage.value)
    return false
  }
  
  // Min validation
  if (props.field.min !== undefined && internalValue.value < props.field.min) {
    errorMessage.value = `Minimum value is ${props.field.min}`
    emit('invalid', errorMessage.value)
    return false
  }
  
  // Max validation
  if (props.field.max !== undefined && internalValue.value > props.field.max) {
    errorMessage.value = `Maximum value is ${props.field.max}`
    emit('invalid', errorMessage.value)
    return false
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
