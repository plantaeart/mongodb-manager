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
    component: 'ConnectUpdateStep2',  // Use custom component for mode toggle
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

      // Pre-populate step data
      if (currentStep) {
        currentStep.data = {
          name: connectionDetails.name,
          uri: connectionDetails.uri,
          description: connectionDetails.description,
          host: connectionDetails.host,
          port: connectionDetails.port,
          username: connectionDetails.username,
          password: connectionDetails.password,
          database: connectionDetails.database,
          auth_source: connectionDetails.auth_source
        }
      }
    },
    validate: (data, allSteps) => {
      const step = allSteps[1]
      if (!step) return false

      const hasErrors = Object.keys(step.errors).length > 0
      
      // Check if we're in advanced mode (based on presence of host field)
      const isAdvancedMode = !!data.host
      
      if (isAdvancedMode) {
        // Advanced mode: require name, host, port
        const required = ['name', 'host', 'port']
        const allRequiredFilled = required.every(
          id => data[id] !== undefined && data[id] !== ''
        )
        
        // If username provided, password should be too
        const hasUsername = !!data.username
        const hasPassword = !!data.password
        const authValid = hasUsername === hasPassword
        
        return allRequiredFilled && authValid && !hasErrors
      } else {
        // Simple mode: require name, uri
        const required = ['name', 'uri']
        const allRequiredFilled = required.every(
          id => data[id] !== undefined && data[id] !== ''
        )
        
        return allRequiredFilled && !hasErrors
      }
    }
  }

  return {
    formId,
    command: 'connect update',
    steps: [step1, step2],
    onSubmit: async (allData) => {
      // Submit logic will be handled by parent component
      // This is just for reference
      console.log('Submitting connect update with data:', allData)
    }
  }
}
