/**
 * Stepper configuration for 'backup folder delete' command
 * 
 * 2-step form for deleting a backup folder from a connection
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'
import { createLogger } from '~/services/logger'

const logger = createLogger('BackupFolderDelete')

/**
 * Create stepper configuration for 'backup folder delete' command
 */
export function createBackupFolderDeleteStepper(formId: string): StepperFormConfig {
  logger.info('Creating stepper config for formId:', formId)

  // Step 1: Select connection (only shows connections with backup folders)
  const step1: StepDefinition = {
    ...createStep(
      'select_connection',
      'Select Connection',
      'Choose which connection\'s backup folder to delete',
      'i-lucide-database'
    ),
    loadData: async (allSteps, context) => {
      logger.info('🔗 [Step 1] Loading select connection form data')
      logger.debug('API endpoint: /api/forms/backup/folder/delete/select')

      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/delete/select`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      logger.debug('[Step 1] Received form schema:', formSchema)

      // Update step formData
      const currentStep = allSteps[0]
      if (currentStep) {
        currentStep.formData = formSchema as any
        logger.success('[Step 1] Form data set to step 0')
        logger.debug('[Step 1] Form fields:', currentStep.formData?.fields?.map((f: any) => f.id))
      }
    },
    validate: (data, allSteps) => {
      const connectionName = data.connection_name
      const hasSelection = !!connectionName

      const step = allSteps[0]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false

      logger.debug('[Step 1] Validation:', { hasSelection, hasErrors })

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
      logger.info('🗑️ [Step 2] Loading confirm delete form data')
      logger.debug('API endpoint: /api/forms/backup/folder/delete/confirm')

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

      logger.debug('[Step 2] Received form schema:', formSchema)

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
        logger.success('[Step 2] Form data set to step 1')

        // Populate folder_path options from step 1 metadata (backup_paths of selected connection)
        const step1 = allSteps[0]
        const options = step1?.formData?.fields?.find((f: any) => f.id === 'connection_name')?.options || []
        const selectedOption = options.find((opt: any) => opt.value === connectionName)
        const backupPaths: string[] = selectedOption?.metadata?.backup_paths || []

        logger.debug('[Step 2] Backup paths for connection:', backupPaths)

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

      logger.debug('[Step 2] Validation:', { hasFolderPath, hasConfirmation, hasErrors })

      return hasFolderPath && hasConfirmation && !hasErrors
    }
  }

  logger.info('Stepper config created with 2 steps')

  return {
    formId,
    command: 'backup folder delete',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      logger.info('Submitting backup folder delete with data:', allData)
    }
  }
}
