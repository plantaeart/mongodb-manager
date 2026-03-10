<template>
  <div class="update-details-form">
    <!-- Readonly Summary View -->
    <div v-if="readonly" class="update-summary">
      <div class="summary-header">
        <Icon name="i-lucide-info" class="summary-icon" />
        <h3 class="summary-title">Connection Update Summary</h3>
      </div>
      
      <div class="summary-content">
        <div class="summary-item">
          <span class="summary-label">Connection Name:</span>
          <span class="summary-value">{{ displayData.name || 'N/A' }}</span>
        </div>
        
        <div v-if="displayData.uri" class="summary-item">
          <span class="summary-label">MongoDB URI:</span>
          <span class="summary-value uri-value">{{ getMaskedUri(displayData.uri) }}</span>
        </div>
        
        <div v-if="displayData.host" class="summary-item">
          <span class="summary-label">Host:</span>
          <span class="summary-value">{{ displayData.host }}</span>
        </div>
        
        <div v-if="displayData.port" class="summary-item">
          <span class="summary-label">Port:</span>
          <span class="summary-value">{{ displayData.port }}</span>
        </div>
        
        <div v-if="displayData.database" class="summary-item">
          <span class="summary-label">Database:</span>
          <span class="summary-value">{{ displayData.database }}</span>
        </div>
        
        <div v-if="displayData.username" class="summary-item">
          <span class="summary-label">Username:</span>
          <span class="summary-value">{{ displayData.username }}</span>
        </div>
        
        <div v-if="displayData.auth_source" class="summary-item">
          <span class="summary-label">Auth Source:</span>
          <span class="summary-value">{{ displayData.auth_source }}</span>
        </div>
        
        <div v-if="displayData.description" class="summary-item">
          <span class="summary-label">Description:</span>
          <span class="summary-value">{{ displayData.description }}</span>
        </div>
      </div>
    </div>

    <!-- Editable Form View -->
    <div v-else>
      <!-- Mode Toggle (Simple/Advanced) -->
      <FormModeToggle 
        v-model="isAdvancedMode" 
        :disabled="disabled"
      />

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
          :uri-components="field.id === 'uri' ? getUriComponents() : undefined"
          @blur="handleFieldBlur(field.id)"
          @valid="handleFieldValid(field.id)"
          @invalid="handleFieldInvalid(field.id, $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import FormModeToggle from '~/components/Terminal/Forms/Shared/FormModeToggle.vue'
import TerminalTextField from '~/components/Terminal/Forms/Fields/TerminalTextField.vue'
import TerminalPasswordField from '~/components/Terminal/Forms/Fields/TerminalPasswordField.vue'
import TerminalNumberField from '~/components/Terminal/Forms/Fields/TerminalNumberField.vue'
import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import type { FormField } from '~/types/terminal'
import { filterConnectionFields, buildMongoUri } from '~/utils/formHelpers'
import { createLogger } from '~/services/logger'

const logger = createLogger('UpdateDetails')

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

// Sync local data with step data
watch(() => props.step.data, (newData) => {
  localData.value = { ...newData }
  
  // Debug URI field in simple mode
  if (!isAdvancedMode.value && newData.uri) {
    logger.debug(`[UpdateDetails] Step data updated - URI in simple mode: ${newData.uri.substring(0, 60)}...`)
  }
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
    logger.debug('Stored submitted data:', submittedData.value)
  }
})

// Emit error changes
watch(localErrors, (newErrors) => {
  emit('update:errors', newErrors)
}, { deep: true })

// Watch mode changes to rebuild URI when switching modes
watch(isAdvancedMode, (newMode, oldMode) => {
  if (oldMode === true && newMode === false) {
    // Switching from Advanced → Simple: rebuild URI from components
    if (localData.value.host && localData.value.port) {
      const rebuiltUri = buildMongoUri({
        host: localData.value.host,
        port: localData.value.port,
        username: localData.value.username,
        password: localData.value.password,
        database: localData.value.database,
        auth_source: localData.value.auth_source
      }, false, true)  // false = don't mask, true = for display (decoded password)
      
      localData.value.uri = rebuiltUri
      logger.info('Rebuilt URI for simple mode:', rebuiltUri)
    }
  }
})

// Displayed fields based on mode
const displayedFields = computed(() => {
  if (!props.step.formData?.fields) return []
  const filtered = filterConnectionFields(props.step.formData.fields, isAdvancedMode.value)
  
  // Debug which fields are displayed
  logger.debug(`[UpdateDetails] Mode: ${isAdvancedMode.value ? 'Advanced' : 'Simple'}, Fields: ${filtered.map(f => f.id).join(', ')}`)
  
  return filtered
})

// Get field component based on type
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

// Get URI components for building URI dynamically (NO REGEX!)
const getUriComponents = () => {
  return {
    host: localData.value.host || 'localhost',
    port: localData.value.port || 27017,
    username: localData.value.username,
    password: localData.value.password,
    database: localData.value.database,
    auth_source: localData.value.auth_source
  }
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

// Helper to mask URI password for readonly summary (using buildMongoUri - NO REGEX!)
const getMaskedUri = (uri: string): string => {
  if (!uri) return 'N/A'
  
  // Build masked URI from components
  const components = getUriComponents()
  if (components.host && components.port) {
    return buildMongoUri(components, true, true)  // true = mask password, true = for display
  }
  
  // Fallback: mask using regex only for readonly display
  const passwordRegex = /:([^@]+)@/
  return uri.replace(passwordRegex, ':***@')
}
</script>

<style scoped>
.update-details-form {
  padding: 16px 0;
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

/* Summary View Styles */
.update-summary {
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
  color: var(--color-primary, #83a598);
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
  grid-template-columns: 140px 1fr;
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
  word-break: break-all;
}

.summary-value.uri-value {
  color: var(--color-primary, #83a598);
}

@media (max-width: 768px) {
  .form-body.two-columns {
    grid-template-columns: 1fr;
  }
  
  .summary-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
