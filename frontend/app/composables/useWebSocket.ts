import type { WebSocketMessage, CommandExecuteRequest } from '~/types/terminal'
import { WebSocketMessageType } from '~/enums'

/**
 * WebSocket Service - True Singleton
 * Manages a single WebSocket connection for the entire application
 */
class WebSocketService {
  private socket: WebSocket | null = null
  private _isConnected = ref(false)
  private messageHandlers: Array<(msg: WebSocketMessage) => void> = []
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private wsUrl: string = ''
  private token: string = ''
  private isConnecting = false

  constructor() {
    // Service initialized
  }

  get isConnected() {
    return readonly(this._isConnected)
  }

  connect(token: string, wsUrl: string) {
    if (!token) {
      console.warn('[WebSocketService] Cannot connect: no token provided')
      return
    }

    // Prevent multiple simultaneous connection attempts
    if (this.isConnecting) {
      return
    }

    if (this.socket?.readyState === WebSocket.OPEN) {
      return
    }

    // Close existing connection if any
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }

    this.token = token
    this.wsUrl = wsUrl
    this.isConnecting = true

    const url = `${wsUrl}/ws/terminal?token=${token}`
    
    try {
      this.socket = new WebSocket(url)

      this.socket.onopen = () => {
        this._isConnected.value = true
        this.reconnectAttempts = 0
        this.isConnecting = false
      }

      this.socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // Notify all registered handlers
          this.messageHandlers.forEach(handler => {
            try {
              handler(message)
            } catch (error) {
              console.error('[WebSocketService] Error in message handler:', error)
            }
          })
        } catch (error) {
          console.error('[WebSocketService] Failed to parse WebSocket message:', error)
        }
      }

      this.socket.onclose = (event) => {
        this._isConnected.value = false
        this.socket = null
        this.isConnecting = false

        // Attempt to reconnect if we have auth token
        if (this.reconnectAttempts < this.maxReconnectAttempts && this.token) {
          this.reconnectAttempts++
          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
          setTimeout(() => this.connect(this.token, this.wsUrl), delay)
        }
      }

      this.socket.onerror = (error) => {
        console.error('[WebSocketService] WebSocket error:', error)
        this.isConnecting = false
      }
    } catch (error) {
      console.error('[WebSocketService] Failed to create WebSocket:', error)
      this.isConnecting = false
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    
    this._isConnected.value = false
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent auto-reconnect
    this.token = ''
    this.isConnecting = false
  }

  sendCommand(command: string): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('[WebSocketService] Cannot send command: WebSocket not connected')
      return false
    }

    const message: CommandExecuteRequest = {
      type: WebSocketMessageType.EXECUTE,
      command
    }

    try {
      this.socket.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('[WebSocketService] Failed to send command:', error)
      return false
    }
  }

  send(message: any): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('[WebSocketService] Cannot send message: WebSocket not connected')
      return false
    }

    try {
      this.socket.send(JSON.stringify(message))
      return true
    } catch (error) {
      console.error('[WebSocketService] Failed to send message:', error)
      return false
    }
  }

  onMessage(handler: (msg: WebSocketMessage) => void): () => void {
    this.messageHandlers.push(handler)
    
    // Return cleanup function
    return () => {
      const index = this.messageHandlers.indexOf(handler)
      if (index > -1) {
        this.messageHandlers.splice(index, 1)
      }
    }
  }
}

// Create single instance
const wsService = new WebSocketService()

/**
 * WebSocket Composable
 * Sets up authentication-based connection management
 */
export const useWebSocket = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  // Watch auth state and connect/disconnect accordingly
  // This runs for every component that calls useWebSocket, but affects the same service instance
  watch(() => authStore.isAuthenticated, (authenticated) => {
    if (authenticated && authStore.token) {
      wsService.connect(authStore.token, config.public.wsUrl)
    } else {
      wsService.disconnect()
    }
  }, { immediate: true })

  // Return the service methods
  return {
    isConnected: wsService.isConnected,
    sendCommand: (command: string) => wsService.sendCommand(command),
    send: (message: any) => wsService.send(message),
    onMessage: (handler: (msg: WebSocketMessage) => void) => wsService.onMessage(handler),
    connect: () => {
      if (authStore.token) {
        wsService.connect(authStore.token, config.public.wsUrl)
      }
    },
    disconnect: () => wsService.disconnect()
  }
}
