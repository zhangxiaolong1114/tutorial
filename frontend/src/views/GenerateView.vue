<template>
  <div class="max-w-4xl mx-auto h-full flex flex-col overflow-y-auto pb-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('generate.title') }}</h1>

    <!-- 生成表单 -->
    <div v-if="!currentTask" class="bg-white rounded-xl shadow-sm p-6 mb-6">
      <p class="text-gray-600 mb-6">{{ $t('generate.tip') }}</p>

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

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.difficulty') }}</label>
          <select v-model="form.difficulty"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option value="easy">{{ $t('generate.difficultyEasy') }}</option>
            <option value="medium">{{ $t('generate.difficultyMedium') }}</option>
            <option value="hard">{{ $t('generate.difficultyHard') }}</option>
          </select>
        </div>

        <button type="submit" :disabled="isSubmitting"
          class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          {{ isSubmitting ? '提交中...' : $t('generate.generateButton') }}
        </button>
      </form>
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
import type { TaskResponse, TaskStatusResponse } from '../types/outline'

const router = useRouter()
const isSubmitting = ref(false)
const currentTask = ref<TaskStatusResponse | null>(null)
const pollInterval = ref<number | null>(null)
const progressPercent = ref(10)

const form = ref({
  course: '',
  knowledge_point: '',
  difficulty: 'medium' as 'easy' | 'medium' | 'hard'
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
    const response: TaskResponse = await generateOutline({
      course: form.value.course,
      knowledge_point: form.value.knowledge_point,
      difficulty: form.value.difficulty
    })

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
