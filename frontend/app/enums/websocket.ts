/**
 * WebSocket message types
 * Defines the types of messages exchanged between client and server
 */
export enum WebSocketMessageType {
  EXECUTE = 'execute',      // Client sends command to execute
  OUTPUT = 'output',        // Server sends command output
  COMPLETE = 'complete',    // Server signals command completion
  ERROR = 'error'           // Server signals command error
}

/**
 * Session timeout constants (in milliseconds)
 * Used for managing authentication session lifecycle
 */
export enum SessionTimeout {
  WARNING_TIME = 300000,    // 5 minutes before expiration
  REFRESH_BUFFER = 120000   // 2 minutes before expiration
}
