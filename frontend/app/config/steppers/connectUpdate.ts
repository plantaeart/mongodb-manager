/**
 * Stepper configuration for 'connect update' command
 * 
 * This demonstrates how to configure a 2-step form using the generic stepper model.
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import type { ConnectionDetails } from '~/types/connection'
import { createStep } from '~/types/stepper'

/**
 * Create stepper configuration for 'connect update' command
 */
export function createConnectUpdateStepper(formId: string): StepperFormConfig {
  // Step 1: Select which connection to update
  const step1: StepDefinition = {
    ...createStep(
      'select_connection',
      'Select Connection',
      'Choose which connection to update',
      'i-lucide-database'
    ),
    component: 'CommandsConnectUpdateSelectConnection',  // Use custom component
    loadData: async (allSteps, context) => {
      // Fetch form schema for Step 1 (connection list)
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/connect/update/select`, {
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
      // Validate that exactly one connection is selected
      const connectionName = data.connection_name
      
      const hasSelection = Array.isArray(connectionName) 
        ? connectionName.length === 1 
        : !!connectionName
      
      const step = allSteps[0]
      const hasErrors = step ? Object.keys(step.errors).length > 0 : false
      
      return hasSelection && !hasErrors
    }
  }

  // Step 2: Update connection details
  const step2: StepDefinition = {
    ...createStep(
      'update_details',
      'Update Details',
      'Modify connection settings',
      'i-lucide-edit'
    ),
    component: 'CommandsConnectUpdateUpdateDetails',  // Use custom component for mode toggle
    loadData: async (allSteps, context) => {
      // Get selected connection from Step 1
      const step1Data = allSteps[0]?.data
      let connectionName = step1Data?.connection_name
      if (Array.isArray(connectionName)) {
        connectionName = connectionName[0]
      }

      if (!connectionName) {
        throw new Error('No connection selected')
      }

      // Fetch form schema for Step 2
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/connect/update/details`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
      }

      // Fetch connection details to pre-populate
      const connectionDetails = await $fetch<ConnectionDetails>(`${context.baseUrl}/api/forms/connection-details/${connectionName}`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      // Decode password if it contains URL encoding artifacts
      let decodedPassword = connectionDetails.password
      // Note: Backend now handles URL-decoding, so this is just a safety check
      try {
        // Check if password contains % encoding (like %40, %3F, etc.)
        if (decodedPassword && decodedPassword.includes('%')) {
          decodedPassword = decodeURIComponent(decodedPassword)
        }
      } catch (error) {
        // Keep original if decode fails
      }

      // Pre-populate step data with components ONLY
      // NO URI building - backend will handle URI construction when needed
      if (currentStep) {
        currentStep.data = {
          name: connectionDetails.name,
          description: connectionDetails.description,
          host: connectionDetails.host,
          port: connectionDetails.port,
          username: connectionDetails.username,
          password: decodedPassword,  // Use decoded password
          database: connectionDetails.database,
          auth_source: connectionDetails.auth_source
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[1]
      if (!step) return false

      const hasErrors = Object.keys(step.errors).length > 0
      
      // Component-based validation: require name, host, port
      // (regardless of simple/advanced mode UI display)
      const required = ['name', 'host', 'port']
      const allRequiredFilled = required.every(
        id => data[id] !== undefined && data[id] !== ''
      )
      
      // If username provided, password should be too
      const hasUsername = !!data.username
      const hasPassword = !!data.password
      const authValid = !hasUsername || (hasUsername && hasPassword)
      
      return allRequiredFilled && authValid && !hasErrors
    }
  }

  return {
    formId,
    command: 'connect update',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      // Submit logic will be handled by parent component
    }
  }
}
