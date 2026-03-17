import type { TerminalEntry, WebSocketMessage, FormRequestMessage, FormSubmitRequest, FormCancelRequest } from '~/types/terminal'
import { CommandStatus, TerminalCommand, WebSocketMessageType, StorageKey } from '~/enums'
import { getApiPathForCommand, getPostApiPathForCommand } from '~/config/terminalForms'

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
  private historyWatchCleanup: (() => void) | null = null
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

    // Load command history from localStorage
    this.loadHistoryFromStorage()

    // Watch favorites and save to localStorage
    this.favoritesWatchCleanup = watch(
      this._favorites,
      () => this.saveFavoritesToStorage(),
      { deep: true }
    )

    // Watch history and save to localStorage
    this.historyWatchCleanup = watch(
      this._commandHistory,
      () => this.saveHistoryToStorage(),
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
    if (this.historyWatchCleanup) {
      this.historyWatchCleanup()
      this.historyWatchCleanup = null
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
          `    ${TerminalCommand.CONNECT_REMOVE}            - Remove connection(s)`,
          `    ${TerminalCommand.CONNECT_TEST}              - Test connection(s)`,
          `    ${TerminalCommand.CONNECT_UPDATE}            - Update a connection`,
          '',
          '  Backup Folder Management:',
          `    ${TerminalCommand.BACKUP_FOLDER_ADD}         - Add backup folder to connection`,
          `    ${TerminalCommand.BACKUP_FOLDER_DELETE}      - Delete a backup folder`,
          `    ${TerminalCommand.BACKUP_FOLDER_LIST}        - List backup folders`,
          '',
          '  Backup Operations:',
          `    ${TerminalCommand.BACKUP_CREATE}             - Create a new backup`,
          `    ${TerminalCommand.BACKUP_LIST}               - List all backups`,
          `    ${TerminalCommand.BACKUP_DELETE}             - Delete a backup`,
          `    ${TerminalCommand.BACKUP_RESTORE}            - Restore from backup`,
          '',
          '  Authentication:',
          `    ${TerminalCommand.AUTH_CHANGE_PASSWORD}      - Change your password`,
          `    ${TerminalCommand.AUTH_LOGOUT}               - Logout`,
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
    return getApiPathForCommand(command) || null
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
      
      // Add form_id and originating command to the form data
      // IMPORTANT: step and total_steps MUST be forwarded from backend response
      const formWithId: FormRequestMessage = {
        type: 'form_request',
        form_id: formId,
        command,                          // Originating terminal command
        title: formData.title,
        description: formData.description,
        step: formData.step,              // Forward step info from backend
        total_steps: formData.total_steps, // Forward total_steps from backend
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
    if (typeof window !== 'undefined') {
      localStorage.removeItem(StorageKey.TERMINAL_HISTORY)
    }
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
      return
    }

    // Find the form entry in history
    const formEntry = this._commandHistory.value.find(e => e.form?.form_id === formId)
    if (!formEntry) {
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

      // Send components directly to backend (backend builds URI when needed)
      const { decodeConnectionData } = await import('~/utils/formHelpers')
      
      const dataToSubmit = { ...data }
      const processedData = decodeConnectionData(dataToSubmit, formEntry.command)

      // Get POST API path for this command (final step for multi-step forms)
      const postApiPath = getPostApiPathForCommand(formEntry.command)
      
      // Determine which endpoint to use
      // Commands with dedicated form submission endpoints should use /api/forms/{path}
      // Others fall back to /api/commands/execute
      const config = useRuntimeConfig()
      const backendUrl = config.public.backendUrl || 'http://localhost:9000'
      
      const hasFormEndpoint = postApiPath && this.shouldUseFormEndpoint(formEntry.command)
      const endpoint = hasFormEndpoint ? `${backendUrl}/api/forms/${postApiPath}` : `${backendUrl}/api/commands/execute`
      const requestBody = hasFormEndpoint ? processedData : { command: formEntry.command, params: processedData }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      // Update entry with result
      if (result.success) {
        formEntry.output = result.output ? result.output.split('\n').filter((line: string) => line.trim()) : [result.message || 'Command executed successfully']
        formEntry.status = CommandStatus.SUCCESS
      } else {
        formEntry.output = result.error ? [result.error] : [result.message || 'Command failed']
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
   * Check if command should use dedicated form submission endpoint
   */
  private shouldUseFormEndpoint(command: string): boolean {
    // Commands that have dedicated form submission endpoints
    const formEndpointCommands = [
      'backup delete',
      'backup restore',
      // Add more commands here as they get form endpoints
    ]
    
    return formEndpointCommands.includes(command)
  }

  /**
   * Cancel form
   */
  cancelForm(formId: string) {
    if (this.activeFormId !== formId) {
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
        // Failed to load favorites
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
   * Load command history from localStorage
   * Only restores completed entries (SUCCESS or ERROR) — skips active forms
   */
  private loadHistoryFromStorage() {
    if (typeof window === 'undefined') return // SSR guard

    const saved = localStorage.getItem(StorageKey.TERMINAL_HISTORY)
    if (!saved) return

    try {
      const parsed: TerminalEntry[] = JSON.parse(saved)
      this._commandHistory.value = parsed.map(e => {
        const entry = { ...e, timestamp: new Date(e.timestamp), form: undefined }
        // Any entry that was still running (active form) gets marked as interrupted
        if (entry.status === CommandStatus.RUNNING) {
          entry.status = CommandStatus.ERROR
          entry.output = ['Session interrupted — please re-run the command']
        }
        return entry
      })
    } catch {
      // Corrupt data — silently discard
      localStorage.removeItem(StorageKey.TERMINAL_HISTORY)
    }
  }

  /**
   * Save command history to localStorage
   * Only persists completed entries (SUCCESS or ERROR), capped at 50 most recent
   */
  private saveHistoryToStorage() {
    if (typeof window === 'undefined') return // SSR guard

    // Persist all entries (including RUNNING ones so they can be marked interrupted on reload)
    // Strip the live form object — it cannot be serialized meaningfully
    const toSave = this._commandHistory.value
      .slice(-50) // Keep last 50 entries
      .map(e => ({ ...e, form: undefined }))

    localStorage.setItem(StorageKey.TERMINAL_HISTORY, JSON.stringify(toSave))
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
    clearHistory: () => terminalService.clearHistory(),
    addFavorite: (cmd: string) => terminalService.addFavorite(cmd),
    removeFavorite: (cmd: string) => terminalService.removeFavorite(cmd),
    submitForm: (formId: string, data: Record<string, any>) => terminalService.submitForm(formId, data),
    cancelForm: (formId: string) => terminalService.cancelForm(formId)
  }
}
