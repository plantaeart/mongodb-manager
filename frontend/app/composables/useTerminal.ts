/**
 * useTerminal — Terminal composable (god-class slimmed via SRP)
 *
 * Storage persistence  → useTerminalStorage
 * HTTP fetch / submit  → useTerminalHttp
 * This file now owns only: state orchestration, WebSocket wiring, command routing.
 */

import type { TerminalEntry, WebSocketMessage, FormRequestMessage, FileWidgetData } from '~/types/terminal'
import { CommandStatus, TerminalCommand, WebSocketMessageType, StorageKey, TerminalConfig } from '~/enums'
import { getApiPathForCommand } from '~/config/terminalForms'
import { useTerminalStorage } from '~/composables/useTerminalStorage'
import { useTerminalHttp } from '~/composables/useTerminalHttp'
import { stripBackupSuffix } from '~/utils/backupHelpers'

/**
 * TerminalService - True Singleton
 * Manages terminal state (history, execution, favorites) for the entire app.
 */

/** Commands that open a file-widget instead of the normal form system */
const FILE_WIDGET_COMMANDS = new Set<TerminalCommand>([
  TerminalCommand.BACKUP_EXPORT,
  TerminalCommand.BACKUP_IMPORT,
  TerminalCommand.CONNECT_EXPORT,
  TerminalCommand.CONNECT_IMPORT,
])

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
  private activeFormId: string | null = null
  private activeWidgetEntryId: string | null = null

  // Lazily resolved helpers (need Nuxt context)
  private storage = useTerminalStorage()
  private http = useTerminalHttp()

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

  get hasActiveWidget() {
    return this.activeWidgetEntryId !== null
  }

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------

  initialize(wsService: ReturnType<typeof useWebSocket>) {
    if (this.isInitialized) return

    this.sendCommandFn = wsService.sendCommand

    // Restore persisted state
    this._favorites.value = this.storage.loadFavoritesFromStorage()
    this._commandHistory.value = this.storage.loadHistoryFromStorage()

    // Persist changes automatically
    this.favoritesWatchCleanup = watch(
      this._favorites,
      () => this.storage.saveFavoritesToStorage(this._favorites.value),
      { deep: true }
    )
    this.historyWatchCleanup = watch(
      this._commandHistory,
      () => this.storage.saveHistoryToStorage(this._commandHistory.value),
      { deep: true }
    )

    // Wire WebSocket messages
    this.messageCleanup = wsService.onMessage((msg) => this.handleWebSocketMessage(msg))

    this.isInitialized = true
  }

  destroy() {
    this.messageCleanup?.()
    this.favoritesWatchCleanup?.()
    this.historyWatchCleanup?.()
    this.messageCleanup = null
    this.favoritesWatchCleanup = null
    this.historyWatchCleanup = null
    this.isInitialized = false
  }

  // ---------------------------------------------------------------------------
  // Command execution
  // ---------------------------------------------------------------------------

  async executeCommand(command: string) {
    const trimmed = command.trim()
    if (!trimmed) return

    if (trimmed === TerminalCommand.CLEAR) {
      this.clearHistory()
      return
    }

    if (trimmed === TerminalCommand.HELP) {
      this._commandHistory.value.push(this.buildHelpEntry())
      return
    }

    const formPath = getApiPathForCommand(trimmed)
    if (formPath) {
      await this.executeFormCommand(trimmed, formPath)
      return
    }

    // File-widget commands (export / import via browser file APIs)
    if (FILE_WIDGET_COMMANDS.has(trimmed as TerminalCommand)) {
      await this.executeFileWidgetCommand(trimmed as TerminalCommand)
      return
    }

    // WebSocket-based command
    const entry: TerminalEntry = {
      id: this.currentCommandId++,
      command: trimmed,
      output: [],
      timestamp: new Date(),
      status: CommandStatus.RUNNING
    }
    this._commandHistory.value.push(entry)

    // Cap in-memory history
    if (this._commandHistory.value.length > TerminalConfig.MAX_HISTORY) {
      this._commandHistory.value = this._commandHistory.value.slice(-TerminalConfig.MAX_HISTORY)
    }

    this._isExecuting.value = true

    if (this.sendCommandFn) {
      const sent = this.sendCommandFn(trimmed)
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

  // ---------------------------------------------------------------------------
  // Form lifecycle
  // ---------------------------------------------------------------------------

  private async executeFormCommand(command: string, formPath: string) {
    const authStore = useAuthStore()
    if (!authStore.token) {
      this.addErrorEntry(command, 'Not authenticated')
      return
    }

    const result = await this.http.fetchForm(formPath, authStore.token, this.currentCommandId, command)

    if (!result.ok) {
      this.addErrorEntry(command, result.error)
      return
    }

    const entry: TerminalEntry = {
      id: this.currentCommandId++,
      command,
      output: [],
      timestamp: new Date(),
      status: CommandStatus.RUNNING,
      form: result.formData
    }

    this.activeFormId = result.formId
    this._commandHistory.value.push(entry)
  }

  async submitForm(formId: string, data: Record<string, any>) {
    if (this.activeFormId !== formId) return

    const formEntry = this._commandHistory.value.find(e => e.form?.form_id === formId)
    if (!formEntry) {
      this.activeFormId = null
      return
    }

    const authStore = useAuthStore()
    if (!authStore.token) {
      formEntry.output = ['Error: Not authenticated']
      formEntry.status = CommandStatus.ERROR
      this.activeFormId = null
      return
    }

    try {
      const { decodeConnectionData } = await import('~/utils/fieldHelpers')
      const processedData = decodeConnectionData({ ...data }, formEntry.command)

      const result = await this.http.submitFormData(formEntry.command, processedData, authStore.token)

      if (result.success) {
        formEntry.output = result.output ?? ['Command executed successfully']
        formEntry.status = CommandStatus.SUCCESS
      } else {
        formEntry.output = [result.error ?? 'Command failed']
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

  cancelForm(formId: string) {
    if (this.activeFormId !== formId) return

    const entry = this._commandHistory.value.find(e => e.form?.form_id === formId)
    if (entry) {
      entry.status = CommandStatus.ERROR
      entry.output.push('Form cancelled by user')
    }

    this.activeFormId = null
    this._isExecuting.value = false
  }

  // ---------------------------------------------------------------------------
  // File-widget lifecycle (backup/connect export & import)
  // ---------------------------------------------------------------------------

  private async executeFileWidgetCommand(command: TerminalCommand) {
    const authStore = useAuthStore()
    if (!authStore.token) {
      this.addErrorEntry(command, 'Not authenticated')
      return
    }

    const config = useRuntimeConfig()
    const baseUrl = config.public.apiUrl as string
    const headers = { Authorization: `Bearer ${authStore.token}` }

    let widgetData: FileWidgetData

    try {
      if (command === TerminalCommand.BACKUP_EXPORT) {
        const opts = await $fetch<{ backups: { value: string; label: string; description?: string }[] }>(
          `${baseUrl}/api/transfer/backup/export/options`,
          { headers }
        )
        widgetData = { mode: 'backup-export', backupOptions: opts.backups }
      } else if (command === TerminalCommand.BACKUP_IMPORT) {
        const opts = await $fetch<{ folders: { value: string; label: string }[] }>(
          `${baseUrl}/api/transfer/backup/import/options`,
          { headers }
        )
        widgetData = { mode: 'backup-import', folderOptions: opts.folders.map(f => ({ value: f.value, label: stripBackupSuffix(f.label) })) }
      } else if (command === TerminalCommand.CONNECT_EXPORT) {
        widgetData = { mode: 'connect-export' }
      } else {
        // CONNECT_IMPORT
        widgetData = { mode: 'connect-import' }
      }
    } catch (err: any) {
      this.addErrorEntry(command, `Failed to load options: ${err?.message ?? 'Unknown error'}`)
      return
    }

    const entryId = String(this.currentCommandId++)
    const entry: TerminalEntry = {
      id: entryId,
      command,
      output: [],
      timestamp: new Date(),
      status: CommandStatus.RUNNING,
      fileWidget: widgetData,
    }

    this.activeWidgetEntryId = entryId
    this._commandHistory.value.push(entry)
    this._isExecuting.value = true
  }

  resolveFileWidget(entryId: string, message: string) {
    if (this.activeWidgetEntryId !== entryId) return

    const entry = this._commandHistory.value.find(e => String(e.id) === entryId)
    if (entry) {
      entry.output = [message]
      entry.status = CommandStatus.SUCCESS
      // Keep fileWidget so the readonly done-state shows
    }

    this.activeWidgetEntryId = null
    this._isExecuting.value = false
  }

  cancelFileWidget(entryId: string) {
    if (this.activeWidgetEntryId !== entryId) return

    const entry = this._commandHistory.value.find(e => String(e.id) === entryId)
    if (entry) {
      entry.status = CommandStatus.ERROR
      entry.output.push('Cancelled by user')
    }

    this.activeWidgetEntryId = null
    this._isExecuting.value = false
  }

  // ---------------------------------------------------------------------------
  // Favorites
  // ---------------------------------------------------------------------------

  addFavorite(command: string) {
    if (!this._favorites.value.includes(command)) {
      this._favorites.value.push(command)
    }
  }

  removeFavorite(command: string) {
    const index = this._favorites.value.indexOf(command)
    if (index > -1) this._favorites.value.splice(index, 1)
  }

  // ---------------------------------------------------------------------------
  // History
  // ---------------------------------------------------------------------------

  clearHistory() {
    this._commandHistory.value = []
    this.storage.clearHistoryStorage()
  }

  // ---------------------------------------------------------------------------
  // WebSocket message handling
  // ---------------------------------------------------------------------------

  private handleWebSocketMessage(message: WebSocketMessage) {
    if (message.type === WebSocketMessageType.FORM_REQUEST) {
      const formMessage = message as FormRequestMessage
      this._commandHistory.value.push({
        id: formMessage.form_id,
        command: '',
        output: [],
        timestamp: new Date(),
        status: CommandStatus.RUNNING,
        form: formMessage
      })
      this.activeFormId = formMessage.form_id
      this._isExecuting.value = true
      return
    }

    const current = this._commandHistory.value.at(-1)

    if (message.type === WebSocketMessageType.OUTPUT && message.line) {
      if (current?.status === CommandStatus.RUNNING) {
        current.output.push(message.line)
      }
    } else if (message.type === WebSocketMessageType.COMPLETE) {
      if (current?.status === CommandStatus.RUNNING) {
        current.status = message.status === CommandStatus.ERROR
          ? CommandStatus.ERROR
          : CommandStatus.SUCCESS
        this._isExecuting.value = false
      }
    } else if (message.type === WebSocketMessageType.ERROR) {
      if (current?.status === CommandStatus.RUNNING) {
        current.output.push(`Error: ${message.error || 'Unknown error'}`)
        current.status = CommandStatus.ERROR
        this._isExecuting.value = false
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  private addErrorEntry(command: string, errorMessage: string) {
    this._commandHistory.value.push({
      id: this.currentCommandId++,
      command,
      output: [errorMessage],
      timestamp: new Date(),
      status: CommandStatus.ERROR
    })
  }

  private buildHelpEntry(): TerminalEntry {
    return {
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
        `    ${TerminalCommand.CONNECT_EXPORT}            - Export connections to JSON file`,
        `    ${TerminalCommand.CONNECT_IMPORT}            - Import connections from JSON file`,
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
        `    ${TerminalCommand.BACKUP_EXPORT}             - Export backup as ZIP to your computer`,
        `    ${TerminalCommand.BACKUP_IMPORT}             - Import backup ZIP from your computer`,
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
  }
}

// Singleton instance
const terminalService = new TerminalService()

/**
 * Terminal Composable — provides access to the shared terminal service.
 */
export const useTerminal = () => {
  const wsService = useWebSocket()
  terminalService.initialize(wsService)

  return {
    commandHistory: terminalService.commandHistory,
    isExecuting: terminalService.isExecuting,
    hasActiveForm: computed(() => terminalService.hasActiveForm),
    hasActiveWidget: computed(() => terminalService.hasActiveWidget),
    favorites: terminalService.favorites,
    executeCommand: (cmd: string) => terminalService.executeCommand(cmd),
    clearHistory: () => terminalService.clearHistory(),
    addFavorite: (cmd: string) => terminalService.addFavorite(cmd),
    removeFavorite: (cmd: string) => terminalService.removeFavorite(cmd),
    submitForm: (formId: string, data: Record<string, any>) => terminalService.submitForm(formId, data),
    cancelForm: (formId: string) => terminalService.cancelForm(formId),
    resolveFileWidget: (entryId: string, message: string) => terminalService.resolveFileWidget(entryId, message),
    cancelFileWidget: (entryId: string) => terminalService.cancelFileWidget(entryId)
  }
}
