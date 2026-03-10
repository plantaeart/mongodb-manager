/**
 * Stepper Registry
 * Maps commands to their stepper configurations
 */

import type { StepperFormConfig } from '~/types/stepper'
import { createConnectUpdateStepper } from './steppers/connectUpdate'
import { createBackupFolderAddStepper } from './steppers/backupFolderAdd'
import { createBackupCreateStepper } from './steppers/backupCreate'

/**
 * Get stepper configuration for a command
 * @param command - The command string (e.g., 'connect update')
 * @param formId - Unique form ID
 * @returns Stepper configuration or null if command doesn't use stepper
 */
export function getStepperConfig(command: string, formId: string): StepperFormConfig | null {
  switch (command) {
    case 'connect update':
      return createConnectUpdateStepper(formId)
    
    case 'backup folder add':
      return createBackupFolderAddStepper(formId)
    
    case 'backup create':
      return createBackupCreateStepper(formId)
    
    default:
      return null
  }
}

/**
 * Check if a command uses a stepper form
 */
export function isStepperCommand(command: string): boolean {
  return getStepperConfig(command, 'temp') !== null
}
