<template>
  <div class="simulation-sandbox" :style="{ height: height + 'px' }">
    <iframe
      ref="iframeRef"
      :src="sandboxUrl"
      class="sandbox-iframe"
      sandbox="allow-scripts allow-same-origin"
      @load="onIframeLoad"
    ></iframe>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="sandbox-loading">
      <div class="loading-spinner"></div>
      <span class="loading-text">加载仿真中...</span>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="sandbox-error">
      <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>
      <span class="error-text">{{ error }}</span>
      <button @click="reload" class="reload-btn">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

interface Props {
  /** 仿真 HTML 代码 */
  code: string
  /** 沙箱高度 */
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  height: 600
})

const iframeRef = ref<HTMLIFrameElement | null>(null)
const loading = ref(true)
const error = ref('')
const sandboxReady = ref(false)

// 沙箱页面 URL（相对于 public 目录）
const sandboxUrl = '/sandbox.html'

// 监听 code 变化，自动加载
watch(() => props.code, (newCode) => {
  if (newCode && sandboxReady.value) {
    loadSimulation(newCode)
  }
})

// iframe 加载完成
const onIframeLoad = () => {
  loading.value = false
  // 等待沙箱发送 READY 消息
}

// 加载仿真代码到沙箱
const loadSimulation = (code: string) => {
  if (!iframeRef.value || !iframeRef.value.contentWindow) {
    error.value = '沙箱未就绪'
    return
  }

  error.value = ''
  
  try {
    iframeRef.value.contentWindow.postMessage({
      type: 'LOAD_SIMULATION',
      code: code
    }, '*')
  } catch (e) {
    error.value = '发送代码到沙箱失败'
    console.error('Sandbox postMessage error:', e)
  }
}

// 重新加载
const reload = () => {
  error.value = ''
  loading.value = true
  sandboxReady.value = false
  
  if (iframeRef.value) {
    iframeRef.value.src = sandboxUrl
  }
}

// 监听沙箱消息
const handleMessage = (event: MessageEvent) => {
  const data = event.data
  if (!data || typeof data !== 'object') return

  switch (data.type) {
    case 'SANDBOX_READY':
      sandboxReady.value = true
      if (props.code) {
        loadSimulation(props.code)
      }
      break
      
    case 'SIMULATION_LOADED':
      console.log('Simulation loaded at:', data.timestamp)
      break
      
    case 'SIMULATION_ERROR':
      error.value = data.error || '仿真加载失败'
      console.error('Simulation error:', data.error)
      break
      
    case 'SANDBOX_LOG':
      // 沙箱日志，开发环境可打印
      if (import.meta.env.DEV) {
        console.log(`[Sandbox ${data.level}]`, data.message)
      }
      break
  }
}

onMounted(() => {
  window.addEventListener('message', handleMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', handleMessage)
})
</script>

<style scoped>
.simulation-sandbox {
  position: relative;
  width: 100%;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.sandbox-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.sandbox-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: #6b7280;
  font-size: 14px;
}

.sandbox-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(254, 242, 242, 0.95);
  gap: 12px;
  padding: 20px;
}

.error-icon {
  width: 48px;
  height: 48px;
  color: #ef4444;
}

.error-text {
  color: #dc2626;
  font-size: 14px;
  text-align: center;
}

.reload-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.reload-btn:hover {
  background: #2563eb;
}
</style>
