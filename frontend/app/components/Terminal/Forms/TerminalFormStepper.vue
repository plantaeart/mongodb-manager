<template>
  <!-- Compact submitted/cancelled state — hides full form UI -->
  <div v-if="isReadonly" class="form-submitted-state">
    <span v-if="status === CommandStatus.ERROR" class="status-cancelled">
      ✗ Cancelled
    </span>
    <span v-else-if="status === CommandStatus.SUCCESS" class="status-submitted">
      ✓ Submitted
    </span>
  </div>

  <!-- Full stepper UI (only while active) -->
  <div v-else class="terminal-form-stepper-generic">
    <!-- Stepper Progress Component -->
    <StepperProgress 
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
            v-else-if="step.component && getCustomComponent(step.component)" 
            :is="getCustomComponent(step.component)"
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
              :model-value="step.data[field.id]"
              @update:model-value="handleFieldValueUpdate(field.id, $event, index)"
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
    </StepperProgress>

    <!-- Navigation Buttons -->
    <div class="stepper-actions">
      <!-- Previous Button -->
      <BaseButton
        :variant="ButtonVariant.SECONDARY"
        :type="ButtonType.BUTTON"
        :disabled="!hasPrevious || isSubmitting"
        @click="handlePrevious"
      >
        ← Previous
      </BaseButton>

      <!-- Next Button (not on last step) -->
      <BaseButton
        v-if="hasNext"
        :variant="ButtonVariant.PRIMARY"
        :type="ButtonType.BUTTON"
        :disabled="!canProceed || isSubmitting"
        @click="handleNext"
      >
        Next →
      </BaseButton>

      <!-- Submit Button (last step) -->
      <BaseButton
        v-else
        :variant="ButtonVariant.PRIMARY"
        :type="ButtonType.BUTTON"
        :disabled="!canSubmit || isSubmitting"
        :loading="isSubmitting"
        @click="handleSubmit"
      >
        {{ submitButtonText }}
      </BaseButton>

      <!-- Cancel Button -->
      <BaseButton
        :variant="ButtonVariant.SECONDARY"
        :type="ButtonType.BUTTON"
        :disabled="isSubmitting"
        @click="handleCancel"
      >
        Cancel
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, triggerRef } from 'vue'
import StepperProgress from './StepperProgress.vue'
import CommandsConnectUpdateSelectConnection from '~/components/Commands/Connect/Update/SelectConnection.vue'
import CommandsConnectUpdateUpdateDetails from '~/components/Commands/Connect/Update/UpdateDetails.vue'
import type { StepperFormConfig, StepContext } from '~/types/stepper'
import { isStepValid, canProceedFromStep, getAllStepData } from '~/utils/stepperHelpers'
import { getFieldComponent } from '~/composables/useFieldComponent'
import { CommandStatus, ButtonVariant, ButtonType } from '~/enums'
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
// Use a ref wrapper for steps to enable deep reactivity control
const stepsRef = ref(props.config.steps)

const isReadonly = computed(() => 
  props.readonly || props.status === CommandStatus.SUCCESS || props.status === CommandStatus.ERROR
)

// Get fields for a specific step
const stepFields = (stepIndex: number) => {
  const step = stepsRef.value[stepIndex]
  return step?.formData?.fields ?? []
}

// Component registry for custom step components
const customComponentRegistry: Record<string, any> = {
  CommandsConnectUpdateSelectConnection,
  CommandsConnectUpdateUpdateDetails
}

// Resolve custom component by name
const getCustomComponent = (componentName: string) => {
  const component = customComponentRegistry[componentName]
  if (!component) {
    return null
  }
  return component
}

// Stepper steps configuration for UI
const stepperSteps = computed(() => 
  stepsRef.value.map((step, index) => {
    // Step 0 is always enabled
    if (index === 0) {
      return {
        title: step.config.title,
        description: step.config.description,
        icon: step.config.icon,
        disabled: step.config.disabled ?? false
      }
    }
    
    // All other steps are disabled if ANY previous step is invalid
    const previousStepsValidation = stepsRef.value.slice(0, index).map((s, i) => ({
      step: i,
      id: s.id,
      valid: isStepValid(s, stepsRef.value)
    }))
    
    const allPreviousValid = previousStepsValidation.every(v => v.valid)
    // If config.disabled is explicitly true, keep it disabled
    // Otherwise, disable if any previous step is invalid
    const isDisabled = step.config.disabled === true ? true : !allPreviousValid
    
    return {
      title: step.config.title,
      description: step.config.description,
      icon: step.config.icon,
      disabled: isDisabled
    }
  })
)

// Navigation helpers
const hasPrevious = computed(() => currentStepIndex.value > 0)
const hasNext = computed(() => currentStepIndex.value < stepsRef.value.length - 1)

// Can proceed to next step
const canProceed = computed(() => 
  canProceedFromStep(currentStepIndex.value, stepsRef.value) && !isSubmitting.value
)

// Can submit (last step valid)
const canSubmit = computed(() => {
  const lastStep = stepsRef.value[stepsRef.value.length - 1]
  return lastStep && isStepValid(lastStep, stepsRef.value) && !isSubmitting.value
})

// Create step context for handlers
const createStepContext = (): StepContext => {
  const authStore = useAuthStore()
  
  return {
    currentStepIndex: currentStepIndex.value,
    totalSteps: stepsRef.value.length,
    token: authStore.token || '',
    baseUrl,
    goToStep: (index: number) => stepper.value?.goToStep(index),
    next: () => stepper.value?.next(),
    prev: () => stepper.value?.prev()
  }
}

// Update step data
const updateStepData = (stepIndex: number, data: Record<string, any>) => {
  const step = stepsRef.value[stepIndex]
  if (step) {
    step.data = { ...step.data, ...data }
    // Trigger reactivity update for deep changes
    triggerRef(stepsRef)
  }
}

// Update step errors
const updateStepErrors = (stepIndex: number, errors: Record<string, string>) => {
  const step = stepsRef.value[stepIndex]
  if (step) {
    step.errors = errors
    // Trigger reactivity update for deep changes
    triggerRef(stepsRef)
  }
}

// Handle field value updates with proper reactivity
const handleFieldValueUpdate = (fieldId: string, value: any, stepIndex: number) => {
  const step = stepsRef.value[stepIndex]
  if (step) {
    step.data = { ...step.data, [fieldId]: value }
    triggerRef(stepsRef)
  }
}

// Field event handlers
const handleFieldBlur = (fieldId: string, stepIndex: number) => {
  // Validation happens in field component
}

const handleFieldValid = (fieldId: string, stepIndex: number) => {
  const step = stepsRef.value[stepIndex]
  if (step) {
    delete step.errors[fieldId]
    // Trigger reactivity update
    triggerRef(stepsRef)
  }
}

const handleFieldInvalid = (fieldId: string, error: string, stepIndex: number) => {
  const step = stepsRef.value[stepIndex]
  if (step) {
    step.errors[fieldId] = error
    // Trigger reactivity update
    triggerRef(stepsRef)
  }
}

// Navigation handlers
const handleNext = async () => {
  if (!canProceed.value) return
  
  const nextIndex = currentStepIndex.value + 1
  const nextStep = stepsRef.value[nextIndex]
  
  // Load next step data if needed
  if (nextStep && nextStep.loadData && !nextStep.formData) {
    await loadStepData(nextIndex)
  }
  
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
  
  // Run optional pre-submit hook (awaitable)
  if (props.config.onSubmit) {
    try {
      const allData = getAllStepData(stepsRef.value)
      await props.config.onSubmit(allData)
    } catch {
      isSubmitting.value = false
      return
    }
  }

  // Emit to parent — spinner stays on until isReadonly becomes true
  // (parent sets status to SUCCESS/ERROR which triggers the watch below)
  const allData = getAllStepData(stepsRef.value)
  emit('submit', allData)
}

// Reset isSubmitting when the form transitions to readonly (success or error)
watch(isReadonly, (readonly) => {
  if (readonly) {
    isSubmitting.value = false
  }
})

const handleCancel = () => {
  if (props.config.onCancel) {
    props.config.onCancel()
  }
  emit('cancel')
}

// Handle step changes from stepper component
const handleStepChange = async (newStepIndex: number) => {
  currentStepIndex.value = newStepIndex
  
  const step = stepsRef.value[newStepIndex]
  
  // Load step data if needed
  if (step && step.loadData && !step.formData && !step.isLoading) {
    // Check if can proceed to this step
    if (newStepIndex > 0 && !canProceedFromStep(newStepIndex - 1, stepsRef.value)) {
      stepper.value?.goToStep(newStepIndex - 1)
      return
    }
    
    await loadStepData(newStepIndex)
  }
}

// Load data for a specific step
const loadStepData = async (stepIndex: number) => {
  const step = stepsRef.value[stepIndex]
  if (!step || !step.loadData) return
  
  step.isLoading = true
  triggerRef(stepsRef)
  
  try {
    const context = createStepContext()
    await step.loadData(stepsRef.value, context)
    
    // Initialize fields after loading formData
    if (step.formData) {
      step.formData.fields?.forEach(field => {
        if (step.data[field.id] === undefined) {
          if (field.default !== undefined) {
            step.data[field.id] = field.default
          } else if (field.type === 'checkbox') {
            step.data[field.id] = false
          } else if (field.type === 'checkbox-list') {
            step.data[field.id] = []
          }
        }
      })
    }
  } catch (error: any) {
    if (stepIndex > 0) {
      stepper.value?.goToStep(stepIndex - 1)
    }
  } finally {
    step.isLoading = false
    triggerRef(stepsRef)
  }
}

// Sync stepsRef with props changes
watch(() => props.config.steps, (newSteps) => {
  stepsRef.value = newSteps
}, { immediate: true })

// Initialize all steps with form data
watch(() => props.config, (config) => {
  if (config.steps.length > 0) {
    config.steps.forEach((step) => {
      if (step && step.formData) {
        step.formData.fields?.forEach(field => {
          if (step.data[field.id] === undefined) {
            if (field.default !== undefined) {
              step.data[field.id] = field.default
            } else if (field.type === 'checkbox') {
              step.data[field.id] = false
            } else if (field.type === 'checkbox-list') {
              step.data[field.id] = []
            }
          }
        })
      }
    })
    
    triggerRef(stepsRef)
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
.form-submitted-state {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  padding: 4px 0;
}

.terminal-form-stepper-generic {
    padding: 12px;
  }

.stepper-actions {
    flex-wrap: wrap;
  }

.stepper-actions :deep(.base-btn) {
    flex: 1;
    min-width: 0;
  }
}
</style>
