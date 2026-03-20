<template>
  <div class="max-w-6xl mx-auto h-full flex flex-col">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">任务中心</h1>
      <div class="flex gap-3">
        <router-link to="/generate"
          class="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
          新建大纲
        </router-link>
        <router-link to="/documents"
          class="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors">
          我的文档
        </router-link>
      </div>
    </div>

    <!-- 筛选标签 -->
    <div class="flex gap-2 mb-6">
      <button v-for="filter in filters" :key="filter.value" @click="currentFilter = filter.value"
        class="px-4 py-2 rounded-lg font-medium transition-colors"
        :class="currentFilter === filter.value ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'">
        {{ filter.label }}
      </button>
    </div>

    <!-- 任务列表 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <div v-else-if="filteredTasks.length === 0" class="text-center py-12 bg-white rounded-xl shadow-sm">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无任务</h3>
      <p class="mt-1 text-sm text-gray-500">点击上方按钮创建新任务</p>
    </div>

    <div v-else class="space-y-4 overflow-y-auto flex-1 pb-6 min-h-0">
      <div v-for="task in filteredTasks" :key="task.task_id" :id="`task-${task.task_id}`"
        class="relative bg-white rounded-xl shadow-sm m-4 p-6 transition-all"
        :class="{ 'ring-2 ring-blue-500 ring-offset-2': highlightedTask === task.task_id.toString() }">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="taskTypeClass(task.task_type)">
                {{ taskTypeText(task.task_type) }}
              </span>
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="statusClass(task.status)">
                {{ statusText(task.status) }}
              </span>
              <span class="text-sm text-gray-500">#{{ task.task_id }}</span>
            </div>

            <p class="text-gray-700 mb-2">
              {{ taskDescription(task) }}
            </p>

            <div class="flex items-center gap-4 text-sm text-gray-500">
              <span>创建: {{ formatTime(task.created_at) }}</span>
              <span v-if="task.started_at">开始: {{ formatTime(task.started_at) }}</span>
              <span v-if="task.completed_at">完成: {{ formatTime(task.completed_at) }}</span>
              <span v-if="task.result?.title" class="text-blue-600">{{ task.result.title }}</span>
            </div>

            <!-- 错误信息 -->
            <p v-if="task.error_message" class="mt-2 text-sm text-red-600">
              错误: {{ task.error_message }}
            </p>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2 ml-4">
            <!-- 处理中状态 -->
            <div v-if="task.status === 'pending' || task.status === 'processing'" class="flex items-center gap-2">
              <div class="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
            </div>

            <!-- 完成状态 -->
            <template v-if="task.status === 'completed'">
              <router-link v-if="task.result?.outline_id" :to="`/outline/${task.result.outline_id}/edit`"
                class="px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors">
                查看大纲
              </router-link>
              <router-link v-if="task.result?.document_id" :to="`/document/${task.result.document_id}`"
                class="px-3 py-1.5 text-sm bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors">
                查看文档
              </router-link>
            </template>

            <!-- 失败状态 -->
            <button v-if="task.status === 'failed'" @click="retryTask(task)"
              class="px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors">
              重试
            </button>
          </div>
        </div>

        <!-- 进度条 -->
        <div v-if="task.status === 'pending' || task.status === 'processing'" class="mt-4">
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-blue-600 h-2 rounded-full transition-all duration-1000"
              :style="{ width: taskProgress(task) + '%' }">
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listTasks, generateOutline } from '../api/outline'
import type { TaskStatusResponse } from '../types/outline'

const route = useRoute()
const router = useRouter()

const tasks = ref<TaskStatusResponse[]>([])
const loading = ref(true)
const currentFilter = ref('all')
const highlightedTask = ref(route.query.highlight as string || '')
const pollInterval = ref<number | null>(null)

const filters = [
  { label: '全部', value: 'all' },
  { label: '进行中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

const filteredTasks = computed(() => {
  if (!tasks.value || !Array.isArray(tasks.value)) {
    return []
  }
  if (currentFilter.value === 'all') {
    return tasks.value
  }
  if (currentFilter.value === 'processing') {
    return tasks.value.filter(t => t.status === 'pending' || t.status === 'processing')
  }
  return tasks.value.filter(t => t.status === currentFilter.value)
})

const taskTypeClass = (type: string) => {
  switch (type) {
    case 'generate_outline':
      return 'bg-purple-100 text-purple-700'
    case 'generate_document':
      return 'bg-green-100 text-green-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

const taskTypeText = (type: string) => {
  switch (type) {
    case 'generate_outline':
      return '生成大纲'
    case 'generate_document':
      return '生成文档'
    default:
      return type
  }
}

const statusClass = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    case 'processing':
      return 'bg-blue-100 text-blue-700'
    case 'pending':
      return 'bg-yellow-100 text-yellow-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

const statusText = (status: string) => {
  switch (status) {
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    case 'processing':
      return '处理中'
    case 'pending':
      return '等待中'
    default:
      return status
  }
}

const taskDescription = (task: TaskStatusResponse) => {
  if (task.task_type === 'generate_outline') {
    return '生成教学大纲'
  }
  if (task.task_type === 'generate_document') {
    return '生成教学文档'
  }
  return task.task_type
}

const taskProgress = (task: TaskStatusResponse) => {
  if (task.status === 'completed') return 100
  if (task.status === 'failed') return 0
  if (task.status === 'processing') return 60
  return 20
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  // 后端返回的是 UTC 时间（带 +00:00 时区标识）
  // 直接转换为本地时间显示
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadTasks = async () => {
  try {
    const result = await listTasks()
    console.log('加载任务结果:', result)
    tasks.value = result || []
  } catch (error) {
    console.error('加载任务失败:', error)
    // 401 错误会在 api/index.ts 中处理，这里不需要额外处理
    if ((error as Error).message.includes('登录已过期')) {
      // 停止轮询
      if (pollInterval.value) {
        clearInterval(pollInterval.value)
        pollInterval.value = null
      }
    }
  } finally {
    loading.value = false
  }
}

const retryTask = async (task: TaskStatusResponse) => {
  // 这里可以实现重试逻辑
  alert('重试功能开发中...')
}

// 自动刷新
const startPolling = () => {
  pollInterval.value = window.setInterval(() => {
    const hasProcessing = tasks.value.some(t => t.status === 'pending' || t.status === 'processing')
    if (hasProcessing) {
      loadTasks()
    }
  }, 3000)
}

onMounted(() => {
  loadTasks()
  startPolling()

  // 如果有高亮任务，滚动到该任务
  if (highlightedTask.value) {
    setTimeout(() => {
      const element = document.getElementById(`task-${highlightedTask.value}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 500)
  }
})

onUnmounted(() => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
})
</script>
