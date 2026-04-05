/**
 * Terminal configuration constants
 */
export const TerminalConfig = {
  /** Maximum number of history entries kept in memory */
  MAX_HISTORY: 100,
  /** Maximum number of history entries persisted to localStorage */
  PERSIST_HISTORY: 50,
  /** Maximum number of local input history entries */
  MAX_LOCAL_INPUT_HISTORY: 50,
  /** Maximum number of autocomplete suggestions shown */
  MAX_SUGGESTIONS: 10,
  /** Field count threshold for switching to two-column layout */
  TWO_COLUMN_THRESHOLD: 4
} as const

/**
 * Terminal command strings
 * All available commands in the terminal interface
 */
export enum TerminalCommand {
  // Built-in commands
  HELP = 'help',
  CLEAR = 'clear',
  
  // Connection management
  CONNECT_LIST = 'connect list',
  CONNECT_ADD = 'connect add',
  CONNECT_REMOVE = 'connect remove',
  CONNECT_TEST = 'connect test',
  CONNECT_UPDATE = 'connect update',
  CONNECT_EXPORT = 'connect export',
  CONNECT_IMPORT = 'connect import',
  
  // Backup folder management
  BACKUP_FOLDER_ADD = 'backup folder add',
  BACKUP_FOLDER_DELETE = 'backup folder delete',
  BACKUP_FOLDER_LIST = 'backup folder list',
  
  // Backup operations
  BACKUP_CREATE = 'backup create',
  BACKUP_LIST = 'backup list',
  BACKUP_DELETE = 'backup delete',
  BACKUP_RESTORE = 'backup restore',
  BACKUP_EXPORT = 'backup export',
  BACKUP_IMPORT = 'backup import',
  
  // Authentication
  AUTH_CHANGE_PASSWORD = 'auth change-password',
  AUTH_LOGOUT = 'auth logout'
}
