/**
 * Form Helper Utilities
 * 
 * Reusable utilities for form handling
 */

import type { FormField } from '~/types/terminal'

/**
 * Get appropriate field component based on field type
 * 
 * @param fieldType - Field type string
 * @returns Component name
 */
export function getFieldComponentName(fieldType: string): string {
  switch (fieldType) {
    case 'password':
      return 'TerminalPasswordField'
    case 'number':
      return 'TerminalNumberField'
    case 'checkbox-list':
      return 'TerminalCheckboxListField'
    case 'readonly':
      return 'TerminalReadonlyField'
    case 'list':
      return 'TerminalListField'
    case 'textarea':
      return 'TerminalTextField' // TODO: Create TerminalTextAreaField
    case 'select':
      return 'TerminalTextField' // TODO: Create TerminalSelectField
    default:
      return 'TerminalTextField'
  }
}

/**
 * Process connection form data before submission
 * Used for connection commands (connect add, connect update)
 * 
 * This function:
 * - Converts empty strings to null for optional fields
 * - Converts port string to number
 * - Removes empty/null optional fields
 * 
 * @param data - Form data object
 * @param command - Command name
 * @returns Processed data with proper types
 */
export function decodeConnectionData(data: Record<string, any>, command: string): Record<string, any> {
  const processed = { ...data }
  
  // Convert port to number (required field)
  if (processed.port !== undefined && processed.port !== null && processed.port !== '') {
    processed.port = parseInt(String(processed.port), 10)
  } else {
    // If empty, use default port
    processed.port = 27017
  }
  
  // Clean up empty optional string fields - convert to null or remove
  const optionalStringFields = ['username', 'password', 'database', 'auth_source', 'description']
  for (const field of optionalStringFields) {
    if (processed[field] === '') {
      processed[field] = null
    }
  }
  
  // Remove null values for cleaner submission (backend handles missing optional fields)
  Object.keys(processed).forEach(key => {
    if (processed[key] === null) {
      delete processed[key]
    }
  })
  
  return processed
}
