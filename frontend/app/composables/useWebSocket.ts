import type { WebSocketMessage, CommandExecuteRequest } from '~/types/terminal'

export const useWebSocket = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const messageHandlers = ref<Array<(msg: WebSocketMessage) => void>>([])
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5

  const connect = () => {
    if (!authStore.isAuthenticated || !authStore.token) {
      console.warn('Cannot connect WebSocket: not authenticated')
      return
    }

    if (socket.value?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    const wsUrl = `${config.public.wsUrl}/ws/terminal?token=${authStore.token}`
    
    try {
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        console.log('WebSocket connected')
        isConnected.value = true
        reconnectAttempts.value = 0
      }

      socket.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          messageHandlers.value.forEach(handler => handler(message))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      socket.value.onclose = () => {
        console.log('WebSocket disconnected')
        isConnected.value = false
        socket.value = null

        // Attempt to reconnect
        if (reconnectAttempts.value < maxReconnectAttempts && authStore.isAuthenticated) {
          reconnectAttempts.value++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.value})`)
          setTimeout(connect, delay)
        }
      }

      socket.value.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    isConnected.value = false
    reconnectAttempts.value = maxReconnectAttempts // Prevent auto-reconnect
  }

  const sendCommand = (command: string) => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      return false
    }

    const message: CommandExecuteRequest = {
      type: 'execute',
      command
    }

    socket.value.send(JSON.stringify(message))
    return true
  }

  const onMessage = (handler: (msg: WebSocketMessage) => void) => {
    messageHandlers.value.push(handler)
    
    // Return cleanup function
    return () => {
      const index = messageHandlers.value.indexOf(handler)
      if (index > -1) {
        messageHandlers.value.splice(index, 1)
      }
    }
  }

  // Auto-connect when authenticated
  watch(() => authStore.isAuthenticated, (authenticated) => {
    if (authenticated) {
      connect()
    } else {
      disconnect()
    }
  })

  // Connect on mount if already authenticated
  onMounted(() => {
    if (authStore.isAuthenticated) {
      connect()
    }
  })

  // Disconnect on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected: readonly(isConnected),
    sendCommand,
    onMessage,
    connect,
    disconnect
  }
}
