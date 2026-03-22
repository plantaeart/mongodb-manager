/**
 * Field helper utilities
 * 
 * Renamed from formHelpers.ts. Contains only runtime-used helpers.
 * The dead `getFieldComponentName()` (string-based, not used at runtime) has been removed —
 * actual component resolution uses component references via useFieldComponent.ts.
 */

/**
 * Process connection form data before submission.
 * Used for connection commands (connect add, connect update).
 * 
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
    processed.port = 27017
  }

  // Clean up empty optional string fields — convert to null
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
