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
