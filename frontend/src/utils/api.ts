import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { 
  ServerStatus, 
  Player, 
  CommandResponse, 
  DashboardOverview,
  ApiError 
} from '@/types'

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add request ID for tracking
    config.headers['X-Request-ID'] = Date.now().toString()
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data)
    
    // Handle common error cases
    if (error.response?.status === 503) {
      console.warn('Aetherius Core is not available')
    }
    
    return Promise.reject(error)
  }
)

// API functions
export class ApiClient {
  // Health check
  static async healthCheck(): Promise<any> {
    const response = await apiClient.get('/health')
    return response.data
  }

  // Dashboard APIs
  static async getDashboardOverview(): Promise<DashboardOverview> {
    const response = await apiClient.get('/dashboard/overview')
    return response.data
  }

  static async getServerStatus(): Promise<ServerStatus> {
    const response = await apiClient.get('/server/status')
    return response.data
  }

  static async getOnlinePlayers(): Promise<Player[]> {
    const response = await apiClient.get('/players')
    return response.data
  }

  static async getServerMetrics(hours: number = 1): Promise<any> {
    const response = await apiClient.get(`/server/metrics?hours=${hours}`)
    return response.data
  }

  // Server control APIs
  static async startServer(): Promise<any> {
    const response = await apiClient.post('/server/start')
    return response.data
  }

  static async stopServer(): Promise<any> {
    const response = await apiClient.post('/server/stop')
    return response.data
  }

  static async restartServer(): Promise<any> {
    const response = await apiClient.post('/server/restart')
    return response.data
  }

  // Console APIs
  static async executeCommand(command: string): Promise<CommandResponse> {
    const response = await apiClient.post('/console/command', { command })
    return response.data
  }

  static async getConsoleHistory(limit: number = 100): Promise<any> {
    const response = await apiClient.get(`/console/history?limit=${limit}`)
    return response.data
  }

  // Player management APIs
  static async kickPlayer(uuid: string, reason?: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'kick',
      reason: reason || 'Kicked by admin'
    })
    return response.data
  }

  static async banPlayer(uuid: string, reason?: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'ban',
      reason: reason || 'Banned by admin'
    })
    return response.data
  }

  static async opPlayer(uuid: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'op'
    })
    return response.data
  }

  static async deopPlayer(uuid: string): Promise<any> {
    const response = await apiClient.post(`/players/${uuid}/action`, {
      action: 'deop'
    })
    return response.data
  }
}

// Error handling utility
export function handleApiError(error: any): ApiError {
  if (error.response?.data) {
    return error.response.data as ApiError
  }
  
  return {
    error: 'Network Error',
    details: { message: error.message },
    status_code: error.response?.status || 0,
    timestamp: new Date().toISOString()
  }
}

// Utility function for API calls with error handling
export async function apiCall<T>(
  apiFunction: () => Promise<T>,
  errorMessage: string = 'API call failed'
): Promise<{ data: T | null; error: ApiError | null }> {
  try {
    const data = await apiFunction()
    return { data, error: null }
  } catch (error) {
    console.error(errorMessage, error)
    return { data: null, error: handleApiError(error) }
  }
}

export default apiClient