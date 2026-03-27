<template>
  <div class="max-w-6xl mx-auto h-full flex flex-col overflow-y-auto pb-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">编辑大纲</h1>
      <div class="flex gap-3">
        <router-link to="/tasks"
          class="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors">
          任务中心
        </router-link>
        <button @click="handleSave" :disabled="isSaving"
          class="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50">
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
        <button @click="showModelSelector = true" :disabled="isGenerating"
          class="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
          {{ isGenerating ? '提交中...' : '生成文档' }}
        </button>
      </div>
    </div>

    <!-- 生成文档任务状态 -->
    <div v-if="currentTask" class="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-semibold text-blue-900">文档生成中</h3>
          <p class="text-sm text-blue-700 mt-1">{{ taskStatusText }}</p>
        </div>
        <div class="flex items-center gap-3">
          <div v-if="currentTask.status === 'pending' || currentTask.status === 'processing'"
            class="flex items-center gap-2">
            <div class="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
            <span class="text-sm text-blue-600">处理中...</span>
          </div>
          <router-link v-if="currentTask.status === 'completed' && currentTask.result?.document_id"
            :to="`/document/${currentTask.result.document_id}`"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
            查看文档
          </router-link>
          <router-link :to="`/tasks?highlight=${currentTask.task_id}`"
            class="px-4 py-2 bg-white text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-50 transition-colors">
            任务详情
          </router-link>
        </div>
      </div>
      <!-- 进度条 -->
      <div v-if="currentTask.status === 'pending' || currentTask.status === 'processing'" class="mt-4">
        <div class="w-full bg-blue-200 rounded-full h-2">
          <div class="bg-blue-600 h-2 rounded-full transition-all duration-500"
            :style="{ width: progressPercent + '%' }"></div>
        </div>
        <p class="text-xs text-blue-600 mt-1">预计耗时 10-20 分钟</p>
      </div>
    </div>

    <!-- 大纲信息 -->
    <div v-if="outline" class="bg-white rounded-xl shadow-sm p-6 mb-6">
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        <div>
          <span class="text-gray-500">课程:</span>
          <span class="ml-2 font-medium">{{ outline.course }}</span>
        </div>
        <div>
          <span class="text-gray-500">知识点:</span>
          <span class="ml-2 font-medium">{{ outline.knowledge_point }}</span>
        </div>
        <div>
          <span class="text-gray-500">难度:</span>
          <span class="ml-2 font-medium">{{ difficultyText }}</span>
        </div>
      </div>
    </div>

    <!-- 模型选择弹窗 -->
    <div v-if="showModelSelector" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div class="p-6 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">选择 AI 模型</h3>
            <button @click="showModelSelector = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="text-sm text-gray-500 mt-1">选择生成文档各章节使用的 AI 模型</p>
        </div>
        <div class="p-6 overflow-y-auto flex-1">
          <ModelSelector ref="modelSelectorRef" @change="onModelChange" />
        </div>
        <div class="p-6 border-t border-gray-200 flex justify-end gap-3">
          <button @click="showModelSelector = false"
            class="px-4 py-2 text-gray-700 font-medium rounded-lg hover:bg-gray-100 transition-colors">
            取消
          </button>
          <button @click="confirmGenerateDocument"
            class="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
            开始生成
          </button>
        </div>
      </div>
    </div>

    <!-- 章节列表 -->
    <div class="bg-white rounded-xl shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">章节结构</h2>
        <button @click="addSection"
          class="px-3 py-1.5 text-sm bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors">
          + 添加章节
        </button>
      </div>

      <div v-if="sections.length === 0" class="text-center py-12 text-gray-500">
        暂无章节，点击上方按钮添加
      </div>

      <div v-else class="space-y-4">
        <div v-for="(section, index) in sections" :key="section.id" class="border border-gray-200 rounded-lg p-4">
          <div class="flex items-start gap-4">
            <span
              class="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blue-50 text-blue-600 rounded-lg font-medium text-sm">
              {{ index + 1 }}
            </span>
            <div class="flex-1 space-y-3">
              <input v-model="section.title" type="text" placeholder="章节标题"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-medium" />
              <textarea v-model="section.content" rows="6" placeholder="内容要点（每行一个）"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-y min-h-[80px]"></textarea>
            </div>
            <button @click="removeSection(index)"
              class="flex-shrink-0 p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="删除章节">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { getOutline, updateOutline, generateDocument, getTaskStatus } from '../api/outline'
import ModelSelector from '../components/ModelSelector.vue'
import type { Outline, Section, TaskStatusResponse } from '../types/outline'
import type { ModelConfig } from '../api/aiModels'

const route = useRoute()
const outlineId = route.params.id as string

const outline = ref<Outline | null>(null)
const sections = ref<Section[]>([])
const isSaving = ref(false)
const isGenerating = ref(false)
const currentTask = ref<TaskStatusResponse | null>(null)
const pollInterval = ref<number | null>(null)
const progressPercent = ref(10)
const showModelSelector = ref(false)
const modelSelectorRef = ref<InstanceType<typeof ModelSelector> | null>(null)
const modelConfig = ref<ModelConfig>({})

const difficultyText = computed(() => {
  if (!outline.value) return ''
  const map: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[outline.value.difficulty] || outline.value.difficulty
})

const taskStatusText = computed(() => {
  switch (currentTask.value?.status) {
    case 'pending':
      return '任务已提交，等待处理...'
    case 'processing':
      return 'AI 正在生成文档内容...'
    case 'completed':
      return '文档生成完成！'
    case 'failed':
      return currentTask.value?.error_message || '生成失败'
    default:
      return '处理中...'
  }
})

// 加载大纲数据
const loadOutline = async () => {
  try {
    outline.value = await getOutline(outlineId)
    sections.value = (outline.value.sections || []).map(s => ({
      ...s,
      content: Array.isArray(s.content) ? s.content.join('\n') : s.content
    }))
  } catch (error) {
    console.error('加载大纲失败:', error)
    alert('加载大纲失败')
  }
}

// 添加章节
const addSection = () => {
  const newSection: Section = {
    id: `section_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    title: '',
    content: '',
    order: sections.value.length
  }
  sections.value.push(newSection)
}

// 删除章节
const removeSection = (index: number) => {
  if (confirm('确定要删除这个章节吗？')) {
    sections.value.splice(index, 1)
    sections.value.forEach((section, i) => {
      section.order = i
    })
  }
}

// 保存大纲
const handleSave = async () => {
  const emptyTitles = sections.value.filter(s => !s.title.trim())
  if (emptyTitles.length > 0) {
    alert('请填写所有章节的标题')
    return
  }

  isSaving.value = true
  try {
    const sectionsToSave = sections.value.map(s => ({
      ...s,
      content: s.content ? s.content.split('\n').filter(c => c.trim()) : []
    }))
    await updateOutline(outlineId, { sections: sectionsToSave })
    alert('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    alert('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 轮询任务状态
const startPolling = (taskId: number) => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }

  progressPercent.value = 10
  const progressTimer = setInterval(() => {
    if (progressPercent.value < 90 && currentTask.value?.status === 'processing') {
      progressPercent.value += Math.random() * 5
    }
  }, 2000)

  pollInterval.value = window.setInterval(async () => {
    try {
      const status = await getTaskStatus(taskId)
      currentTask.value = status

      if (status.status === 'completed' || status.status === 'failed') {
        clearInterval(pollInterval.value!)
        clearInterval(progressTimer)
        pollInterval.value = null
        progressPercent.value = status.status === 'completed' ? 100 : 0

        if (status.status === 'completed') {
          alert('文档生成成功！')
        }
      }
    } catch (error) {
      console.error('获取任务状态失败:', error)
      // 如果是 401 错误，api/index.ts 会处理跳转，这里停止轮询
      if ((error as Error).message.includes('登录已过期')) {
        clearInterval(pollInterval.value!)
        clearInterval(progressTimer)
        pollInterval.value = null
      }
    }
  }, 2000)
}

// 模型配置变化回调
const onModelChange = () => {
  console.log("change")
  const modelConfigData = modelSelectorRef.value?.getModelConfig()
  if (modelConfigData && (modelConfigData.outline_model_id || modelConfigData.section_model_id || modelConfigData.simulation_model_id)) {
    modelConfig.value = modelConfigData
  }
  console.log(modelConfig.value)
}

// 确认生成文档（带模型选择）
const confirmGenerateDocument = async () => {
  showModelSelector.value = false
  await handleSave()

  isGenerating.value = true
  try {
    // 获取模型配置
    const modelConfigData = modelSelectorRef.value?.getModelConfig()
    console.log('从 ModelSelector 获取的配置:', modelConfigData)

    // 检查是否有选择的模型
    const hasSelectedModel = modelConfigData && (
      modelConfigData.outline_model_id ||
      modelConfigData.section_model_id ||
      modelConfigData.simulation_model_id
    )

    if (hasSelectedModel) {
      modelConfig.value = JSON.parse(JSON.stringify(modelConfigData))
      console.log('更新后的 modelConfig:', modelConfig.value)
    } else {
      console.log('没有选择模型，使用默认配置')
      modelConfig.value = {}
    }

    // 再次检查 modelConfig 是否有实际内容
    const hasModelConfig = modelConfig.value && (
      modelConfig.value.outline_model_id ||
      modelConfig.value.section_model_id ||
      modelConfig.value.simulation_model_id
    )

    console.log('最终传递的配置:', hasModelConfig ? modelConfig.value : undefined)
    const result = await generateDocument(outlineId, hasModelConfig ? modelConfig.value : undefined)

    currentTask.value = <any>{
      task_id: result.task_id,
      status: 'pending',
      task_type: 'generate_document',
      created_at: new Date().toISOString()
    }

    startPolling(result.task_id)
  } catch (error) {
    console.error('创建任务失败:', error)
    alert('创建任务失败')
  } finally {
    isGenerating.value = false
  }
}

onMounted(() => {
  loadOutline()
})

onUnmounted(() => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
})
</script>
