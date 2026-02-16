/**
 * WebSocket message types
 * Defines the types of messages exchanged between client and server
 */
export enum WebSocketMessageType {
  EXECUTE = 'execute',           // Client sends command to execute
  OUTPUT = 'output',             // Server sends command output
  COMPLETE = 'complete',         // Server signals command completion
  ERROR = 'error',               // Server signals command error
  FORM_REQUEST = 'form_request', // Server requests form input (single-step)
  FORM_STEPPER = 'form_stepper', // Server requests form input (multi-step)
  FORM_SUBMIT = 'form_submit',   // Client submits form data
  FORM_CANCEL = 'form_cancel'    // Client cancels form
}

/**
 * Session timeout constants (in milliseconds)
 * Used for managing authentication session lifecycle
 */
export enum SessionTimeout {
  WARNING_TIME = 300000,    // 5 minutes before expiration
  REFRESH_BUFFER = 120000   // 2 minutes before expiration
}
