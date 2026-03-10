<template>
  <div class="select-connection-form">
    <!-- Readonly Summary View -->
    <div v-if="readonly" class="selection-summary">
      <div class="summary-header">
        <Icon name="i-lucide-check-circle" class="summary-icon" />
        <h3 class="summary-title">Selected Connection</h3>
      </div>
      
      <div class="summary-content">
        <div class="summary-item">
          <span class="summary-label">Connection:</span>
          <span class="summary-value">{{ selectedConnectionName }}</span>
        </div>
      </div>
    </div>

    <!-- Editable Form View -->
    <div v-else>
      <!-- Help Text -->
      <p class="help-text">Choose one connection to update</p>

      <!-- Connection List Field -->
      <TerminalCheckboxListField
        v-if="connectionField"
        :field="connectionField"
        v-model="localData.connection_name"
        :disabled="disabled"
        :readonly="readonly"
        @blur="handleFieldBlur"
        @valid="handleFieldValid"
        @invalid="handleFieldInvalid"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import TerminalCheckboxListField from '~/components/Terminal/Forms/Fields/TerminalCheckboxListField.vue'
import type { StepDefinition, StepperFormConfig } from '~/types/stepper'

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
const localData = ref<Record<string, any>>({ ...props.step.data })
const localErrors = ref<Record<string, string>>({ ...props.step.errors })

// Store submitted data for readonly summary
const submittedData = ref<Record<string, any>>({})

// Use step data directly in readonly mode to ensure we have the submitted values
const displayData = computed(() => {
  if (props.readonly) {
    // In readonly mode, use submitted data if available, fallback to step data
    return Object.keys(submittedData.value).length > 0 
      ? submittedData.value 
      : props.step.data
  }
  return localData.value
})

// Get connection field from formData
const connectionField = computed(() => {
  return props.step.formData?.fields?.find(f => f.id === 'connection_name')
})

// Get selected connection name for summary
const selectedConnectionName = computed(() => {
  const name = displayData.value.connection_name
  if (Array.isArray(name)) {
    return name[0] || 'N/A'
  }
  return name || 'N/A'
})

// Sync local data with step data
watch(() => props.step.data, (newData) => {
  localData.value = { ...newData }
}, { deep: true })

// Emit data changes
watch(localData, (newData) => {
  emit('update:data', newData)
}, { deep: true })

// Watch for readonly changes to store submitted data
watch(() => props.readonly, (newReadonly) => {
  if (newReadonly && Object.keys(localData.value).length > 0) {
    // Store current data when entering readonly mode
    submittedData.value = { ...localData.value }
  }
})

// Emit error changes
watch(localErrors, (newErrors) => {
  emit('update:errors', newErrors)
}, { deep: true })

// Field handlers
const handleFieldBlur = () => {
  // Validation happens in field component
}

const handleFieldValid = () => {
  delete localErrors.value.connection_name
}

const handleFieldInvalid = (error: string) => {
  localErrors.value.connection_name = error
}
</script>

<style scoped>
.select-connection-form {
  padding: 16px 0;
}

.help-text {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  color: var(--color-text-secondary, #a89984);
  margin-bottom: 16px;
  font-style: italic;
}

/* Summary View Styles */
.selection-summary {
  background: var(--color-bg-tertiary, #282828);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  padding: 16px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-secondary, #504945);
}

.summary-icon {
  width: 20px;
  height: 20px;
  color: var(--color-success, #b8bb26);
}

.summary-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #ebdbb2);
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 12px;
  align-items: start;
}

.summary-label {
  font-size: 13px;
  color: var(--color-text-secondary, #a89984);
  font-weight: 500;
}

.summary-value {
  font-size: 13px;
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-weight: 600;
}

@media (max-width: 768px) {
  .summary-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
