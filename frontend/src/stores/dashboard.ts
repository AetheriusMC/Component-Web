import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ApiClient, apiCall } from '@/utils/api'
import type { ServerStatus, Player, DashboardOverview, MetricDataPoint } from '@/types'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const serverStatus = ref<ServerStatus | null>(null)
  const onlinePlayers = ref<Player[]>([])
  const dashboardOverview = ref<DashboardOverview | null>(null)
  const metrics = ref<MetricDataPoint[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Auto refresh settings
  const autoRefresh = ref(true)
  const refreshInterval = ref(5000) // 5 seconds
  let refreshTimer: number | null = null

  // Computed
  const isServerRunning = computed(() => serverStatus.value?.is_running ?? false)
  const playerCount = computed(() => serverStatus.value?.player_count ?? 0)
  const maxPlayers = computed(() => serverStatus.value?.max_players ?? 20)
  const serverUptime = computed(() => serverStatus.value?.uptime ?? 0)
  const memoryUsage = computed(() => serverStatus.value?.memory_usage ?? { used: 0, max: 4096, percentage: 0 })
  const cpuUsage = computed(() => serverStatus.value?.cpu_usage ?? 0)
  const tps = computed(() => serverStatus.value?.tps ?? 0)

  // Format uptime as human readable string
  const formattedUptime = computed(() => {
    const uptime = serverUptime.value
    const hours = Math.floor(uptime / 3600)
    const minutes = Math.floor((uptime % 3600) / 60)
    const seconds = uptime % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  })

  // Actions
  async function fetchDashboardOverview() {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.getDashboardOverview(),
      'Failed to fetch dashboard overview'
    )

    if (data) {
      dashboardOverview.value = data
      serverStatus.value = data.server_status
      onlinePlayers.value = data.online_players
      lastUpdated.value = new Date()
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
  }

  async function fetchServerStatus() {
    const { data, error: apiError } = await apiCall(
      () => ApiClient.getServerStatus(),
      'Failed to fetch server status'
    )

    if (data) {
      serverStatus.value = data
      lastUpdated.value = new Date()
    } else if (apiError) {
      error.value = apiError.error
    }
  }

  async function fetchOnlinePlayers() {
    const { data, error: apiError } = await apiCall(
      () => ApiClient.getOnlinePlayers(),
      'Failed to fetch online players'
    )

    if (data) {
      onlinePlayers.value = data
    } else if (apiError) {
      error.value = apiError.error
    }
  }

  async function fetchMetrics(hours: number = 1) {
    const { data, error: apiError } = await apiCall(
      () => ApiClient.getServerMetrics(hours),
      'Failed to fetch server metrics'
    )

    if (data) {
      metrics.value = data.metrics
    } else if (apiError) {
      error.value = apiError.error
    }
  }

  async function startServer() {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.startServer(),
      'Failed to start server'
    )

    if (data) {
      // Refresh status after starting
      await fetchServerStatus()
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data !== null
  }

  async function stopServer() {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.stopServer(),
      'Failed to stop server'
    )

    if (data) {
      // Refresh status after stopping
      await fetchServerStatus()
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data !== null
  }

  async function restartServer() {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.restartServer(),
      'Failed to restart server'
    )

    if (data) {
      // Refresh status after restarting
      await fetchServerStatus()
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data !== null
  }

  async function executeServerControl(action: string) {
    switch (action) {
      case 'start':
        return await startServer()
      case 'stop':
        return await stopServer()
      case 'restart':
        return await restartServer()
      default:
        throw new Error(`Unknown action: ${action}`)
    }
  }

  function startAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
    }

    if (autoRefresh.value) {
      refreshTimer = window.setInterval(() => {
        fetchDashboardOverview()
      }, refreshInterval.value)
    }
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  function setAutoRefresh(enabled: boolean) {
    autoRefresh.value = enabled
    if (enabled) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }

  function setRefreshInterval(interval: number) {
    refreshInterval.value = interval
    if (autoRefresh.value) {
      startAutoRefresh()
    }
  }

  function clearError() {
    error.value = null
  }

  // Initialize
  function initialize() {
    fetchDashboardOverview()
    fetchMetrics()
    startAutoRefresh()
  }

  // Cleanup
  function cleanup() {
    stopAutoRefresh()
  }

  return {
    // State
    serverStatus,
    onlinePlayers,
    dashboardOverview,
    metrics,
    loading,
    error,
    lastUpdated,
    autoRefresh,
    refreshInterval,

    // Computed
    isServerRunning,
    playerCount,
    maxPlayers,
    serverUptime,
    formattedUptime,
    memoryUsage,
    cpuUsage,
    tps,

    // Actions
    fetchDashboardOverview,
    fetchServerStatus,
    fetchOnlinePlayers,
    fetchMetrics,
    startServer,
    stopServer,
    restartServer,
    executeServerControl,
    startAutoRefresh,
    stopAutoRefresh,
    setAutoRefresh,
    setRefreshInterval,
    clearError,
    initialize,
    cleanup
  }
})