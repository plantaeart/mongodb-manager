import type { TerminalEntry, WebSocketMessage, FormRequestMessage, FormSubmitRequest, FormCancelRequest } from '~/types/terminal'
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
  private sendMessageFn: ((message: any) => boolean) | null = null
  private activeFormId: string | null = null

  get commandHistory() {
    return readonly(this._commandHistory)
  }

  get isExecuting() {
    return readonly(this._isExecuting)
  }

  get favorites() {
    return this._favorites
  }

  get hasActiveForm() {
    return this.activeFormId !== null
  }

  /**
   * Initialize the terminal service with WebSocket integration
   */
  initialize(wsService: ReturnType<typeof useWebSocket>) {
    if (this.isInitialized) {
      return
    }

    // Store send functions
    this.sendCommandFn = wsService.sendCommand
    this.sendMessageFn = wsService.send

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

    // Check if this command requires a form (HTTP-based)
    const formCommandPath = this.getFormCommandPath(trimmedCommand)
    if (formCommandPath) {
      await this.executeFormCommand(trimmedCommand, formCommandPath)
      return
    }

    // Create new entry for server command (WebSocket-based)
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
   * Check if a command requires a form and return its path
   */
  private getFormCommandPath(command: string): string | null {
    const formCommands: Record<string, string> = {
      'connect add': 'connect/add',
      'connect remove': 'connect/remove',
      // Add more form commands here as needed
      // 'backup create': 'backup/create',
      // 'mongodb discover': 'mongodb/discover',
    }
    
    return formCommands[command] || null
  }

  /**
   * Execute a command that requires a form (HTTP-based)
   */
  private async executeFormCommand(command: string, formPath: string) {
    try {
      // Get auth token
      const authStore = useAuthStore()
      const token = authStore.token
      
      if (!token) {
        this.addErrorEntry(command, 'Not authenticated')
        return
      }

      // Fetch form schema from backend
      const config = useRuntimeConfig()
      const backendUrl = config.public.backendUrl || 'http://localhost:9000'
      
      const formResponse = await fetch(`${backendUrl}/api/forms/${formPath}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!formResponse.ok) {
        this.addErrorEntry(command, `Failed to fetch form: ${formResponse.statusText}`)
        return
      }

      const formData = await formResponse.json() as any
      
      // Generate a unique form ID
      const formId = `form-${this.currentCommandId}`
      
      // Add form_id to the form data (required by FormRequestMessage type)
      const formWithId: FormRequestMessage = {
        type: 'form_request',
        form_id: formId,
        title: formData.title,
        description: formData.description,
        fields: formData.fields,
        actions: formData.actions
      }

      // Create terminal entry with form
      const entry: TerminalEntry = {
        id: this.currentCommandId++,
        command,
        output: [],
        timestamp: new Date(),
        status: CommandStatus.RUNNING,
        form: formWithId
      }

      // Set active form
      this.activeFormId = formId

      // Add to history
      this._commandHistory.value.push(entry)

      // Wait for form submission (handled by submitForm method)
      // Form will be submitted via submitForm() when user clicks submit button

    } catch (error) {
      this.addErrorEntry(command, `Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Add an error entry to history
   */
  private addErrorEntry(command: string, errorMessage: string) {
    const entry: TerminalEntry = {
      id: this.currentCommandId++,
      command,
      output: [errorMessage],
      timestamp: new Date(),
      status: CommandStatus.ERROR
    }
    this._commandHistory.value.push(entry)
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
   * Submit form data
   */
  async submitForm(formId: string, data: Record<string, any>) {
    if (this.activeFormId !== formId) {
      console.warn('[TerminalService] Cannot submit form: form ID mismatch')
      return
    }

    // Find the form entry in history
    const formEntry = this._commandHistory.value.find(e => e.form?.form_id === formId)
    if (!formEntry) {
      console.error('[TerminalService] Form entry not found')
      this.activeFormId = null
      return
    }

    try {
      // Get auth token
      const authStore = useAuthStore()
      const token = authStore.token
      
      if (!token) {
        formEntry.output = ['Error: Not authenticated']
        formEntry.status = CommandStatus.ERROR
        this.activeFormId = null
        return
      }

      // Execute command via HTTP API
      const config = useRuntimeConfig()
      const backendUrl = config.public.backendUrl || 'http://localhost:9000'
      
      const response = await fetch(`${backendUrl}/api/commands/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          command: formEntry.command,
          params: data
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      // Update entry with result
      if (result.success) {
        formEntry.output = result.output ? result.output.split('\n').filter((line: string) => line.trim()) : ['Command executed successfully']
        formEntry.status = CommandStatus.SUCCESS
      } else {
        formEntry.output = result.error ? [result.error] : ['Command failed']
        formEntry.status = CommandStatus.ERROR
      }

    } catch (error) {
      formEntry.output = [`Error: ${error instanceof Error ? error.message : 'Unknown error'}`]
      formEntry.status = CommandStatus.ERROR
    } finally {
      this.activeFormId = null
      this._isExecuting.value = false
    }
  }

  /**
   * Cancel form
   */
  cancelForm(formId: string) {
    if (this.activeFormId !== formId) {
      console.warn('[TerminalService] Cannot cancel form: form ID mismatch')
      return
    }

    // Update form entry status to error (cancelled)
    const entry = this._commandHistory.value.find(e => e.form?.form_id === formId)
    if (entry) {
      entry.status = CommandStatus.ERROR
      entry.output.push('Form cancelled by user')
    }

    this.activeFormId = null
    this._isExecuting.value = false
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
    // Handle form request
    if (message.type === WebSocketMessageType.FORM_REQUEST) {
      const formMessage = message as FormRequestMessage
      const formEntry: TerminalEntry = {
        id: formMessage.form_id,
        command: '', // No command for forms
        output: [],
        timestamp: new Date(),
        status: CommandStatus.RUNNING,
        form: formMessage
      }
      this._commandHistory.value.push(formEntry)
      this.activeFormId = formMessage.form_id
      this._isExecuting.value = true // Keep true - form blocks new commands
      return
    }

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
    hasActiveForm: computed(() => terminalService.hasActiveForm),
    favorites: terminalService.favorites,
    executeCommand: (cmd: string) => terminalService.executeCommand(cmd),
    addFavorite: (cmd: string) => terminalService.addFavorite(cmd),
    removeFavorite: (cmd: string) => terminalService.removeFavorite(cmd),
    submitForm: (formId: string, data: Record<string, any>) => terminalService.submitForm(formId, data),
    cancelForm: (formId: string) => terminalService.cancelForm(formId)
  }
}
