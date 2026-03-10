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
  
  // Backup operations
  BACKUP_CREATE = 'backup create',
  BACKUP_LIST = 'backup list',
  BACKUP_RESTORE = 'backup restore',
  BACKUP_DELETE = 'backup delete',
  BACKUP_FOLDER_CREATE = 'create-backup-folder',
  
  // Authentication
  AUTH_CHANGE_PASSWORD = 'auth change-password',
  AUTH_LOGOUT = 'auth logout'
}
