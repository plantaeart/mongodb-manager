/**
 * Stepper configuration for 'backup folder delete' command
 * 
 * 2-step form for deleting a backup folder from a connection
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'

/**
 * Create stepper configuration for 'backup folder delete' command
 */
export function createBackupFolderDeleteStepper(formId: string): StepperFormConfig {
  // Step 1: Select connection (only shows connections with backup folders)
  const step1: StepDefinition = {
    ...createStep(
      'select_connection',
      'Select Connection',
      'Choose which connection\'s backup folder to delete',
      'i-lucide-database'
    ),
    loadData: async (allSteps, context) => {
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/delete/select`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Update step formData
      const currentStep = allSteps[0]
      if (currentStep) {
        currentStep.formData = formSchema as any
      }
    },
    validate: (data, allSteps) => {
      const connectionName = data.connection_name
      const hasSelection = !!connectionName

      const step = allSteps[0]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false

      return hasSelection && !hasErrors
    }
  }

  // Step 2: Select folder and confirm deletion
  const step2: StepDefinition = {
    ...createStep(
      'confirm_delete',
      'Delete Folder',
      'Select the folder to delete and confirm',
      'i-lucide-trash-2'
    ),
    loadData: async (allSteps, context) => {
      // Get selected connection from Step 1
      const step1Data = allSteps[0]?.data
      const connectionName = step1Data?.connection_name

      if (!connectionName) {
        throw new Error('No connection selected')
      }

      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/delete/confirm`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any

        // Populate folder_path options from step 1 metadata (backup_paths of selected connection)
        const step1 = allSteps[0]
        const options = step1?.formData?.fields?.find((f: any) => f.id === 'connection_name')?.options || []
        const selectedOption = options.find((opt: any) => opt.value === connectionName)
        const backupPaths: string[] = selectedOption?.metadata?.backup_paths || []

        // Update folder_path field options
        const folderField = currentStep.formData?.fields?.find((f: any) => f.id === 'folder_path')
        if (folderField && backupPaths.length > 0) {
          folderField.options = backupPaths.map((path: string) => ({
            value: path,
            label: path
          }))
        }

        // Pre-set connection_name so it is included in the submission params
        currentStep.data = {
          connection_name: connectionName
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[1]
      if (!step) return false

      const hasErrors = Object.keys(step.errors).length > 0
      const hasFolderPath = !!data.folder_path
      const hasConfirmation = !!data.confirmation

      return hasFolderPath && hasConfirmation && !hasErrors
    }
  }

  return {
    formId,
    command: 'backup folder delete',
    steps: [step1, step2],
    onSubmit: async (_allData) => {}
  }
}
