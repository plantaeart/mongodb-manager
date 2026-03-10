/**
 * EXAMPLE: Multi-step Stepper Configuration
 * 
 * This is an example showing how to create a 3-step form using the generic stepper system.
 * This example is for a hypothetical "backup create" command.
 * 
 * To add a new stepper form:
 * 1. Create a file in /config/steppers/yourCommand.ts
 * 2. Define your steps with validation and data loading logic
 * 3. Register it in /config/stepperRegistry.ts
 * 4. The TerminalFormStepperGeneric component will handle the rest!
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import { createStep } from '~/types/stepper'

/**
 * EXAMPLE: Create a 3-step backup creation form
 */
export function createBackupCreateStepper(formId: string): StepperFormConfig {
  
  // STEP 1: Select databases to backup
  const step1: StepDefinition = {
    ...createStep(
      'select_databases',
      'Select Databases',
      'Choose databases to backup',
      'i-lucide-database'
    ),
    validate: (data) => {
      // Must select at least one database
      const databases = data.databases
      return Array.isArray(databases) && databases.length > 0
    }
  }

  // STEP 2: Configure backup options
  const step2: StepDefinition = {
    ...createStep(
      'backup_options',
      'Backup Options',
      'Configure backup settings',
      'i-lucide-settings'
    ),
    loadData: async (allSteps, context) => {
      // Fetch backup options form schema
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/backup/options`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })
      
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
        
        // Set default values
        currentStep.data = {
          compression: 'gzip',
          include_indexes: true,
          parallel_threads: 4
        }
      }
    },
    validate: (data) => {
      // Validate backup path is provided
      return !!data.backup_path && !!data.compression
    }
  }

  // STEP 3: Review and confirm
  const step3: StepDefinition = {
    ...createStep(
      'review',
      'Review',
      'Review and confirm backup',
      'i-lucide-check-circle'
    ),
    // Custom component for review step (optional)
    component: 'BackupReviewStep',
    loadData: async (allSteps, context) => {
      // Prepare summary data
      const currentStep = allSteps[2]
      if (currentStep) {
        currentStep.data = {
          summary: {
            databases: allSteps[0]?.data.databases || [],
            options: allSteps[1]?.data || {},
            estimated_size: '~500 MB',
            estimated_time: '~2 minutes'
          }
        }
      }
    },
    validate: (data) => {
      // Must confirm
      return !!data.confirmed
    }
  }

  return {
    formId,
    command: 'backup create',
    steps: [step1, step2, step3],
    onSubmit: async (allData) => {
      // Submit logic handled by parent
    }
  }
}

/**
 * EXAMPLE: Another command - User registration with 4 steps
 */
export function createUserRegisterStepper(formId: string): StepperFormConfig {
  
  const step1: StepDefinition = createStep(
    'basic_info',
    'Basic Information',
    'Enter user details',
    'i-lucide-user'
  )

  const step2: StepDefinition = createStep(
    'permissions',
    'Permissions',
    'Configure user access',
    'i-lucide-shield'
  )

  const step3: StepDefinition = createStep(
    'database_access',
    'Database Access',
    'Select accessible databases',
    'i-lucide-database'
  )

  const step4: StepDefinition = createStep(
    'review',
    'Review',
    'Review and create user',
    'i-lucide-check'
  )

  return {
    formId,
    command: 'user register',
    steps: [step1, step2, step3, step4]
  }
}
