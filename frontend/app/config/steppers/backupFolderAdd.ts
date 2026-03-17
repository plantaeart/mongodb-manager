/**
 * Stepper configuration for 'backup folder add' command
 * 
 * 2-step form for adding a backup folder to a connection
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'

/**
 * Create stepper configuration for 'backup folder add' command
 */
export function createBackupFolderAddStepper(formId: string): StepperFormConfig {
  // Step 1: Configure folder path
  const step1: StepDefinition = {
    ...createStep(
      'configure_folder',
      'Configure Folder',
      'Enter backup folder path and options',
      'i-lucide-folder-plus'
    ),
    loadData: async (allSteps, context) => {
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/add/configure`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Update step formData
      const currentStep = allSteps[0]
      if (currentStep) {
        currentStep.formData = formSchema as any

        // Initialize with default values
        currentStep.data = {
          create_if_missing: true,
          set_as_active: true
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[0]
      if (!step) return false

      const hasErrors = Object.keys(step.errors).length > 0
      const hasFolderPath = !!data.folder_path

      return hasFolderPath && !hasErrors
    }
  }

  // Step 2: Select connection
  const step2: StepDefinition = {
    ...createStep(
      'select_connection',
      'Select Connection',
      'Choose which connection this backup folder will be used for',
      'i-lucide-database'
    ),
    loadData: async (allSteps, context) => {
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/add/select`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
      }
    },
    validate: (data, allSteps) => {
      const connectionName = data.connection_name
      const hasSelection = !!connectionName

      const step = allSteps[1]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false

      return hasSelection && !hasErrors
    }
  }

  return {
    formId,
    command: 'backup folder add',
    steps: [step1, step2],
    onSubmit: async (_allData) => {}
  }
}
