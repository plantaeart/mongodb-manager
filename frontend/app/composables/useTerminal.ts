import type { TerminalEntry } from '~/types/terminal'

export const useTerminal = () => {
  const { sendCommand, onMessage } = useWebSocket()
  
  const commandHistory = ref<TerminalEntry[]>([])
  const isExecuting = ref(false)
  const currentCommandId = ref(0)
  const favorites = ref<string[]>([])

  // Load favorites from localStorage
  onMounted(() => {
    const savedFavorites = localStorage.getItem('favorite_commands')
    if (savedFavorites) {
      try {
        favorites.value = JSON.parse(savedFavorites)
      } catch (error) {
        console.error('Failed to load favorites:', error)
      }
    }
  })

  // Save favorites to localStorage
  watch(favorites, (newFavorites) => {
    localStorage.setItem('favorite_commands', JSON.stringify(newFavorites))
  }, { deep: true })

  // Listen to WebSocket messages
  onMessage((message) => {
    if (message.type === 'output' && message.line) {
      // Add output line to current command
      const currentEntry = commandHistory.value[0]
      if (currentEntry && currentEntry.status === 'running') {
        currentEntry.output.push(message.line)
      }
    } else if (message.type === 'complete') {
      // Mark command as complete
      const currentEntry = commandHistory.value[0]
      if (currentEntry && currentEntry.status === 'running') {
        currentEntry.status = message.status === 'error' ? 'error' : 'success'
        isExecuting.value = false
      }
    } else if (message.type === 'error') {
      // Handle error
      const currentEntry = commandHistory.value[0]
      if (currentEntry && currentEntry.status === 'running') {
        currentEntry.output.push(`Error: ${message.error || 'Unknown error'}`)
        currentEntry.status = 'error'
        isExecuting.value = false
      }
    }
  })

  const executeCommand = async (command: string) => {
    const trimmedCommand = command.trim()
    if (!trimmedCommand) return

    // Handle built-in commands
    if (trimmedCommand === 'clear') {
      commandHistory.value = []
      return
    }

    if (trimmedCommand === 'help') {
      const helpEntry: TerminalEntry = {
        id: currentCommandId.value++,
        command: 'help',
        output: [
          'Available commands:',
          '',
          '  Connection Management:',
          '    connect list              - List all MongoDB connections',
          '    connect add               - Add a new connection',
          '    connect remove <name>     - Remove a connection',
          '    connect test <name>       - Test a connection',
          '',
          '  Backup Management:',
          '    backup create <name>      - Create a backup',
          '    backup list               - List all backups',
          '    backup restore <file>     - Restore a backup',
          '    backup delete <file>      - Delete a backup',
          '',
          '  Database Operations:',
          '    db list                   - List all databases',
          '    db switch <name>          - Switch to a database',
          '    collection list           - List collections',
          '',
          '  Authentication:',
          '    auth change-password      - Change your password',
          '    auth logout               - Logout',
          '',
          '  Other:',
          '    clear                     - Clear terminal',
          '    help                      - Show this help message'
        ],
        timestamp: new Date(),
        status: 'success'
      }
      commandHistory.value.unshift(helpEntry)
      return
    }

    // Create new entry
    const entry: TerminalEntry = {
      id: currentCommandId.value++,
      command: trimmedCommand,
      output: [],
      timestamp: new Date(),
      status: 'running'
    }

    // Add to history (at the beginning)
    commandHistory.value.unshift(entry)

    // Limit history to 100 entries
    if (commandHistory.value.length > 100) {
      commandHistory.value = commandHistory.value.slice(0, 100)
    }

    // Send command via WebSocket
    isExecuting.value = true
    const sent = sendCommand(trimmedCommand)

    if (!sent) {
      entry.output.push('Error: Not connected to server')
      entry.status = 'error'
      isExecuting.value = false
    }
  }

  const addFavorite = (command: string) => {
    if (!favorites.value.includes(command)) {
      favorites.value.push(command)
    }
  }

  const removeFavorite = (command: string) => {
    const index = favorites.value.indexOf(command)
    if (index > -1) {
      favorites.value.splice(index, 1)
    }
  }

  return {
    commandHistory: readonly(commandHistory),
    isExecuting: readonly(isExecuting),
    favorites,
    executeCommand,
    addFavorite,
    removeFavorite
  }
}
