/**
 * Stepper Registry
 * Maps commands to their stepper configurations using an OCP-compliant registry map.
 */

import type { StepperFormConfig } from '~/types/stepper'
import { TerminalCommand } from '~/enums'
import { createConnectUpdateStepper } from './steppers/connectUpdate'
import { createBackupFolderAddStepper } from './steppers/backupFolderAdd'
import { createBackupFolderDeleteStepper } from './steppers/backupFolderDelete'
import { createBackupCreateStepper } from './steppers/backupCreate'
import { createBackupRestoreStepper } from './steppers/backupRestore'

/**
 * Registry map: command → factory function
 * Add new stepper commands here without touching getStepperConfig().
 */
const STEPPER_REGISTRY: Partial<Record<TerminalCommand, (formId: string) => StepperFormConfig>> = {
  [TerminalCommand.CONNECT_UPDATE]: createConnectUpdateStepper,
  [TerminalCommand.BACKUP_FOLDER_ADD]: createBackupFolderAddStepper,
  [TerminalCommand.BACKUP_FOLDER_DELETE]: createBackupFolderDeleteStepper,
  [TerminalCommand.BACKUP_CREATE]: createBackupCreateStepper,
  [TerminalCommand.BACKUP_RESTORE]: createBackupRestoreStepper
}

/**
 * Get stepper configuration for a command
 * @param command - The command string (e.g., 'connect update')
 * @param formId - Unique form ID
 * @returns Stepper configuration or null if command doesn't use stepper
 */
export function getStepperConfig(command: string, formId: string): StepperFormConfig | null {
  const factory = STEPPER_REGISTRY[command as TerminalCommand]
  return factory ? factory(formId) : null
}

/**
 * Check if a command uses a stepper form
 */
export function isStepperCommand(command: string): boolean {
  return (command as TerminalCommand) in STEPPER_REGISTRY
}
