/**
 * Generic Stepper Form Types
 * 
 * This module defines types for building multi-step forms where each step
 * can have its own form schema, validation rules, and data loading logic.
 */

import type { FormRequestMessage, FormField } from './terminal'

/**
 * Step configuration for stepper UI
 */
export interface StepConfig {
  /** Step title shown in stepper UI */
  title: string
  /** Step description/subtitle */
  description: string
  /** Icon name (e.g., 'i-lucide-database') */
  icon?: string
  /** Whether step is disabled (computed based on validation) */
  disabled?: boolean
}

/**
 * Step data and behavior
 */
export interface StepDefinition {
  /** Unique step identifier */
  id: string
  /** UI configuration */
  config: StepConfig
  /** Form schema for this step (can be loaded lazily) */
  formData?: FormRequestMessage | null
  /** Data values for this step's fields */
  data: Record<string, any>
  /** Validation errors for this step */
  errors: Record<string, string>
  /** Whether step is currently loading data */
  isLoading: boolean
  /** Custom validation function (returns true if valid) */
  validate?: (data: Record<string, any>, allSteps: StepDefinition[]) => boolean
  /** Custom data loader (called when navigating to step) */
  loadData?: (allSteps: StepDefinition[], context: StepContext) => Promise<void>
  /** Custom component name to render (optional, overrides default field rendering) */
  component?: string
}

/**
 * Context passed to step handlers
 */
export interface StepContext {
  /** Current step index */
  currentStepIndex: number
  /** Total number of steps */
  totalSteps: number
  /** Auth token */
  token: string
  /** API base URL */
  baseUrl: string
  /** Navigate to specific step */
  goToStep: (index: number) => void
  /** Navigate to next step */
  next: () => void
  /** Navigate to previous step */
  prev: () => void
}

/**
 * Stepper form configuration
 */
export interface StepperFormConfig {
  /** Form ID */
  formId: string
  /** Command that triggered the stepper */
  command: string
  /** Step definitions */
  steps: StepDefinition[]
  /** Custom submit handler (receives all step data) */
  onSubmit?: (allData: Record<string, any>) => Promise<void>
  /** Custom cancel handler */
  onCancel?: () => void
}

/**
 * Helper to create a basic step definition
 */
export function createStep(
  id: string,
  title: string,
  description: string,
  icon?: string
): StepDefinition {
  return {
    id,
    config: {
      title,
      description,
      icon,
      disabled: false
    },
    data: {},
    errors: {},
    isLoading: false
  }
}

/**
 * Helper to get all form data from all steps
 */
export function getAllStepData(steps: StepDefinition[]): Record<string, any> {
  return steps.reduce((acc, step) => {
    return { ...acc, ...step.data }
  }, {})
}

/**
 * Helper to check if a step is valid
 */
export function isStepValid(step: StepDefinition, allSteps: StepDefinition[]): boolean {
  // If custom validation exists, use it
  if (step.validate) {
    return step.validate(step.data, allSteps)
  }
  
  // Default validation: no errors
  return Object.keys(step.errors).length === 0
}

/**
 * Helper to check if can proceed to next step
 */
export function canProceedFromStep(stepIndex: number, steps: StepDefinition[]): boolean {
  const step = steps[stepIndex]
  if (!step) return false
  
  return isStepValid(step, steps) && !step.isLoading
}
