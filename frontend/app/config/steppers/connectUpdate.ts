/**
 * Stepper configuration for 'connect update' command
 * 
 * This demonstrates how to configure a 2-step form using the generic stepper model.
 */

import type { StepDefinition, StepperFormConfig } from '~/types/stepper'
import type { ConnectionDetails } from '~/types/connection'
import { createStep } from '~/types/stepper'
import { createLogger } from '~/services/logger'
import { buildMongoUri } from '~/utils/formHelpers'

const logger = createLogger('ConnectUpdateStepper')

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
      logger.info('Loading Step 1 data...')
      
      // Fetch form schema for Step 1 (connection list)
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/connect/update/select`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })
      
      logger.success('Step 1 form schema fetched')
      logger.object('Form schema', formSchema)
      
      // Update step formData
      const currentStep = allSteps[0]
      if (currentStep) {
        currentStep.formData = formSchema as any
        logger.success('Step 1 formData updated')
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
      logger.info('Loading Step 2 data...')
      
      // Get selected connection from Step 1
      const step1Data = allSteps[0]?.data
      let connectionName = step1Data?.connection_name
      if (Array.isArray(connectionName)) {
        connectionName = connectionName[0]
      }

      logger.debug(`Selected connection: ${connectionName}`)

      if (!connectionName) {
        logger.error('No connection selected')
        throw new Error('No connection selected')
      }

      // Fetch form schema for Step 2
      logger.info('Fetching Step 2 form schema...')
      const formSchema = await $fetch(`${context.baseUrl}/api/forms/connect/update/details`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      logger.success('Step 2 form schema fetched')
      logger.object('Form schema', formSchema)

      // Update step formData
      const currentStep = allSteps[1]
      if (currentStep) {
        currentStep.formData = formSchema as any
        logger.success('Step 2 formData updated')
      }

      // Fetch connection details to pre-populate
      logger.info(`Fetching connection details for: ${connectionName}`)
      const connectionDetails = await $fetch<ConnectionDetails>(`${context.baseUrl}/api/forms/connection-details/${connectionName}`, {
        headers: {
          'Authorization': `Bearer ${context.token}`
        }
      })

      logger.success('Connection details fetched')
      logger.object('Connection details', connectionDetails)
      
      // Backend already sends separated components (host, port, username, password, etc.)
      // Backend's urlparse() handles URL-decoding, so password is already decoded
      logger.debug(`Components from backend:`)
      logger.debug(`  - Host: ${connectionDetails.host}`)
      logger.debug(`  - Port: ${connectionDetails.port}`)
      logger.debug(`  - Username: ${connectionDetails.username}`)
      logger.debug(`  - Password length: ${connectionDetails.password?.length || 0}`)
      logger.debug(`  - Database: ${connectionDetails.database}`)
      logger.debug(`  - Auth Source: ${connectionDetails.auth_source}`)

      // Pre-populate step data with separated components
      if (currentStep) {
        // Build masked URI for simple mode display
        const maskedUri = buildMongoUri({
          host: connectionDetails.host || 'localhost',
          port: connectionDetails.port || 27017,
          username: connectionDetails.username,
          password: connectionDetails.password,
          database: connectionDetails.database,
          auth_source: connectionDetails.auth_source
        }, true)  // true = mask password
        
        logger.debug(`Built masked URI: ${maskedUri}`)
        
        // Store components directly - no more parsing needed!
        currentStep.data = {
          name: connectionDetails.name,
          description: connectionDetails.description,
          
          // Components for advanced mode
          host: connectionDetails.host,
          port: connectionDetails.port,
          username: connectionDetails.username,
          password: connectionDetails.password,  // Already decoded by backend
          database: connectionDetails.database,
          auth_source: connectionDetails.auth_source,
          
          // Masked URI for simple mode display
          uri: maskedUri
        }
        logger.success('Step 2 data pre-populated')
        logger.object('Pre-populated data', currentStep.data)
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
