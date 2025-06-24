<template>
  <div class="dashboard-view">
    <!-- Server Status Cards -->
    <el-row :gutter="20" class="status-cards">
      <el-col :span="6">
        <el-card class="status-card server-status">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>服务器状态</span>
            </div>
          </template>
          <div class="status-content">
            <div class="status-indicator" :class="{ running: serverStatus.is_running }">
              {{ serverStatus.is_running ? '运行中' : '已停止' }}
            </div>
            <div class="status-details">
              <p>版本: {{ serverStatus.version || 'Unknown' }}</p>
              <p>运行时间: {{ formatUptime(serverStatus.uptime) }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card players-card">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>在线玩家</span>
            </div>
          </template>
          <div class="status-content">
            <div class="metric-value">{{ onlinePlayers.length }}</div>
            <div class="metric-subtitle">/ {{ serverStatus.max_players || 20 }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card performance-card">
          <template #header>
            <div class="card-header">
              <el-icon><Cpu /></el-icon>
              <span>TPS</span>
            </div>
          </template>
          <div class="status-content">
            <div class="metric-value" :class="getTpsClass(performance.tps)">
              {{ performance.tps?.toFixed(1) || '0.0' }}
            </div>
            <div class="metric-subtitle">每秒tick数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card memory-card">
          <template #header>
            <div class="card-header">
              <el-icon><PieChart /></el-icon>
              <span>内存使用</span>
            </div>
          </template>
          <div class="status-content">
            <div class="metric-value">{{ (performance.memory_usage || 0).toFixed(1) }}%</div>
            <div class="metric-subtitle">{{ formatMemory(performance.memory_used) }} / {{ formatMemory(performance.memory_total) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Server Control Panel -->
    <el-row :gutter="20" class="control-panel">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>服务器控制</span>
            </div>
          </template>
          <div class="control-buttons">
            <el-button 
              type="success" 
              :disabled="serverStatus.is_running || controlLoading"
              :loading="controlLoading && pendingAction === 'start'"
              @click="handleServerControl('start')"
            >
              <el-icon><VideoPlay /></el-icon>
              启动服务器
            </el-button>
            
            <el-button 
              type="danger" 
              :disabled="!serverStatus.is_running || controlLoading"
              :loading="controlLoading && pendingAction === 'stop'"
              @click="handleServerControl('stop')"
            >
              <el-icon><VideoPause /></el-icon>
              停止服务器
            </el-button>
            
            <el-button 
              type="warning" 
              :disabled="!serverStatus.is_running || controlLoading"
              :loading="controlLoading && pendingAction === 'restart'"
              @click="handleServerControl('restart')"
            >
              <el-icon><Refresh /></el-icon>
              重启服务器
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Performance Charts -->
    <el-row :gutter="20" class="charts-section">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>性能监控</span>
            </div>
          </template>
          <div ref="performanceChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>玩家活动</span>
            </div>
          </template>
          <div ref="playersChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Online Players List -->
    <el-row class="players-section">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><UserFilled /></el-icon>
              <span>在线玩家列表</span>
            </div>
          </template>
          <div class="players-list">
            <el-empty v-if="onlinePlayers.length === 0" description="暂无在线玩家" />
            <div v-else class="player-grid">
              <div 
                v-for="player in onlinePlayers" 
                :key="player.uuid" 
                class="player-item"
              >
                <el-avatar :size="40" class="player-avatar">
                  {{ player.name.charAt(0).toUpperCase() }}
                </el-avatar>
                <div class="player-info">
                  <div class="player-name">{{ player.name }}</div>
                  <div class="player-details">
                    <span>等级 {{ player.level || 0 }}</span>
                    <span>{{ player.game_mode || 'survival' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  Monitor,
  User,
  Cpu,
  PieChart,
  Operation,
  VideoPlay,
  VideoPause,
  Refresh,
  TrendCharts,
  DataLine,
  UserFilled
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebSocketStore } from '@/stores/websocket'
import type { ServerStatus, Player, PerformanceData } from '@/types'

const dashboardStore = useDashboardStore()
const wsStore = useWebSocketStore()

// Reactive data
const serverStatus = ref<ServerStatus>({
  is_running: false,
  uptime: 0,
  version: 'Unknown',
  player_count: 0,
  max_players: 20,
  tps: 0,
  cpu_usage: 0,
  memory_usage: { used: 0, max: 4096, percentage: 0 }
})

const onlinePlayers = ref<Player[]>([])
const performance = ref<PerformanceData>({
  tps: 0,
  cpu_usage: 0,
  memory_usage: 0,
  memory_total: 4096,
  memory_used: 0
})

const controlLoading = ref(false)
const pendingAction = ref('')

// Chart instances
const performanceChart = ref<HTMLElement>()
const playersChart = ref<HTMLElement>()
let performanceChartInstance: echarts.ECharts | null = null
let playersChartInstance: echarts.ECharts | null = null

// Utility functions
const formatUptime = (seconds: number): string => {
  if (!seconds) return '0分钟'
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  const parts = []
  if (days > 0) parts.push(`${days}天`)
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  
  return parts.join(' ') || '刚刚启动'
}

const formatMemory = (mb: number): string => {
  if (!mb) return '0MB'
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(1)}GB`
  }
  return `${mb.toFixed(0)}MB`
}

const getTpsClass = (tps: number): string => {
  if (tps >= 19) return 'excellent'
  if (tps >= 15) return 'good'
  if (tps >= 10) return 'warning'
  return 'danger'
}

// Server control functions
const handleServerControl = async (action: string) => {
  controlLoading.value = true
  pendingAction.value = action
  
  try {
    await dashboardStore.executeServerControl(action)
    ElMessage.success(`服务器${action === 'start' ? '启动' : action === 'stop' ? '停止' : '重启'}命令已发送`)
  } catch (error) {
    ElMessage.error(`服务器控制失败: ${error}`)
  } finally {
    controlLoading.value = false
    pendingAction.value = ''
  }
}

// Chart initialization
const initCharts = async () => {
  await nextTick()
  
  if (performanceChart.value) {
    performanceChartInstance = echarts.init(performanceChart.value)
    updatePerformanceChart()
  }
  
  if (playersChart.value) {
    playersChartInstance = echarts.init(playersChart.value)
    updatePlayersChart()
  }
}

const updatePerformanceChart = () => {
  if (!performanceChartInstance) return
  
  const option = {
    title: {
      text: '实时性能监控',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['TPS', 'CPU使用率', '内存使用率'],
      bottom: 0
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: 'TPS',
        min: 0,
        max: 20,
        position: 'left'
      },
      {
        type: 'value',
        name: '使用率 (%)',
        min: 0,
        max: 100,
        position: 'right'
      }
    ],
    series: [
      {
        name: 'TPS',
        type: 'line',
        yAxisIndex: 0,
        data: [],
        smooth: true,
        lineStyle: { color: '#67C23A' }
      },
      {
        name: 'CPU使用率',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        lineStyle: { color: '#E6A23C' }
      },
      {
        name: '内存使用率',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        lineStyle: { color: '#409EFF' }
      }
    ]
  }
  
  performanceChartInstance.setOption(option)
}

const updatePlayersChart = () => {
  if (!playersChartInstance) return
  
  const option = {
    title: {
      text: '玩家活动统计',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '在线人数',
      min: 0
    },
    series: [
      {
        name: '在线玩家',
        type: 'area',
        data: [],
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.8)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
            ]
          }
        },
        lineStyle: { color: '#409EFF' }
      }
    ]
  }
  
  playersChartInstance.setOption(option)
}

// Data loading and WebSocket handling
const loadDashboardData = async () => {
  try {
    const data = await dashboardStore.fetchDashboardOverview()
    
    serverStatus.value = data.server_status
    onlinePlayers.value = data.online_players
    
    // Update performance data if available
    if (data.server_status) {
      performance.value = {
        tps: data.server_status.tps || 0,
        cpu_usage: data.server_status.cpu_usage || 0,
        memory_usage: data.server_status.memory_usage?.percentage || 0,
        memory_total: data.server_status.memory_usage?.max || 4096,
        memory_used: data.server_status.memory_usage?.used || 0
      }
    }
  } catch (error) {
    ElMessage.error('获取仪表盘数据失败')
  }
}

const setupWebSocket = () => {
  // Connect to dashboard WebSocket
  wsStore.connectDashboard()
  
  // Listen for dashboard updates
  wsStore.onMessage((message) => {
    switch (message.type) {
      case 'dashboard_summary':
        serverStatus.value = message.data.server_status
        onlinePlayers.value = message.data.online_players
        break
        
      case 'performance_update':
        performance.value = message.data
        
        // Update charts with new data
        if (performanceChartInstance) {
          const now = new Date()
          const option = performanceChartInstance.getOption() as any
          
          // Add new data points
          option.series[0].data.push([now, message.data.tps])
          option.series[1].data.push([now, message.data.cpu_usage])
          option.series[2].data.push([now, message.data.memory_usage])
          
          // Keep only last 50 points
          option.series.forEach((series: any) => {
            if (series.data.length > 50) {
              series.data = series.data.slice(-50)
            }
          })
          
          performanceChartInstance.setOption(option)
        }
        
        if (playersChartInstance) {
          const now = new Date()
          const option = playersChartInstance.getOption() as any
          
          option.series[0].data.push([now, onlinePlayers.value.length])
          
          if (option.series[0].data.length > 50) {
            option.series[0].data = option.series[0].data.slice(-50)
          }
          
          playersChartInstance.setOption(option)
        }
        break
        
      case 'server_control_result':
        const action = message.data.action
        const result = message.data.result
        
        if (result.success) {
          ElMessage.success(`${action}操作成功: ${result.message}`)
        } else {
          ElMessage.error(`${action}操作失败: ${result.message}`)
        }
        break
    }
  })
}

onMounted(async () => {
  await loadDashboardData()
  await initCharts()
  setupWebSocket()
})

onUnmounted(() => {
  if (performanceChartInstance) {
    performanceChartInstance.dispose()
  }
  if (playersChartInstance) {
    playersChartInstance.dispose()
  }
  wsStore.disconnect()
})
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.status-cards {
  margin-bottom: 20px;
}

.status-card {
  text-align: center;
  transition: all 0.3s;
}

.status-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
}

.status-content {
  padding: 10px 0;
}

.status-indicator {
  font-size: 18px;
  font-weight: 600;
  color: #f56c6c;
  margin-bottom: 10px;
}

.status-indicator.running {
  color: #67c23a;
}

.status-details p {
  margin: 5px 0;
  color: #606266;
  font-size: 14px;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 5px;
}

.metric-value.excellent {
  color: #67c23a;
}

.metric-value.good {
  color: #e6a23c;
}

.metric-value.warning {
  color: #f56c6c;
}

.metric-value.danger {
  color: #f56c6c;
}

.metric-subtitle {
  color: #909399;
  font-size: 12px;
}

.control-panel {
  margin-bottom: 20px;
}

.control-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.players-section {
  margin-bottom: 20px;
}

.players-list {
  padding: 20px;
}

.player-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.player-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.player-avatar {
  background: linear-gradient(45deg, #409eff, #67c23a);
  color: white;
  font-weight: 600;
}

.player-info {
  flex: 1;
}

.player-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.player-details {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.player-details span {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>