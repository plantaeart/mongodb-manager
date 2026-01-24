import type { TerminalEntry, WebSocketMessage } from '~/types/terminal'
import { CommandStatus, TerminalCommand, WebSocketMessageType, StorageKey } from '~/enums'

/**
 * TerminalService - True Singleton
 * Manages terminal state (history, execution, favorites) for entire application
 */
class TerminalService {
  private _commandHistory = ref<TerminalEntry[]>([])
  private _isExecuting = ref(false)
  private _favorites = ref<string[]>([])
  private currentCommandId = 0
  private messageCleanup: (() => void) | null = null
  private favoritesWatchCleanup: (() => void) | null = null
  private isInitialized = false
  private sendCommandFn: ((command: string) => boolean) | null = null

  get commandHistory() {
    return readonly(this._commandHistory)
  }

  get isExecuting() {
    return readonly(this._isExecuting)
  }

  get favorites() {
    return this._favorites
  }

  /**
   * Initialize the terminal service with WebSocket integration
   */
  initialize(wsService: ReturnType<typeof useWebSocket>) {
    if (this.isInitialized) {
      return
    }

    // Store send command function
    this.sendCommandFn = wsService.sendCommand

    // Load favorites from localStorage
    this.loadFavoritesFromStorage()

    // Watch favorites and save to localStorage
    this.favoritesWatchCleanup = watch(
      this._favorites,
      () => this.saveFavoritesToStorage(),
      { deep: true }
    )

    // Register WebSocket message handler
    this.messageCleanup = wsService.onMessage((msg) => this.handleWebSocketMessage(msg))

    this.isInitialized = true
  }

  /**
   * Cleanup service resources
   */
  destroy() {
    if (this.messageCleanup) {
      this.messageCleanup()
      this.messageCleanup = null
    }
    if (this.favoritesWatchCleanup) {
      this.favoritesWatchCleanup()
      this.favoritesWatchCleanup = null
    }
    this.isInitialized = false
  }

  /**
   * Execute a command (built-in or server command)
   */
  async executeCommand(command: string) {
    const trimmedCommand = command.trim()
    if (!trimmedCommand) return

    // Handle built-in commands
    if (trimmedCommand === TerminalCommand.CLEAR) {
      this.clearHistory()
      return
    }

    if (trimmedCommand === TerminalCommand.HELP) {
      const helpEntry: TerminalEntry = {
        id: this.currentCommandId++,
        command: TerminalCommand.HELP,
        output: [
          'Available commands:',
          '',
          '  Connection Management:',
          `    ${TerminalCommand.CONNECT_LIST}              - List all MongoDB connections`,
          `    ${TerminalCommand.CONNECT_ADD}               - Add a new connection`,
          `    ${TerminalCommand.CONNECT_REMOVE} <name>     - Remove a connection`,
          `    ${TerminalCommand.CONNECT_TEST} <name>       - Test a connection`,
          '',
          '  Backup Management:',
          `    ${TerminalCommand.BACKUP_CREATE} <name>      - Create a backup`,
          `    ${TerminalCommand.BACKUP_LIST}               - List all backups`,
          `    ${TerminalCommand.BACKUP_RESTORE} <file>     - Restore a backup`,
          `    ${TerminalCommand.BACKUP_DELETE} <file>      - Delete a backup`,
          `    ${TerminalCommand.BACKUP_FOLDER_CREATE}      - Manage backup folders`,
          '',
          '  Database Operations:',
          `    ${TerminalCommand.DB_LIST}                   - List all databases`,
          `    ${TerminalCommand.DB_SWITCH} <name>          - Switch to a database`,
          `    ${TerminalCommand.COLLECTION_LIST}           - List collections`,
          '',
          '  Authentication:',
          `    ${TerminalCommand.AUTH_CHANGE_PASSWORD}      - Change your password`,
          `    ${TerminalCommand.AUTH_LOGOUT}               - Logout`,
          '',
          '  MongoDB Discovery:',
          `    ${TerminalCommand.MONGODB_DISCOVER}          - Discover MongoDB instances`,
          `    ${TerminalCommand.MONGODB_CONFIG}            - Configure discovery settings`,
          `    ${TerminalCommand.MONGODB_CONFIG_SHOW}       - Show discovery config`,
          `    ${TerminalCommand.MONGODB_CONFIG_UPDATE}     - Update discovery config`,
          '',
          '  Other:',
          `    ${TerminalCommand.CLEAR}                     - Clear terminal`,
          `    ${TerminalCommand.HELP}                      - Show this help message`
        ],
        timestamp: new Date(),
        status: CommandStatus.SUCCESS
      }
      this._commandHistory.value.push(helpEntry)
      return
    }

    // Create new entry for server command
    const entry: TerminalEntry = {
      id: this.currentCommandId++,
      command: trimmedCommand,
      output: [],
      timestamp: new Date(),
      status: CommandStatus.RUNNING
    }

    // Add to history (at the end)
    this._commandHistory.value.push(entry)

    // Limit history to 100 entries (keep most recent)
    if (this._commandHistory.value.length > 100) {
      this._commandHistory.value = this._commandHistory.value.slice(-100)
    }

    // Send command via WebSocket
    this._isExecuting.value = true
    
    if (this.sendCommandFn) {
      const sent = this.sendCommandFn(trimmedCommand)
      
      if (!sent) {
        entry.output.push('Error: Not connected to server')
        entry.status = CommandStatus.ERROR
        this._isExecuting.value = false
      }
    } else {
      entry.output.push('Error: WebSocket service not initialized')
      entry.status = CommandStatus.ERROR
      this._isExecuting.value = false
    }
  }

  /**
   * Clear command history
   */
  clearHistory() {
    this._commandHistory.value = []
  }

  /**
   * Add command to favorites
   */
  addFavorite(command: string) {
    if (!this._favorites.value.includes(command)) {
      this._favorites.value.push(command)
    }
  }

  /**
   * Remove command from favorites
   */
  removeFavorite(command: string) {
    const index = this._favorites.value.indexOf(command)
    if (index > -1) {
      this._favorites.value.splice(index, 1)
    }
  }

  /**
   * Load favorites from localStorage
   */
  private loadFavoritesFromStorage() {
    if (typeof window === 'undefined') return // SSR guard

    const savedFavorites = localStorage.getItem(StorageKey.FAVORITE_COMMANDS)
    if (savedFavorites) {
      try {
        this._favorites.value = JSON.parse(savedFavorites)
      } catch (error) {
        console.error('[TerminalService] Failed to load favorites:', error)
      }
    }
  }

  /**
   * Save favorites to localStorage
   */
  private saveFavoritesToStorage() {
    if (typeof window === 'undefined') return // SSR guard

    localStorage.setItem(StorageKey.FAVORITE_COMMANDS, JSON.stringify(this._favorites.value))
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleWebSocketMessage(message: WebSocketMessage) {
    if (message.type === WebSocketMessageType.OUTPUT && message.line) {
      // Add output line to current command (most recent = last in array)
      const currentEntry = this._commandHistory.value.at(-1)
      if (currentEntry && currentEntry.status === CommandStatus.RUNNING) {
        currentEntry.output.push(message.line)
      }
    } else if (message.type === WebSocketMessageType.COMPLETE) {
      // Mark command as complete
      const currentEntry = this._commandHistory.value.at(-1)
      if (currentEntry && currentEntry.status === CommandStatus.RUNNING) {
        currentEntry.status = message.status === CommandStatus.ERROR ? CommandStatus.ERROR : CommandStatus.SUCCESS
        this._isExecuting.value = false
      }
    } else if (message.type === WebSocketMessageType.ERROR) {
      // Handle error
      const currentEntry = this._commandHistory.value.at(-1)
      if (currentEntry && currentEntry.status === CommandStatus.RUNNING) {
        currentEntry.output.push(`Error: ${message.error || 'Unknown error'}`)
        currentEntry.status = CommandStatus.ERROR
        this._isExecuting.value = false
      }
    }
  }
}

// Create single instance
const terminalService = new TerminalService()

/**
 * Terminal Composable
 * Provides access to shared terminal service
 */
export const useTerminal = () => {
  const wsService = useWebSocket()

  // Initialize service with WebSocket on first use
  terminalService.initialize(wsService)

  // Cleanup on unmount
  // Note: We don't destroy the service, as it should persist
  // across component mounts/unmounts. Only destroy on app shutdown.
  onUnmounted(() => {
    // Service persists across component lifecycle
  })

  return {
    commandHistory: terminalService.commandHistory,
    isExecuting: terminalService.isExecuting,
    favorites: terminalService.favorites,
    executeCommand: (cmd: string) => terminalService.executeCommand(cmd),
    addFavorite: (cmd: string) => terminalService.addFavorite(cmd),
    removeFavorite: (cmd: string) => terminalService.removeFavorite(cmd)
  }
}
