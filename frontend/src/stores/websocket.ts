import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { AutoReconnectWebSocket, createWebSocketUrl } from '@/utils/websocket'
import type { WSMessage, WSConnectionStatus, ConsoleMessage } from '@/types'

export const useWebSocketStore = defineStore('websocket', () => {
  // State
  const consoleWs = ref<AutoReconnectWebSocket | null>(null)
  const statusWs = ref<AutoReconnectWebSocket | null>(null)
  
  const consoleStatus = ref<WSConnectionStatus>({
    connected: false,
    reconnecting: false
  })
  
  const statusConnectionStatus = ref<WSConnectionStatus>({
    connected: false,
    reconnecting: false
  })
  
  const consoleMessages = ref<ConsoleMessage[]>([])
  const maxConsoleMessages = 1000

  // Computed
  const isConsoleConnected = computed(() => consoleStatus.value.connected)
  const isStatusConnected = computed(() => statusConnectionStatus.value.connected)
  const isAnyConnected = computed(() => isConsoleConnected.value || isStatusConnected.value)

  // Actions
  function initConsoleWebSocket() {
    if (consoleWs.value) {
      return
    }

    const wsUrl = createWebSocketUrl('/console/ws')
    consoleWs.value = new AutoReconnectWebSocket(wsUrl)

    // Handle connection status changes
    consoleWs.value.onConnectionChange((status) => {
      consoleStatus.value = status
      console.log('Console WebSocket status:', status)
    })

    // Handle incoming messages
    consoleWs.value.onMessage((message: WSMessage) => {
      handleConsoleMessage(message)
    })

    // Connect
    consoleWs.value.connect().catch((error) => {
      console.error('Failed to connect console WebSocket:', error)
    })
  }

  function initStatusWebSocket() {
    if (statusWs.value) {
      return
    }

    const wsUrl = createWebSocketUrl('/status/ws')
    statusWs.value = new AutoReconnectWebSocket(wsUrl)

    // Handle connection status changes
    statusWs.value.onConnectionChange((status) => {
      statusConnectionStatus.value = status
      console.log('Status WebSocket status:', status)
    })

    // Handle incoming messages
    statusWs.value.onMessage((message: WSMessage) => {
      handleStatusMessage(message)
    })

    // Connect
    statusWs.value.connect().catch((error) => {
      console.error('Failed to connect status WebSocket:', error)
    })
  }

  function handleConsoleMessage(message: WSMessage) {
    console.log('Console message received:', message)

    switch (message.type) {
      case 'console_log':
        addConsoleMessage({
          type: message.type,
          timestamp: message.timestamp,
          data: message.data
        })
        break

      case 'connection_established':
        console.log('Console connection established:', message.data)
        break

      case 'pong':
        // Handle ping/pong
        break

      default:
        console.warn('Unknown console message type:', message.type)
    }
  }

  function handleStatusMessage(message: WSMessage) {
    console.log('Status message received:', message)

    switch (message.type) {
      case 'status_update':
        // Handle server status updates
        break

      case 'player_event':
        // Handle player events
        break

      default:
        console.warn('Unknown status message type:', message.type)
    }
  }

  function addConsoleMessage(message: ConsoleMessage) {
    consoleMessages.value.push(message)

    // Limit the number of stored messages
    if (consoleMessages.value.length > maxConsoleMessages) {
      consoleMessages.value.splice(0, consoleMessages.value.length - maxConsoleMessages)
    }
  }

  function sendConsoleCommand(command: string) {
    if (!consoleWs.value || !isConsoleConnected.value) {
      console.warn('Console WebSocket is not connected')
      return false
    }

    try {
      consoleWs.value.sendCommand(command)
      return true
    } catch (error) {
      console.error('Failed to send console command:', error)
      return false
    }
  }

  function clearConsoleMessages() {
    consoleMessages.value = []
  }

  function connectAll() {
    initConsoleWebSocket()
    initStatusWebSocket()
  }

  function disconnectAll() {
    if (consoleWs.value) {
      consoleWs.value.disconnect()
      consoleWs.value = null
    }

    if (statusWs.value) {
      statusWs.value.disconnect()
      statusWs.value = null
    }

    // Reset status
    consoleStatus.value = { connected: false, reconnecting: false }
    statusConnectionStatus.value = { connected: false, reconnecting: false }
  }

  function reconnectConsole() {
    if (consoleWs.value) {
      consoleWs.value.disconnect()
      consoleWs.value = null
    }
    initConsoleWebSocket()
  }

  function reconnectStatus() {
    if (statusWs.value) {
      statusWs.value.disconnect()
      statusWs.value = null
    }
    initStatusWebSocket()
  }

  // Auto-connect on store creation
  connectAll()

  return {
    // State
    consoleStatus,
    statusConnectionStatus,
    consoleMessages,

    // Computed
    isConsoleConnected,
    isStatusConnected,
    isAnyConnected,

    // Actions
    initConsoleWebSocket,
    initStatusWebSocket,
    sendConsoleCommand,
    clearConsoleMessages,
    connectAll,
    disconnectAll,
    reconnectConsole,
    reconnectStatus,
    addConsoleMessage
  }
})