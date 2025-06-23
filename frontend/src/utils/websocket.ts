import type { WSMessage, WSConnectionStatus } from '@/types'

export type MessageHandler = (message: WSMessage) => void
export type ConnectionHandler = (status: WSConnectionStatus) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private messageHandlers: MessageHandler[] = []
  private connectionHandlers: ConnectionHandler[] = []
  private connectionStatus: WSConnectionStatus = {
    connected: false,
    reconnecting: false
  }

  constructor(url: string) {
    this.url = url
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.updateConnectionStatus({ connected: false, reconnecting: true })
        
        this.ws = new WebSocket(this.url)
        
        this.ws.onopen = () => {
          console.log('WebSocket connected:', this.url)
          this.reconnectAttempts = 0
          this.updateConnectionStatus({ connected: true, reconnecting: false })
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
        
        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason)
          this.updateConnectionStatus({ connected: false, reconnecting: false })
          
          // Attempt reconnection if not manually closed
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect()
          }
        }
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.updateConnectionStatus({ 
            connected: false, 
            reconnecting: false, 
            error: 'Connection error' 
          })
          reject(error)
        }
        
      } catch (error) {
        this.updateConnectionStatus({ 
          connected: false, 
          reconnecting: false, 
          error: 'Failed to create WebSocket connection' 
        })
        reject(error)
      }
    })
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      this.updateConnectionStatus({ 
        connected: false, 
        reconnecting: false, 
        error: 'Max reconnection attempts reached' 
      })
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    this.updateConnectionStatus({ connected: false, reconnecting: true })
    
    setTimeout(() => {
      this.connect().catch(() => {
        // Reconnection failed, will try again in onclose handler
      })
    }, delay)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }
    this.updateConnectionStatus({ connected: false, reconnecting: false })
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected, cannot send message')
    }
  }

  sendCommand(command: string) {
    this.send({
      type: 'command',
      command: command,
      timestamp: new Date().toISOString()
    })
  }

  ping() {
    this.send({
      type: 'ping',
      timestamp: new Date().toISOString()
    })
  }

  // Event handling
  onMessage(handler: MessageHandler) {
    this.messageHandlers.push(handler)
  }

  offMessage(handler: MessageHandler) {
    const index = this.messageHandlers.indexOf(handler)
    if (index !== -1) {
      this.messageHandlers.splice(index, 1)
    }
  }

  onConnectionChange(handler: ConnectionHandler) {
    this.connectionHandlers.push(handler)
  }

  offConnectionChange(handler: ConnectionHandler) {
    const index = this.connectionHandlers.indexOf(handler)
    if (index !== -1) {
      this.connectionHandlers.splice(index, 1)
    }
  }

  private handleMessage(message: WSMessage) {
    console.log('WebSocket message received:', message.type)
    this.messageHandlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('Error in message handler:', error)
      }
    })
  }

  private updateConnectionStatus(status: WSConnectionStatus) {
    this.connectionStatus = { ...status }
    this.connectionHandlers.forEach(handler => {
      try {
        handler(this.connectionStatus)
      } catch (error) {
        console.error('Error in connection handler:', error)
      }
    })
  }

  getConnectionStatus(): WSConnectionStatus {
    return { ...this.connectionStatus }
  }

  isConnected(): boolean {
    return this.connectionStatus.connected
  }
}

// Singleton instances for different WebSocket endpoints
export const consoleWebSocket = new WebSocketClient('ws://localhost:3000/api/v1/console/ws')
export const statusWebSocket = new WebSocketClient('ws://localhost:3000/api/v1/status/ws')

// Utility functions
export function createWebSocketUrl(endpoint: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/api/v1${endpoint}`
}

// Auto-reconnecting WebSocket wrapper
export class AutoReconnectWebSocket extends WebSocketClient {
  private pingInterval: number | null = null
  private pingIntervalMs = 30000 // 30 seconds

  async connect(): Promise<void> {
    await super.connect()
    this.startPing()
  }

  disconnect() {
    this.stopPing()
    super.disconnect()
  }

  private startPing() {
    this.stopPing()
    this.pingInterval = window.setInterval(() => {
      if (this.isConnected()) {
        this.ping()
      }
    }, this.pingIntervalMs)
  }

  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }
}