/**
 * Stepper configuration for 'backup folder add' command
 * 
 * 2-step form for adding a backup folder to a connection
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'
import { createLogger } from '~/services/logger'

const logger = createLogger('BackupFolderAdd')

/**
 * Create stepper configuration for 'backup folder add' command
 */
export function createBackupFolderAddStepper(formId: string): StepperFormConfig {
  logger.info('Creating stepper config for formId:', formId)
  
  // Step 1: Configure folder path
  const step1: StepDefinition = {
    ...createStep(
      'configure_folder',
      'Configure Folder',
      'Enter backup folder path and options',
      'i-lucide-folder-plus'
    ),
    loadData: async (allSteps, context) => {
      logger.info('📂 [Step 1] Loading configure form data')
      logger.debug('API endpoint: /api/forms/backup/folder/add/configure')
      
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/add/configure`, {
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
      
      logger.debug('[Step 1] Validation:', { hasFolderPath, hasErrors })
      
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
      logger.info('🔗 [Step 2] Loading select connection form data')
      logger.debug('API endpoint: /api/forms/backup/folder/add/select')
      
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/folder/add/select`, {
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
        logger.debug('[Step 2] Form fields:', currentStep.formData?.fields?.map((f: any) => f.id))
      }
    },
    validate: (data, allSteps) => {
      const connectionName = data.connection_name
      const hasSelection = !!connectionName
      
      const step = allSteps[1]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false
      
      logger.debug('[Step 2] Validation:', { hasSelection, hasErrors })
      
      return hasSelection && !hasErrors
    }
  }

  logger.info('Stepper config created with 2 steps')
  
  return {
    formId,
    command: 'backup folder add',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      logger.info('Submitting backup folder add with data:', allData)
    }
  }
}
