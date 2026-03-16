<template>
  <div class="terminal-field terminal-checkbox-field" :class="{ 'error': hasError, 'valid': isValid && !hasError }">
    <div class="checkbox-container">
      <input
        :id="field.id"
        type="checkbox"
        v-model="internalValue"
        :disabled="disabled"
        :readonly="readonly"
        class="checkbox-input"
        @change="handleChange"
      />
      <label :for="field.id" class="checkbox-label">
        {{ field.label }}
        <span v-if="field.required" class="required">*</span>
      </label>
      <FieldTooltip :text="field.tooltip" />
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
  'update:modelValue': [value: boolean]
  blur: []
  valid: []
  invalid: [error: string]
  enter: []
}>()

const internalValue = ref<boolean>(!!props.modelValue || !!props.field.default)
const errorMessage = ref<string>('')
const touched = ref<boolean>(false)

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalValue.value) {
    internalValue.value = !!newValue
  }
})

// Watch internal changes and emit
watch(internalValue, (newValue) => {
  emit('update:modelValue', newValue)
})

const hasError = computed(() => touched.value && !!errorMessage.value)
const isValid = computed(() => touched.value && !errorMessage.value && internalValue.value)

const validate = (): boolean => {
  errorMessage.value = ''
  
  // Required validation (checkbox must be checked)
  if (props.field.required && !internalValue.value) {
    errorMessage.value = props.field.help_text || 'You must confirm to proceed with deletion'
    emit('invalid', errorMessage.value)
    return false
  }
  
  emit('valid')
  return true
}

const handleChange = () => {
  touched.value = true
  validate()
  emit('blur')
}

// Validate on mount if field has a value
onMounted(() => {
  if (internalValue.value) {
    validate()
  }
})

// Expose validate method for parent component
defineExpose({
  validate
})
</script>

<style scoped>
.terminal-checkbox-field {
  margin-bottom: 1.5rem;
}

.checkbox-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-input {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
  accent-color: var(--terminal-primary, #4ade80);
}

.checkbox-input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.checkbox-label {
  cursor: pointer;
  user-select: none;
  font-size: 0.95rem;
  color: var(--terminal-text, #e5e7eb);
  margin: 0;
}

.checkbox-label .required {
  color: var(--terminal-danger, #ef4444);
  margin-left: 0.25rem;
}

.help-text {
  display: block;
  margin-top: 0.5rem;
  margin-left: 1.75rem; /* Indent under checkbox */
  font-size: 0.85rem;
  color: var(--terminal-text-dim, #9ca3af);
  font-style: italic;
}

.error-message {
  display: block;
  margin-top: 0.5rem;
  margin-left: 1.75rem; /* Indent under checkbox */
  font-size: 0.85rem;
  color: var(--terminal-danger, #ef4444);
}

.terminal-checkbox-field.error .checkbox-label {
  color: var(--terminal-danger, #ef4444);
}

.terminal-checkbox-field.valid .checkbox-label {
  color: var(--terminal-success, #4ade80);
}
</style>
