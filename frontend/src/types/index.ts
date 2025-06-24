// API Response Types
export interface ServerStatus {
  is_running: boolean
  uptime: number
  version: string
  player_count: number
  max_players: number
  tps: number
  cpu_usage: number
  memory_usage: MemoryInfo
  timestamp: string
}

export interface MemoryInfo {
  used: number
  max: number
  percentage: number
}

export interface Player {
  uuid: string
  name: string
  online: boolean
  last_login?: string
  ip_address?: string
  game_mode: string
  level: number
  experience: number
}

// Extended player response from API
export interface PlayerResponse {
  uuid: string
  name: string
  online: boolean
  last_login?: string
  last_logout?: string
  ip_address?: string
  game_mode: string
  level: number
  experience: number
  health?: number
  food_level?: number
  location?: {
    world: string
    x: number
    y: number
    z: number
  }
  inventory_size?: number
  playtime_hours?: number
  is_op: boolean
  is_banned: boolean
  ban_reason?: string
  ban_expires?: string
}

export interface ConsoleMessage {
  type: string
  timestamp: string
  data: {
    level: string
    message: string
    source: string
  }
}

export interface CommandResponse {
  command: string
  success: boolean
  message: string
  timestamp: string
  execution_time?: number
}

// WebSocket Types
export interface WSMessage {
  type: string
  timestamp: string
  data: any
}

export interface WSConnectionStatus {
  connected: boolean
  reconnecting: boolean
  error?: string
}

// Dashboard Types
export interface DashboardOverview {
  server_status: ServerStatus
  online_players: Player[]
  recent_logs: LogEntry[]
  statistics: {
    total_players: number
    server_uptime: number
    memory_usage_mb: number
    cpu_usage_percent: number
  }
  timestamp: string
}

export interface LogEntry {
  timestamp: string
  level: string
  source: string
  message: string
}

// Chart Data Types
export interface MetricDataPoint {
  timestamp: number
  tps: number
  cpu_usage: number
  memory_usage: number
  player_count: number
}

export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor: string
    backgroundColor: string
    fill: boolean
  }[]
}

// Performance Data Types
export interface PerformanceData {
  tps: number
  cpu_usage: number
  memory_usage: number
  memory_total: number
  memory_used: number
  disk_usage?: number
  network_in?: number
  network_out?: number
  thread_count?: number
  gc_collections?: number
  timestamp?: string
}

// File Manager Types
export interface FileInfo {
  name: string
  path: string
  is_directory: boolean
  size?: number
  modified_time: string
  permissions: string
}

// Error Types
export interface ApiError {
  error: string
  details?: Record<string, any>
  status_code: number
  timestamp: string
  request_id?: string
}