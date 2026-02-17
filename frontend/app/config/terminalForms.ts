/**
 * Terminal Forms Configuration
 * 
 * Maps terminal commands to their corresponding API endpoints.
 * Form schemas are fetched from the backend at runtime.
 * 
 * Backend is the single source of truth for:
 * - Form structure (fields, types, validation)
 * - Field metadata (labels, placeholders, tooltips)
 * - Dynamic data (connection lists, options)
 * 
 * This file only maintains the command→API path mapping.
 */

/**
 * Command to API Path Registry
 * 
 * Maps terminal commands to their form API endpoints.
 * When a user runs a command that requires a form, the frontend
 * fetches the form schema from: /api/forms/{apiPath}
 */
export const COMMAND_TO_API_PATH: Record<string, string> = {
  // Connection Management Commands
  'connect add': 'connect/add',
  'connect remove': 'connect/remove',
  'connect list': 'connect/list',
  'connect test': 'connect/test',
  'connect update': 'connect/update/select',  // Step 1 of stepper
  
  // Add more command mappings here as needed
  // 'backup create': 'backup/create',
  // 'mongodb discover': 'mongodb/discover',
}

/**
 * Get API path for a given command
 * 
 * @param command - Terminal command (e.g., 'connect add')
 * @returns API path (e.g., 'connect/add') or undefined if not found
 */
export function getApiPathForCommand(command: string): string | undefined {
  return COMMAND_TO_API_PATH[command]
}

/**
 * Check if a command has a form
 * 
 * @param command - Terminal command
 * @returns True if command has a form API endpoint
 */
export function hasForm(command: string): boolean {
  return command in COMMAND_TO_API_PATH
}

/**
 * Extract command from form title
 * 
 * @param title - Form title (e.g., "Select Connection - Step 1 of 2")
 * @returns Command string (e.g., "connect update") or null
 */
export function getCommandFromFormTitle(title: string): string | null {
  // Check if title contains "Step 1"
  if (!title.includes('Step 1')) {
    return null
  }
  
  // Try to match title patterns to commands
  const titleLower = title.toLowerCase()
  
  // Match "Update MongoDB Connection - Step 1" or similar
  if (titleLower.includes('update') && titleLower.includes('connection')) {
    return 'connect update'
  }
  
  // Match "Select MongoDB Connection - Step 1" (alternative pattern)
  if (titleLower.includes('connection') && titleLower.includes('select')) {
    return 'connect update'
  }
  
  // Add more title patterns here as needed
  
  return null
}
