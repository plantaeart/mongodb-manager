/**
 * WebSocket connection status display text
 * User-facing connection status labels
 */
export enum ConnectionStatus {
  CONNECTED = 'Connected',
  DISCONNECTED = 'Disconnected',
  CONNECTING = 'Connecting'
}

/**
 * CSS classes for connection status styling
 * Applied to status indicators based on connection state
 */
export enum ConnectionStatusClass {
  CONNECTED = 'status-connected',
  DISCONNECTED = 'status-disconnected',
  CONNECTING = 'status-connecting'
}

/**
 * MongoDB connection status
 * Represents the state of a MongoDB connection
 */
export enum MongoConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected'
}
