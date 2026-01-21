import { CommandStatus, WebSocketMessageType } from '~/enums'

export interface TerminalEntry {
  id: number
  command: string
  output: string[]
  timestamp: Date
  status: CommandStatus
}

export interface WebSocketMessage {
  type: Exclude<WebSocketMessageType, WebSocketMessageType.EXECUTE>
  line?: string
  status?: CommandStatus.SUCCESS | CommandStatus.ERROR
  exit_code?: number
  error?: string
  timestamp?: string
}

export interface CommandExecuteRequest {
  type: WebSocketMessageType.EXECUTE
  command: string
}
