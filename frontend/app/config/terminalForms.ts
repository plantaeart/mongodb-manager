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

import { TerminalCommand } from '~/enums'

/**
 * Base path for all form API endpoints
 */
export const API_FORM_BASE = '/api/forms'

/**
 * Commands that use a dedicated form submission endpoint (/api/forms/...)
 * instead of the generic /api/commands/execute endpoint.
 */
export const FORM_ENDPOINT_COMMANDS = new Set<TerminalCommand>([
  TerminalCommand.BACKUP_DELETE,
  TerminalCommand.BACKUP_RESTORE
])

/**
 * Command to API Path Registry
 * 
 * Maps terminal commands to their form API endpoints.
 * When a user runs a command that requires a form, the frontend
 * fetches the form schema from: /api/forms/{apiPath}
 */
export const COMMAND_TO_API_PATH: Partial<Record<TerminalCommand, string>> = {
  // Connection Management Commands
  [TerminalCommand.CONNECT_ADD]: 'connect/add',
  [TerminalCommand.CONNECT_REMOVE]: 'connect/remove',
  [TerminalCommand.CONNECT_LIST]: 'connect/list',
  [TerminalCommand.CONNECT_TEST]: 'connect/test',
  [TerminalCommand.CONNECT_UPDATE]: 'connect/update/select',  // Step 1 of multi-step

  // Backup Folder Management Commands (multi-step)
  [TerminalCommand.BACKUP_FOLDER_ADD]: 'backup/folder/add/configure',  // Step 1
  [TerminalCommand.BACKUP_FOLDER_DELETE]: 'backup/folder/delete/select',  // Step 1
  [TerminalCommand.BACKUP_FOLDER_LIST]: 'backup/folder/list',

  // Backup Operation Commands (multi-step)
  [TerminalCommand.BACKUP_CREATE]: 'backup/create/select',  // Step 1
  [TerminalCommand.BACKUP_LIST]: 'backup/list',
  [TerminalCommand.BACKUP_DELETE]: 'backup/delete',
  [TerminalCommand.BACKUP_RESTORE]: 'backup/restore/select',  // Step 1
}

/**
 * Command to POST API Path Registry
 * 
 * Maps terminal commands to their POST endpoints for form submission.
 * For multi-step forms, this should point to the FINAL step's POST endpoint.
 */
export const COMMAND_TO_POST_API_PATH: Partial<Record<TerminalCommand, string>> = {
  // Single-step forms (same as GET)
  [TerminalCommand.CONNECT_ADD]: 'connect/add',
  [TerminalCommand.CONNECT_REMOVE]: 'connect/remove',
  [TerminalCommand.CONNECT_TEST]: 'connect/test',
  [TerminalCommand.BACKUP_FOLDER_LIST]: 'backup/folder/list',
  [TerminalCommand.BACKUP_LIST]: 'backup/list',
  [TerminalCommand.BACKUP_DELETE]: 'backup/delete',

  // Multi-step forms (final step POST endpoint)
  [TerminalCommand.BACKUP_FOLDER_ADD]: 'backup/folder/add/configure',  // Step 2 POST
  [TerminalCommand.BACKUP_FOLDER_DELETE]: 'backup/folder/delete/confirm',  // Step 2 POST
  [TerminalCommand.BACKUP_CREATE]: 'backup/create/configure',  // Step 2 POST
  [TerminalCommand.BACKUP_RESTORE]: 'backup/restore/configure',  // Step 2 POST
}

/**
 * Get API path for a given command
 * 
 * @param command - Terminal command
 * @returns API path (e.g., 'connect/add') or undefined if not found
 */
export function getApiPathForCommand(command: string): string | undefined {
  return COMMAND_TO_API_PATH[command as TerminalCommand]
}

/**
 * Get POST API path for a given command (for form submission)
 * 
 * For multi-step forms, returns the FINAL step's POST endpoint.
 * For single-step forms, returns the same as getApiPathForCommand.
 * 
 * @param command - Terminal command
 * @returns POST API path or undefined if not found
 */
export function getPostApiPathForCommand(command: string): string | undefined {
  return COMMAND_TO_POST_API_PATH[command as TerminalCommand] ?? COMMAND_TO_API_PATH[command as TerminalCommand]
}

/**
 * Check if a command has a form
 * 
 * @param command - Terminal command
 * @returns True if command has a form API endpoint
 */
export function hasForm(command: string): boolean {
  return (command as TerminalCommand) in COMMAND_TO_API_PATH
}

/**
 * Extract command from form title
 * 
 * @param title - Form title (e.g., "Select Connection - Step 1 of 2")
 * @returns Command string or null
 */
export function getCommandFromFormTitle(title: string): string | null {
  if (!title.includes('Step 1')) {
    return null
  }

  const titleLower = title.toLowerCase()

  if (titleLower.includes('update') && titleLower.includes('connection')) {
    return TerminalCommand.CONNECT_UPDATE
  }

  if (titleLower.includes('add') && titleLower.includes('backup') && titleLower.includes('folder')) {
    return TerminalCommand.BACKUP_FOLDER_ADD
  }

  if (titleLower.includes('create') && titleLower.includes('backup')) {
    return TerminalCommand.BACKUP_CREATE
  }

  if (titleLower.includes('restore') && titleLower.includes('backup')) {
    return TerminalCommand.BACKUP_RESTORE
  }

  return null
}
