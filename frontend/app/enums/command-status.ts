/**
 * Command execution status
 * Tracks the lifecycle state of terminal commands
 */
export enum CommandStatus {
  RUNNING = 'running',
  SUCCESS = 'success',
  ERROR = 'error'
}
