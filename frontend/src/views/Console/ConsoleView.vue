<template>
  <div class="console-view">
    <el-card class="console-card" shadow="hover">
      <template #header>
        <div class="console-header">
          <div class="header-left">
            <el-icon :size="18">
              <Monitor />
            </el-icon>
            <span class="header-title">实时控制台</span>
          </div>
          <div class="header-right">
            <el-space>
              <el-tag 
                :type="connectionStatus.connected ? 'success' : 'danger'"
                size="small"
              >
                <el-icon class="status-icon">
                  <component :is="connectionStatus.connected ? Connection : WifiOff" />
                </el-icon>
                {{ connectionStatus.connected ? '已连接' : '未连接' }}
              </el-tag>
              
              <el-button 
                size="small" 
                @click="clearConsole"
                :icon="Delete"
              >
                清空
              </el-button>
              
              <el-button 
                size="small" 
                @click="toggleAutoScroll"
                :type="autoScroll ? 'primary' : 'default'"
                :icon="Bottom"
              >
                自动滚动
              </el-button>
            </el-space>
          </div>
        </div>
      </template>
      
      <!-- Console Output -->
      <div class="console-container">
        <div 
          ref="outputRef" 
          class="console-output"
          @scroll="handleScroll"
        >
          <div
            v-for="(message, index) in displayMessages"
            :key="`${message.timestamp}-${index}`"
            :class="['log-line', `log-${message.data.level.toLowerCase()}`]"
          >
            <span class="log-timestamp">{{ formatTime(message.timestamp) }}</span>
            <span class="log-level">[{{ message.data.level }}]</span>
            <span class="log-source">[{{ message.data.source }}]</span>
            <span class="log-content">{{ message.data.message }}</span>
          </div>
          
          <!-- Loading indicator -->
          <div v-if="isReconnecting" class="reconnecting-indicator">
            <el-icon class="rotating">
              <Loading />
            </el-icon>
            <span>正在重新连接...</span>
          </div>
          
          <!-- Empty state -->
          <div v-if="displayMessages.length === 0 && !isReconnecting" class="empty-console">
            <el-icon :size="48" class="empty-icon">
              <Monitor />
            </el-icon>
            <p>等待控制台输出...</p>
          </div>
        </div>
        
        <!-- Command Input -->
        <div class="console-input">
          <el-input
            v-model="currentCommand"
            placeholder="输入控制台命令... (按Enter发送, 上/下箭头浏览历史)"
            @keydown="handleKeyDown"
            :prefix-icon="ArrowRight"
            size="large"
            :disabled="!connectionStatus.connected"
          >
            <template #append>
              <el-button 
                @click="sendCommand"
                :disabled="!currentCommand.trim() || !connectionStatus.connected"
                :icon="Promotion"
              >
                发送
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { 
  Monitor, 
  Connection, 
  WifiOff, 
  Delete, 
  Bottom, 
  Loading,
  ArrowRight,
  Promotion
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useWebSocketStore } from '@/stores/websocket'
import type { ConsoleMessage } from '@/types'

const wsStore = useWebSocketStore()

// Refs
const outputRef = ref<HTMLElement>()
const currentCommand = ref('')
const commandHistory = ref<string[]>([])
const historyIndex = ref(-1)
const autoScroll = ref(true)
const maxHistorySize = 50

// Computed
const connectionStatus = computed(() => wsStore.consoleStatus)
const isReconnecting = computed(() => connectionStatus.value.reconnecting)

const displayMessages = computed(() => {
  // Limit displayed messages for performance
  const maxMessages = 500
  const messages = wsStore.consoleMessages
  if (messages.length <= maxMessages) {
    return messages
  }
  return messages.slice(-maxMessages)
})

// Methods
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function scrollToBottom() {
  if (outputRef.value && autoScroll.value) {
    nextTick(() => {
      if (outputRef.value) {
        outputRef.value.scrollTop = outputRef.value.scrollHeight
      }
    })
  }
}

function handleScroll() {
  if (!outputRef.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = outputRef.value
  const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10
  
  // Disable auto-scroll if user scrolls up
  if (!isAtBottom && autoScroll.value) {
    autoScroll.value = false
  }
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

function clearConsole() {
  wsStore.clearConsoleMessages()
  ElMessage.success('控制台已清空')
}

function sendCommand() {
  const command = currentCommand.value.trim()
  if (!command) return

  if (!connectionStatus.value.connected) {
    ElMessage.error('WebSocket未连接，无法发送命令')
    return
  }

  // Add to history
  if (commandHistory.value[commandHistory.value.length - 1] !== command) {
    commandHistory.value.push(command)
    if (commandHistory.value.length > maxHistorySize) {
      commandHistory.value.shift()
    }
  }

  // Reset history index
  historyIndex.value = -1

  // Send command
  const success = wsStore.sendConsoleCommand(command)
  if (success) {
    currentCommand.value = ''
    
    // Add command to console output for immediate feedback
    wsStore.addConsoleMessage({
      type: 'console_log',
      timestamp: new Date().toISOString(),
      data: {
        level: 'COMMAND',
        source: 'Client',
        message: `> ${command}`
      }
    })
  } else {
    ElMessage.error('命令发送失败')
  }
}

function handleKeyDown(event: KeyboardEvent) {
  switch (event.key) {
    case 'Enter':
      if (!event.shiftKey) {
        event.preventDefault()
        sendCommand()
      }
      break
      
    case 'ArrowUp':
      event.preventDefault()
      navigateHistory(1)
      break
      
    case 'ArrowDown':
      event.preventDefault()
      navigateHistory(-1)
      break
      
    case 'Tab':
      event.preventDefault()
      // TODO: Implement command auto-completion
      break
  }
}

function navigateHistory(direction: number) {
  if (commandHistory.value.length === 0) return

  const newIndex = historyIndex.value + direction
  
  if (newIndex >= 0 && newIndex < commandHistory.value.length) {
    historyIndex.value = newIndex
    const commandIndex = commandHistory.value.length - 1 - historyIndex.value
    currentCommand.value = commandHistory.value[commandIndex]
  } else if (newIndex < 0) {
    historyIndex.value = -1
    currentCommand.value = ''
  }
}

// Watch for new messages and auto-scroll
watch(
  () => wsStore.consoleMessages.length,
  () => {
    scrollToBottom()
  }
)

// Watch connection status
watch(
  () => connectionStatus.value.connected,
  (connected) => {
    if (connected) {
      ElMessage.success('WebSocket连接已建立')
    } else {
      ElMessage.warning('WebSocket连接已断开')
    }
  }
)

onMounted(() => {
  // Ensure WebSocket is connected
  wsStore.initConsoleWebSocket()
  scrollToBottom()
})

onUnmounted(() => {
  // Cleanup if needed
})
</script>

<style scoped>
.console-view {
  height: calc(100vh - 120px);
}

.console-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
}

.status-icon {
  margin-right: 4px;
}

.console-container {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.console-output {
  flex: 1;
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  overflow-y: auto;
  border-radius: 6px;
  margin-bottom: 12px;
}

.log-line {
  margin-bottom: 2px;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.log-timestamp {
  color: #808080;
  margin-right: 8px;
}

.log-level {
  margin-right: 8px;
  font-weight: bold;
  min-width: 60px;
  display: inline-block;
}

.log-source {
  color: #9cdcfe;
  margin-right: 8px;
  min-width: 80px;
  display: inline-block;
}

.log-content {
  color: #d4d4d4;
}

/* Log level colors */
.log-info .log-level {
  color: #4fc3f7;
}

.log-warn .log-level {
  color: #ffb74d;
}

.log-error .log-level {
  color: #f48fb1;
}

.log-debug .log-level {
  color: #81c784;
}

.log-command .log-level {
  color: #ba68c8;
}

.log-command .log-content {
  color: #ba68c8;
  font-weight: bold;
}

.reconnecting-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #ffb74d;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-console {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #808080;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.console-input {
  margin-top: auto;
}

:deep(.el-card__body) {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-input-group__append) {
  background-color: #409EFF;
  border-color: #409EFF;
}

:deep(.el-input-group__append .el-button) {
  background-color: transparent;
  border: none;
  color: white;
}

/* Custom scrollbar */
.console-output::-webkit-scrollbar {
  width: 8px;
}

.console-output::-webkit-scrollbar-track {
  background: #2d2d2d;
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.console-output::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style>