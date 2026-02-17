<template>
  <div class="terminal-form-stepper-generic" :class="{ 'readonly': isReadonly }">
    <!-- Custom Stepper Component -->
    <TerminalCustomStepper 
      ref="stepper" 
      :steps="stepperSteps" 
      @step-change="handleStepChange"
    >
      <template #default="{ currentStep: currentStepIndex }">
        <div 
          v-for="(step, index) in config.steps" 
          :key="step.id"
          v-show="currentStepIndex === index"
          class="step-wrapper"
        >
          <!-- Loading State -->
          <div v-if="step.isLoading" class="loading-step">
            <span>Loading {{ step.config.title }}...</span>
          </div>

          <!-- Custom Component (if specified) -->
          <component 
            v-else-if="step.component" 
            :is="step.component"
            :step="step"
            :config="config"
            :disabled="isSubmitting"
            :readonly="isReadonly"
            @update:data="updateStepData(index, $event)"
            @update:errors="updateStepErrors(index, $event)"
          />

          <!-- Default Field Rendering -->
          <div v-else-if="step.formData && stepFields(index).length > 0" class="step-content">
            <component
              v-for="field in stepFields(index)"
              :key="field.id"
              :is="getFieldComponent(field)"
              :field="field"
              v-model="step.data[field.id]"
              :disabled="isSubmitting"
              :readonly="isReadonly"
              @blur="handleFieldBlur(field.id, index)"
              @valid="handleFieldValid(field.id, index)"
              @invalid="handleFieldInvalid(field.id, $event, index)"
              @enter="handleEnter"
            />
          </div>

          <!-- Empty State -->
          <div v-else class="empty-step">
            <p>Please complete previous steps first.</p>
          </div>
        </div>
      </template>
    </TerminalCustomStepper>

    <!-- Navigation Buttons -->
    <div v-if="!isReadonly" class="stepper-actions">
      <!-- Previous Button -->
      <button
        type="button"
        class="btn btn-secondary"
        :disabled="!hasPrevious || isSubmitting"
        @click="handlePrevious"
      >
        ← Previous
      </button>

      <!-- Next Button (not on last step) -->
      <button
        v-if="hasNext"
        type="button"
        class="btn btn-primary"
        @click="handleNext"
        :disabled="!canProceed || isSubmitting"
      >
        Next →
      </button>

      <!-- Submit Button (last step) -->
      <button
        v-else
        type="button"
        class="btn btn-primary"
        @click="handleSubmit"
        :disabled="!canSubmit || isSubmitting"
      >
        {{ isSubmitting ? 'Submitting...' : submitButtonText }}
      </button>

      <!-- Cancel Button -->
      <button
        type="button"
        class="btn btn-secondary"
        @click="handleCancel"
        :disabled="isSubmitting"
      >
        Cancel
      </button>
    </div>

    <!-- Status (shown in readonly) -->
    <div v-if="isReadonly" class="form-status">
      <span v-if="status === CommandStatus.ERROR" class="status-cancelled">
        ✗ Cancelled
      </span>
      <span v-else-if="status === CommandStatus.SUCCESS" class="status-submitted">
        ✓ Submitted
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, useTemplateRef } from 'vue'
import TerminalCustomStepper from './TerminalCustomStepper.vue'
import TerminalTextField from './Fields/TerminalTextField.vue'
import TerminalPasswordField from './Fields/TerminalPasswordField.vue'
import TerminalNumberField from './Fields/TerminalNumberField.vue'
import TerminalCheckboxListField from './Fields/TerminalCheckboxListField.vue'
import type { FormField } from '~/types/terminal'
import type { StepperFormConfig, StepContext } from '~/types/stepper'
import { canProceedFromStep, isStepValid, getAllStepData } from '~/types/stepper'
import { CommandStatus } from '~/enums'
import { useAuthStore } from '~/stores/auth'

interface Props {
  config: StepperFormConfig
  readonly?: boolean
  status?: CommandStatus
  submitButtonText?: string
}

const props = withDefaults(defineProps<Props>(), {
  submitButtonText: 'Submit'
})

const emit = defineEmits<{
  submit: [data: Record<string, any>]
  cancel: []
}>()

// Runtime config
const runtimeConfig = useRuntimeConfig()
const baseUrl = runtimeConfig.public.apiUrl

// State
const stepper = useTemplateRef('stepper')
const currentStepIndex = ref(0)
const isSubmitting = ref(false)

const isReadonly = computed(() => 
  props.readonly || props.status === CommandStatus.SUCCESS || props.status === CommandStatus.ERROR
)

// Get fields for a specific step
const stepFields = (stepIndex: number) => {
  const step = props.config.steps[stepIndex]
  return step?.formData?.fields ?? []
}

// Stepper steps configuration for UI
const stepperSteps = computed(() => 
  props.config.steps.map((step, index) => ({
    title: step.config.title,
    description: step.config.description,
    icon: step.config.icon,
    disabled: step.config.disabled ?? !canProceedFromStep(index - 1, props.config.steps)
  }))
)

// Navigation helpers
const hasPrevious = computed(() => currentStepIndex.value > 0)
const hasNext = computed(() => currentStepIndex.value < props.config.steps.length - 1)

// Can proceed to next step
const canProceed = computed(() => 
  canProceedFromStep(currentStepIndex.value, props.config.steps) && !isSubmitting.value
)

// Can submit (last step valid)
const canSubmit = computed(() => {
  const lastStepIndex = props.config.steps.length - 1
  const lastStep = props.config.steps[lastStepIndex]
  return lastStep && isStepValid(lastStep, props.config.steps) && !isSubmitting.value
})

// Get appropriate component for field type
const getFieldComponent = (field: FormField) => {
  switch (field.type) {
    case 'password':
      return TerminalPasswordField
    case 'number':
      return TerminalNumberField
    case 'checkbox-list':
      return TerminalCheckboxListField
    default:
      return TerminalTextField
  }
}

// Create step context for handlers
const createStepContext = (): StepContext => {
  const authStore = useAuthStore()
  
  return {
    currentStepIndex: currentStepIndex.value,
    totalSteps: props.config.steps.length,
    token: authStore.token || '',
    baseUrl,
    goToStep: (index: number) => stepper.value?.goToStep(index),
    next: () => stepper.value?.next(),
    prev: () => stepper.value?.prev()
  }
}

// Update step data
const updateStepData = (stepIndex: number, data: Record<string, any>) => {
  const step = props.config.steps[stepIndex]
  if (step) {
    step.data = { ...step.data, ...data }
  }
}

// Update step errors
const updateStepErrors = (stepIndex: number, errors: Record<string, string>) => {
  const step = props.config.steps[stepIndex]
  if (step) {
    step.errors = errors
  }
}

// Field event handlers
const handleFieldBlur = (fieldId: string, stepIndex: number) => {
  // Validation happens in field component
}

const handleFieldValid = (fieldId: string, stepIndex: number) => {
  const step = props.config.steps[stepIndex]
  if (step) {
    delete step.errors[fieldId]
  }
}

const handleFieldInvalid = (fieldId: string, error: string, stepIndex: number) => {
  const step = props.config.steps[stepIndex]
  if (step) {
    step.errors[fieldId] = error
  }
}

// Navigation handlers
const handleNext = async () => {
  if (!canProceed.value) return
  
  const nextIndex = currentStepIndex.value + 1
  const nextStep = props.config.steps[nextIndex]
  
  // Load next step data if needed
  if (nextStep && nextStep.loadData && !nextStep.formData) {
    await loadStepData(nextIndex)
  }
  
  // Move to next step
  if (nextStep) {
    stepper.value?.next()
  }
}

const handlePrevious = () => {
  stepper.value?.prev()
}

const handleEnter = () => {
  if (!hasNext.value && canSubmit.value) {
    handleSubmit()
  }
}

// Submit handler
const handleSubmit = async () => {
  if (!canSubmit.value) return
  
  isSubmitting.value = true
  
  try {
    // Get all data from all steps
    const allData = getAllStepData(props.config.steps)
    
    // Call custom submit handler if provided
    if (props.config.onSubmit) {
      await props.config.onSubmit(allData)
    }
    
    // Emit to parent
    emit('submit', allData)
  } finally {
    isSubmitting.value = false
  }
}

const handleCancel = () => {
  if (props.config.onCancel) {
    props.config.onCancel()
  }
  emit('cancel')
}

// Handle step changes from stepper component
const handleStepChange = async (newStepIndex: number) => {
  currentStepIndex.value = newStepIndex
  
  const step = props.config.steps[newStepIndex]
  
  // Load step data if needed
  if (step && step.loadData && !step.formData && !step.isLoading) {
    // Check if can proceed to this step
    if (newStepIndex > 0 && !canProceedFromStep(newStepIndex - 1, props.config.steps)) {
      // Go back to previous step
      stepper.value?.goToStep(newStepIndex - 1)
      return
    }
    
    await loadStepData(newStepIndex)
  }
}

// Load data for a specific step
const loadStepData = async (stepIndex: number) => {
  const step = props.config.steps[stepIndex]
  if (!step || !step.loadData) return
  
  step.isLoading = true
  
  try {
    const context = createStepContext()
    await step.loadData(props.config.steps, context)
  } catch (error: any) {
    console.error(`Failed to load step ${stepIndex}:`, error)
    // Go back to previous step on error
    if (stepIndex > 0) {
      stepper.value?.goToStep(stepIndex - 1)
    }
  } finally {
    step.isLoading = false
  }
}

// Initialize first step with form data
watch(() => props.config, (config) => {
  if (config.steps.length > 0) {
    const firstStep = config.steps[0]
    if (firstStep && firstStep.formData) {
      // Initialize default values
      firstStep.formData.fields?.forEach(field => {
        if (field.default !== undefined && firstStep.data[field.id] === undefined) {
          firstStep.data[field.id] = field.default
        }
      })
    }
  }
}, { immediate: true, deep: true })
</script>

<style scoped>
.terminal-form-stepper-generic {
  background: var(--color-bg-primary, #1d2021);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  padding: 16px;
  margin: 12px 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.terminal-form-stepper-generic.readonly {
  opacity: 0.7;
  pointer-events: none;
}

.step-wrapper {
  min-height: 200px;
}

.step-content {
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-step {
  padding: 40px 0;
  text-align: center;
  color: var(--color-text-secondary, #a89984);
  font-size: 14px;
}

.empty-step {
  padding: 40px 0;
  text-align: center;
  color: var(--color-warning, #fe8019);
  font-size: 14px;
  font-style: italic;
}

.stepper-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-secondary, #504945);
}

.btn {
  padding: 10px 20px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover, #689d6a);
}

.btn-secondary {
  background: transparent;
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-secondary, #3c3836);
}

.form-status {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-secondary, #504945);
  font-size: 13px;
}

.status-cancelled {
  color: var(--color-warning, #fe8019);
}

.status-submitted {
  color: var(--color-success, #b8bb26);
}

@media (max-width: 768px) {
  .terminal-form-stepper-generic {
    padding: 12px;
  }
}
</style>
