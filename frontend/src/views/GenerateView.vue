<template>
  <div class="max-w-6xl mx-auto h-full flex flex-col">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('generate.title') }}</h1>

    <!-- 生成表单 -->
    <div v-if="!currentTask" class="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
      <!-- 左侧：基本信息 -->
      <div class="lg:col-span-2 space-y-6">
        <div class="bg-white rounded-xl shadow-sm p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
          
          <form @submit.prevent="handleGenerate" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.courseName') }}</label>
                <input v-model="form.course" type="text" required
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  :placeholder="$t('generate.coursePlaceholder')" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.knowledgePoint') }}</label>
                <input v-model="form.knowledge_point" type="text" required
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  :placeholder="$t('generate.knowledgePlaceholder')" />
              </div>
            </div>

            <div class="bg-blue-50 rounded-lg p-4">
              <div class="flex items-center gap-2 text-blue-700 text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>难度等级和其他生成选项请在右侧配置面板中设置</span>
              </div>
            </div>

            <button type="submit" :disabled="isSubmitting"
              class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ isSubmitting ? '提交中...' : $t('generate.generateButton') }}
            </button>
          </form>
        </div>
      </div>

      <!-- 右侧：生成配置 -->
      <div class="lg:col-span-1 h-full overflow-hidden">
        <GenerationConfigPanel
          ref="configPanelRef"
          @save="onConfigSave"
        />
      </div>
    </div>

    <!-- 任务状态显示 -->
    <div v-else class="bg-white rounded-xl shadow-sm p-8 text-center">
      <div class="mb-6">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" :class="taskStatusClass">
          <svg v-if="currentTask.status === 'completed'" class="w-8 h-8 text-green-600" fill="none"
            stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else-if="currentTask.status === 'failed'" class="w-8 h-8 text-red-600" fill="none"
            stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <div v-else class="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
        </div>

        <h2 class="text-xl font-semibold text-gray-900 mb-2">{{ taskStatusText }}</h2>
        <p class="text-gray-500">{{ taskStatusDescription }}</p>
      </div>

      <!-- 进度条 -->
      <div v-if="currentTask.status === 'pending' || currentTask.status === 'processing'" class="mb-6">
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div class="bg-blue-600 h-2 rounded-full transition-all duration-500"
            :style="{ width: progressPercent + '%' }"></div>
        </div>
        <p class="text-sm text-gray-500 mt-2">预计耗时 10-30 秒</p>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-center gap-4">
        <button v-if="currentTask.status === 'completed' && currentTask.result?.outline_id" @click="goToOutline"
          class="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
          查看大纲
        </button>
        <button v-if="currentTask.status === 'failed'" @click="resetTask"
          class="px-6 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors">
          重试
        </button>
        <button v-if="currentTask.status !== 'pending' && currentTask.status !== 'processing'" @click="resetTask"
          class="px-6 py-2 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors">
          生成新大纲
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { generateOutline, getTaskStatus } from '../api/outline'
import GenerationConfigPanel from '../components/GenerationConfigPanel.vue'
import type { TaskResponse, TaskStatusResponse } from '../types/outline'
import type { GenerationConfigCreate } from '../types/generationConfig'

const router = useRouter()
const isSubmitting = ref(false)
const currentTask = ref<TaskStatusResponse | null>(null)
const pollInterval = ref<number | null>(null)
const progressPercent = ref(10)
const configPanelRef = ref<InstanceType<typeof GenerationConfigPanel> | null>(null)

const form = ref({
  course: '',
  knowledge_point: ''
})

const taskStatusClass = computed(() => {
  switch (currentTask.value?.status) {
    case 'completed':
      return 'bg-green-100'
    case 'failed':
      return 'bg-red-100'
    default:
      return 'bg-blue-100'
  }
})

const taskStatusText = computed(() => {
  switch (currentTask.value?.status) {
    case 'pending':
      return '等待处理'
    case 'processing':
      return '正在生成'
    case 'completed':
      return '生成完成'
    case 'failed':
      return '生成失败'
    default:
      return '处理中'
  }
})

const taskStatusDescription = computed(() => {
  switch (currentTask.value?.status) {
    case 'pending':
      return '任务已加入队列，等待处理...'
    case 'processing':
      return 'AI 正在生成教学大纲，请稍候...'
    case 'completed':
      return '大纲生成成功！'
    case 'failed':
      return currentTask.value?.error_message || '生成过程中出现错误，请重试'
    default:
      return ''
  }
})

// 配置保存回调（可选，用于显示保存成功提示）
const onConfigSave = (config: GenerationConfigCreate) => {
  console.log('配置已保存:', config)
}

// 轮询任务状态
const startPolling = (taskId: number) => {
  // 清除之前的轮询
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }

  // 模拟进度条增长
  progressPercent.value = 10
  const progressInterval = setInterval(() => {
    if (progressPercent.value < 90 && currentTask.value?.status === 'processing') {
      progressPercent.value += Math.random() * 10
    }
  }, 1000)

  // 轮询任务状态
  pollInterval.value = window.setInterval(async () => {
    try {
      const status = await getTaskStatus(taskId)
      currentTask.value = status

      // 任务完成或失败，停止轮询
      if (status.status === 'completed' || status.status === 'failed') {
        clearInterval(pollInterval.value!)
        clearInterval(progressInterval)
        pollInterval.value = null
        progressPercent.value = status.status === 'completed' ? 100 : 0
      }
    } catch (error) {
      console.error('获取任务状态失败:', error)
      // 如果是 401 错误，api/index.ts 会处理跳转，这里停止轮询
      if ((error as Error).message.includes('登录已过期')) {
        clearInterval(pollInterval.value!)
        clearInterval(progressInterval)
        pollInterval.value = null
      }
    }
  }, 2000) // 每2秒查询一次
}

const handleGenerate = async () => {
  isSubmitting.value = true
  try {
    // 获取当前配置
    const config = configPanelRef.value?.getConfig()
    
    if (!config) {
      alert('无法获取配置信息')
      return
    }
    
    // 自动保存配置
    const saveSuccess = await configPanelRef.value?.saveConfig()
    if (!saveSuccess) {
      console.warn('配置保存失败，继续生成...')
    }
    
    // 构建请求数据
    const requestData: {
      course: string
      knowledge_point: string
      difficulty: 'easy' | 'medium' | 'hard'
      config?: GenerationConfigCreate
    } = {
      course: form.value.course,
      knowledge_point: form.value.knowledge_point,
      difficulty: 'medium'  // 默认难度，实际使用配置中的 difficulty
    }
    
    // 添加配置到请求中，并使用配置中的难度
    requestData.config = config
    // 将配置中的 difficulty 映射到请求中的 difficulty（向后兼容）
    const difficultyMap: Record<string, 'easy' | 'medium' | 'hard'> = {
      'beginner': 'easy',
      'intermediate': 'medium',
      'advanced': 'hard'
    }
    requestData.difficulty = difficultyMap[config.difficulty] || 'medium'
    
    const response: TaskResponse = await generateOutline(requestData)

    // 设置初始任务状态
    currentTask.value = {
      task_id: response.task_id,
      status: 'pending',
      task_type: 'generate_outline',
      created_at: new Date().toISOString()
    }

    // 开始轮询
    startPolling(response.task_id)
  } catch (error) {
    console.error('创建任务失败:', error)
    alert('创建任务失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

const goToOutline = () => {
  if (currentTask.value?.result?.outline_id) {
    router.push(`/outline/${currentTask.value.result.outline_id}/edit`)
  }
}

const resetTask = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
  currentTask.value = null
  progressPercent.value = 10
}

// 组件卸载时清除轮询
onUnmounted(() => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
})
</script>
