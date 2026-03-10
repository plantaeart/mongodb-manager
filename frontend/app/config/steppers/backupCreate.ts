/**
 * Stepper configuration for 'backup create' command
 * 
 * 2-step form for creating a MongoDB backup
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'

/**
 * Create stepper configuration for 'backup create' command
 */
export function createBackupCreateStepper(formId: string): StepperFormConfig {
  // Step 1: Select connection
  const step1: StepDefinition = {
    ...createStep(
      'select_connection',
      'Select Connection',
      'Choose connection to backup',
      'i-lucide-database'
    ),
    loadData: async (allSteps, context) => {
      // Fetch form schema for Step 1
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/create/select`, {
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

  // Step 2: Configure backup
  const step2: StepDefinition = {
    ...createStep(
      'configure_backup',
      'Configure Backup',
      'Enter backup name and details',
      'i-lucide-save'
    ),
    loadData: async (allSteps, context) => {
      // Get selected connection from Step 1
      const step1Data = allSteps[0]?.data
      const connectionName = step1Data?.connection_name

      if (!connectionName) {
        throw new Error('No connection selected')
      }

      // Fetch form schema for Step 2
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/create/configure`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
        
        // Get active backup path from step 1 metadata
        const step1 = allSteps[0]
        const options = step1?.formData?.fields?.find((f: any) => f.id === 'connection_name')?.options || []
        const selectedOption = options.find((opt: any) => opt.value === connectionName)
        const activeBackupPath = selectedOption?.metadata?.active_backup_path || 'Not configured'
        
        // Pre-populate backup location readonly field
        const locationField = currentStep.formData?.fields?.find((f: any) => f.id === 'backup_location')
        if (locationField) {
          locationField.content = activeBackupPath
        }
        
        // Store connection_name for submission
        currentStep.data = {
          connection_name: connectionName
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[1]
      if (!step) return false

      const hasErrors = Object.keys(step.errors).length > 0
      const hasBackupName = !!data.backup_name
      
      return hasBackupName && !hasErrors
    }
  }

  return {
    formId,
    command: 'backup create',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      // Submit logic handled by parent component
    }
  }
}
