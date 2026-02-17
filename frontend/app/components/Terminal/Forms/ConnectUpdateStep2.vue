<template>
  <div class="connect-update-step2">
    <!-- Mode Toggle (Simple/Advanced) -->
    <div class="form-mode-toggle">
      <button 
        type="button"
        class="mode-button" 
        :class="{ 'active': !isAdvancedMode }"
        @click="toggleMode(false)"
        :disabled="disabled || readonly"
      >
        Simple
      </button>
      <button 
        type="button"
        class="mode-button" 
        :class="{ 'active': isAdvancedMode }"
        @click="toggleMode(true)"
        :disabled="disabled || readonly"
      >
        Advanced
      </button>
    </div>

    <!-- Fields based on mode -->
    <div class="form-body" :class="{ 'two-columns': isAdvancedMode }">
      <component
        v-for="field in displayedFields"
        :key="field.id"
        :is="getFieldComponent(field)"
        :field="field"
        v-model="localData[field.id]"
        :disabled="disabled"
        :readonly="readonly"
        @blur="handleFieldBlur(field.id)"
        @valid="handleFieldValid(field.id)"
        @invalid="handleFieldInvalid(field.id, $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import TerminalTextField from './Fields/TerminalTextField.vue'
import TerminalPasswordField from './Fields/TerminalPasswordField.vue'
import TerminalNumberField from './Fields/TerminalNumberField.vue'
import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import type { FormField } from '~/types/terminal'

interface Props {
  step: StepDefinition
  config: StepperFormConfig
  disabled?: boolean
  readonly?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:data': [Record<string, any>]
  'update:errors': [Record<string, string>]
}>()

// Local state
const isAdvancedMode = ref(false)
const localData = ref<Record<string, any>>({ ...props.step.data })
const localErrors = ref<Record<string, string>>({ ...props.step.errors })

// Sync local data with step data
watch(() => props.step.data, (newData) => {
  localData.value = { ...newData }
}, { deep: true })

// Emit data changes
watch(localData, (newData) => {
  emit('update:data', newData)
}, { deep: true })

// Emit error changes
watch(localErrors, (newErrors) => {
  emit('update:errors', newErrors)
}, { deep: true })

// Displayed fields based on mode
const displayedFields = computed(() => {
  if (!props.step.formData?.fields) return []
  
  if (!isAdvancedMode.value) {
    // Simple mode: show name, uri, description
    return props.step.formData.fields.filter(f => 
      ['name', 'uri', 'description'].includes(f.id)
    )
  } else {
    // Advanced mode: show all except uri
    return props.step.formData.fields.filter(f => f.id !== 'uri')
  }
})

// Get field component
const getFieldComponent = (field: FormField) => {
  switch (field.type) {
    case 'password':
      return TerminalPasswordField
    case 'number':
      return TerminalNumberField
    default:
      return TerminalTextField
  }
}

// Toggle mode
const toggleMode = (advanced: boolean) => {
  isAdvancedMode.value = advanced
}

// Field handlers
const handleFieldBlur = (fieldId: string) => {
  // Validation happens in field component
}

const handleFieldValid = (fieldId: string) => {
  delete localErrors.value[fieldId]
}

const handleFieldInvalid = (fieldId: string, error: string) => {
  localErrors.value[fieldId] = error
}
</script>

<style scoped>
.connect-update-step2 {
  padding: 16px 0;
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

.mode-button:hover:not(:disabled) {
  background: var(--color-bg-secondary, #3c3836);
}

.mode-button.active {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
  border-color: var(--color-primary, #83a598);
}

.mode-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

@media (max-width: 768px) {
  .form-body.two-columns {
    grid-template-columns: 1fr;
  }
}
</style>
