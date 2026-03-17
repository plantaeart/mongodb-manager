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
  'connect update': 'connect/update/select',  // Step 1 of multi-step
  
  // Backup Folder Management Commands (multi-step)
  'backup folder add': 'backup/folder/add/configure',  // Step 1: Configure folder path
  'backup folder delete': 'backup/folder/delete/select',  // Step 1: Select connection
  'backup folder list': 'backup/folder/list',
  
  // Backup Operation Commands (multi-step)
  'backup create': 'backup/create/select',  // Step 1
  'backup list': 'backup/list',
  'backup delete': 'backup/delete',
  'backup restore': 'backup/restore/select',  // Step 1
}

/**
 * Command to POST API Path Registry
 * 
 * Maps terminal commands to their POST endpoints for form submission.
 * For multi-step forms, this should point to the FINAL step's POST endpoint.
 */
export const COMMAND_TO_POST_API_PATH: Record<string, string> = {
  // Single-step forms (same as GET)
  'connect add': 'connect/add',
  'connect remove': 'connect/remove',
  'connect test': 'connect/test',
  'backup folder list': 'backup/folder/list',
  'backup list': 'backup/list',
  'backup delete': 'backup/delete',
  
  // Multi-step forms (final step POST endpoint)
  'backup folder add': 'backup/folder/add/configure',  // Step 2 POST
  'backup folder delete': 'backup/folder/delete/confirm',  // Step 2 POST
  'backup create': 'backup/create/configure',  // Step 2 POST
  'backup restore': 'backup/restore/configure',  // Step 2 POST
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
 * Get POST API path for a given command (for form submission)
 * 
 * For multi-step forms, returns the FINAL step's POST endpoint.
 * For single-step forms, returns the same as getApiPathForCommand.
 * 
 * @param command - Terminal command (e.g., 'backup restore')
 * @returns POST API path (e.g., 'backup/restore/configure') or undefined if not found
 */
export function getPostApiPathForCommand(command: string): string | undefined {
  return COMMAND_TO_POST_API_PATH[command] || COMMAND_TO_API_PATH[command]
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
  
  // Match "Add Backup Folder - Step 1"
  if (titleLower.includes('add') && titleLower.includes('backup') && titleLower.includes('folder')) {
    return 'backup folder add'
  }
  
  // Match "Create Backup - Step 1"
  if (titleLower.includes('create') && titleLower.includes('backup')) {
    return 'backup create'
  }
  
  // Match "Restore Backup - Step 1"
  if (titleLower.includes('restore') && titleLower.includes('backup')) {
    return 'backup restore'
  }
  
  // Add more title patterns here as needed
  
  return null
}
