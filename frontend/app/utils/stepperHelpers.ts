/**
 * Stepper helper utilities
 * 
 * Pure functions extracted from types/stepper.ts so that type-only imports
 * remain lightweight and functions are co-located with utils.
 */

import type { StepDefinition } from '~/types/stepper'

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
 * Helper to get all form data merged from all steps
 */
export function getAllStepData(steps: StepDefinition[]): Record<string, any> {
  return steps.reduce((acc, step) => ({ ...acc, ...step.data }), {})
}

/**
 * Helper to check if a step is valid
 */
export function isStepValid(step: StepDefinition, allSteps: StepDefinition[]): boolean {
  if (step.validate) {
    if (!step.validate(step.data, allSteps)) return false
  }
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
