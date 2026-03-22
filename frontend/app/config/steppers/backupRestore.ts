/**
 * Stepper configuration for 'backup restore' command
 * 
 * 2-step form for restoring a MongoDB backup
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/utils/stepperHelpers'
import { loadStepSchema } from '~/composables/useStepLoader'

/**
 * Create stepper configuration for 'backup restore' command
 */
export function createBackupRestoreStepper(formId: string): StepperFormConfig {
  // Step 1: Select backup
  const step1: StepDefinition = {
    ...createStep(
      'select_backup',
      'Select Backup',
      'Choose backup to restore',
      'i-lucide-archive'
    ),
    loadData: async (allSteps, context) => {
      // Fetch form schema for Step 1
      const currentStep = allSteps[0]
      if (currentStep) {
        await loadStepSchema(`${context.baseUrl}/api/forms/backup/restore/select`, context.token, currentStep)
      }
    },
    validate: (data, allSteps) => {
      const backupSelector = data.backup_selector
      const hasSelection = !!backupSelector
      
      const step = allSteps[0]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false
      
      return hasSelection && !hasErrors
    }
  }

  // Step 2: Configure restore
  const step2: StepDefinition = {
    ...createStep(
      'configure_restore',
      'Configure Restore',
      'Select connection and restore options',
      'i-lucide-upload'
    ),
    loadData: async (allSteps, context) => {
      // Get selected backup from Step 1
      const step1Data = allSteps[0]?.data
      const backupSelector = step1Data?.backup_selector

      if (!backupSelector) {
        throw new Error('No backup selected')
      }

      // Fetch form schema for Step 2 with backup_selector query param
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/restore/configure`, {
        headers: {
          Authorization: `Bearer ${context.token}`
        },
        params: {
          backup_selector: backupSelector
        }
      })

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
        
        // Store backup_selector for submission
        currentStep.data = {
          backup_selector: backupSelector
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[1]
      if (!step) return false

      const hasErrors = Object.keys(step.errors).length > 0
      const hasConnection = !!data.connection_name
      const hasConfirmation = !!data.confirmation
      
      return hasConnection && hasConfirmation && !hasErrors
    }
  }

  return {
    formId,
    command: 'backup restore',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      // Submit logic handled by parent component
    }
  }
}
