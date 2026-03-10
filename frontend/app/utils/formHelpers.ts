/**
 * Form Helper Utilities
 * 
 * Reusable utilities for form handling
 */

import type { FormField } from '~/types/terminal'

/**
 * Connection component interface for building URIs
 */
export interface ConnectionComponents {
  username?: string
  password?: string
  host: string
  port: number
  database?: string
  auth_source?: string
}

/**
 * Build MongoDB URI from separated components
 * This is the ONLY place where we build URIs - no more regex parsing!
 * 
 * @param components - Connection components (host, port, username, password, etc.)
 * @param maskPassword - Whether to mask password with *** (for display only)
 * @returns MongoDB URI string
 * 
 * @example
 * // Build URI for submission (URL-encoded password)
 * buildMongoUri({ host: 'localhost', port: 27017, username: 'user', password: 'p@ss!' }, false)
 * // Returns: "mongodb://user:p%40ss%21@localhost:27017"
 * 
 * // Build URI for display (masked password)
 * buildMongoUri({ host: 'localhost', port: 27017, username: 'user', password: 'p@ss!' }, true)
 * // Returns: "mongodb://user:***@localhost:27017"
 */
export function buildMongoUri(components: ConnectionComponents, maskPassword: boolean = false): string {
  const { username, password, host, port, database, auth_source } = components
  
  let uri = 'mongodb://'
  
  // Add credentials if provided
  if (username && password) {
    const displayPassword = maskPassword ? '***' : encodeURIComponent(password)
    uri += `${username}:${displayPassword}@`
  }
  
  // Add host:port
  uri += `${host}:${port}`
  
  // Add database if provided
  if (database) {
    uri += `/${database}`
  }
  
  // Add query params
  const params = []
  if (auth_source) {
    params.push(`authSource=${auth_source}`)
  }
  
  if (params.length > 0) {
    uri += `?${params.join('&')}`
  }
  
  return uri
}

/**
 * Filter connection form fields based on mode
 * 
 * @param fields - All form fields
 * @param isAdvancedMode - Whether in advanced mode
 * @returns Filtered fields array
 */
export function filterConnectionFields(fields: FormField[], isAdvancedMode: boolean): FormField[] {
  if (!isAdvancedMode) {
    // Simple mode: show name, uri, description
    return fields.filter(f => ['name', 'uri', 'description'].includes(f.id))
  } else {
    // Advanced mode: show all except uri
    return fields.filter(f => f.id !== 'uri')
  }
}

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
 * DEPRECATED: Old URI masking function - kept for backward compatibility
 * Use buildMongoUri() with maskPassword=true instead
 */
export function maskMongoUriPassword(uri: string): string {
  if (!uri) return uri
  
  try {
    const uriMatch = uri.match(/^(mongodb:\/\/[^:]+:)([^@]+)(@.+)$/)
    if (uriMatch && uriMatch[1] && uriMatch[2] && uriMatch[3]) {
      const prefix = uriMatch[1]
      const suffix = uriMatch[3]
      return `${prefix}***${suffix}`
    }
  } catch (error) {
    console.warn('Failed to mask URI password:', error)
  }
  
  return uri
}

/**
 * Process connection form data before submission
 * Used for connection commands (connect add, connect update)
 * 
 * NOTE: This function is now a simple pass-through.
 * The backend expects URL-encoded URIs which we build using buildMongoUri()
 * The backend's urlparse() handles decoding automatically.
 * 
 * @param data - Form data object
 * @param command - Command name
 * @returns Processed data (unchanged)
 */
export function decodeConnectionData(data: Record<string, any>, command: string): Record<string, any> {
  // Simply return data unchanged
  // All URI encoding is handled by buildMongoUri()
  return { ...data }
}
