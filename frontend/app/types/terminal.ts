export interface TerminalEntry {
  id: number
  command: string
  output: string[]
  timestamp: Date
  status: 'running' | 'success' | 'error'
}

export interface WebSocketMessage {
  type: 'output' | 'complete' | 'error'
  line?: string
  status?: 'success' | 'error'
  exit_code?: number
  error?: string
  timestamp?: string
}

export interface CommandExecuteRequest {
  type: 'execute'
  command: string
}
