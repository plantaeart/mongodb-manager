<template>
  <div class="terminal-checkbox-list-field" :class="{ 'error': hasError }">
    <div class="field-label-row">
      <label class="field-label">
        {{ field.label }}
        <span v-if="field.required" class="required">*</span>
      </label>
      <FieldTooltip :text="field.tooltip" />
    </div>
    
    <!-- Bulk selection actions -->
    <div v-if="options.length > 0" class="bulk-actions">
      <button 
        type="button" 
        class="action-btn" 
        @click="selectAll"
        :disabled="disabled || readonly"
      >
        Select All
      </button>
      <button 
        type="button" 
        class="action-btn" 
        @click="clearSelection"
        :disabled="disabled || readonly"
      >
        Clear Selection
      </button>
      <span class="selection-count">{{ selectedCount }} selected</span>
    </div>
    
    <!-- Options list -->
    <div v-if="options.length > 0" class="options-container">
      <div
        v-for="option in options"
        :key="option.value"
        class="checkbox-item"
        :class="{ 'selected': isSelected(option.value), 'disabled': disabled || readonly }"
        @click="toggleSelection(option.value)"
      >
        <div class="checkbox-wrapper">
          <input
            type="checkbox"
            :id="`${field.id}-${option.value}`"
            :value="option.value"
            :checked="isSelected(option.value)"
            :disabled="disabled || readonly"
            @click.stop
            @change="toggleSelection(option.value)"
            class="checkbox-input"
          />
          <label :for="`${field.id}-${option.value}`" class="checkbox-label">
            {{ option.label }}
          </label>
        </div>
        
        <div v-if="option.description || option.metadata" class="option-details">
          <span v-if="option.description" class="option-description">{{ option.description }}</span>
          <span v-if="option.metadata?.added_at" class="option-meta">
            Added: {{ formatDate(option.metadata.added_at) }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Empty state -->
    <div v-else class="empty-state">
      <p>No options available</p>
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
  'update:modelValue': [value: string[]]
  blur: []
  valid: []
  invalid: [error: string]
  enter: []
}>()

// Initialize with array
const selectedValues = ref<string[]>(
  Array.isArray(props.modelValue) ? props.modelValue : []
)
const errorMessage = ref<string>('')
const touched = ref<boolean>(false)

// Get options from field
const options = computed(() => props.field.options || [])

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  const newArray = Array.isArray(newValue) ? newValue : []
  if (JSON.stringify(newArray) !== JSON.stringify(selectedValues.value)) {
    selectedValues.value = newArray
  }
})

// Watch internal changes
watch(selectedValues, (newValue) => {
  emit('update:modelValue', newValue)
  if (touched.value) {
    validate()
  }
}, { deep: true })

const hasError = computed(() => touched.value && !!errorMessage.value)
const selectedCount = computed(() => selectedValues.value.length)

const isSelected = (value: string): boolean => {
  return selectedValues.value.includes(value)
}

const toggleSelection = (value: string) => {
  if (props.disabled || props.readonly) return
  
  touched.value = true
  const index = selectedValues.value.indexOf(value)
  
  if (index > -1) {
    // Remove from selection
    selectedValues.value = selectedValues.value.filter(v => v !== value)
  } else {
    // Add to selection
    selectedValues.value = [...selectedValues.value, value]
  }
}

const selectAll = () => {
  if (props.disabled || props.readonly) return
  touched.value = true
  selectedValues.value = options.value.map(opt => opt.value)
}

const clearSelection = () => {
  if (props.disabled || props.readonly) return
  touched.value = true
  selectedValues.value = []
}

const validate = (): boolean => {
  errorMessage.value = ''
  
  // Required validation - at least one item must be selected
  if (props.field.required && selectedValues.value.length === 0) {
    errorMessage.value = `Please select at least one ${props.field.label.toLowerCase()}`
    emit('invalid', errorMessage.value)
    return false
  }
  
  emit('valid')
  return true
}

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateString
  }
}

// Expose validate method for parent
defineExpose({ validate })
</script>

<style scoped>
.terminal-checkbox-list-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.bulk-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border-secondary, #504945);
}

.action-btn {
  padding: 4px 12px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-bg-secondary, #3c3836);
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
}

.action-btn:hover:not(:disabled) {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  border-color: var(--color-primary, #83a598);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.selection-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-tertiary, #928374);
}

.options-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
  padding: 4px 0;
}

.checkbox-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  background: var(--color-bg-tertiary, #282828);
  cursor: pointer;
  transition: all 0.2s;
}

.checkbox-item:hover:not(.disabled) {
  background: var(--color-bg-secondary, #3c3836);
  border-color: var(--color-primary, #83a598);
}

.checkbox-item.selected {
  background: var(--color-bg-secondary, #3c3836);
  border-color: var(--color-primary, #83a598);
}

.checkbox-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary, #83a598);
}

.checkbox-input:disabled {
  cursor: not-allowed;
}

.checkbox-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary, #ebdbb2);
  cursor: pointer;
  flex: 1;
}

.option-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 28px;
  font-size: 12px;
}

.option-description {
  color: var(--color-text-secondary, #a89984);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.option-meta {
  color: var(--color-text-tertiary, #928374);
  font-style: italic;
}

.empty-state {
  padding: 24px;
  text-align: center;
  color: var(--color-text-tertiary, #928374);
  font-style: italic;
  border: 1px dashed var(--color-border-secondary, #504945);
  border-radius: 4px;
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

.terminal-checkbox-list-field.error .options-container {
  border: 1px solid var(--color-danger, #fb4934);
  border-radius: 4px;
  padding: 8px;
}

/* Scrollbar styling */
.options-container::-webkit-scrollbar {
  width: 8px;
}

.options-container::-webkit-scrollbar-track {
  background: var(--color-bg-primary, #1d2021);
  border-radius: 4px;
}

.options-container::-webkit-scrollbar-thumb {
  background: var(--color-border-secondary, #504945);
  border-radius: 4px;
}

.options-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary, #83a598);
}
</style>
