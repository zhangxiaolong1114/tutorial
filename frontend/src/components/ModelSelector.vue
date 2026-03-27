<template>
  <div class="generation-config-panel">
    <h3 class="panel-title">🤖 AI 模型配置</h3>
    <p class="panel-desc">选择生成内容使用的 AI 模型</p>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载模型列表...</span>
    </div>

    <!-- 模型选择 -->
    <div v-else class="config-form">
      <!-- 大纲生成模型 -->
      <div class="form-section">
        <h4 class="section-title">📋 大纲生成</h4>
        <div class="form-row">
          <div class="form-group" style="grid-column: 1 / -1;">
            <select v-model="selectedModels.outline" class="form-select" @change="onModelChange">
              <option value="">使用默认模型</option>
              <optgroup label="推荐模型">
                <option v-for="model in outlineRecommendations" :key="model.id" :value="model.id">
                  {{ model.name }} {{ getPriceTag(model) }} {{ getBadge(model) }}
                </option>
              </optgroup>
              <optgroup label="全部模型">
                <option v-for="model in outlineModels" :key="model.id" :value="model.id">
                  {{ model.name }} {{ getPriceTag(model) }}
                </option>
              </optgroup>
            </select>
            <!-- <p v-if="outlineModel" class="model-desc">
              {{ getModelDesc(outlineModel) }}
            </p> -->
          </div>
        </div>
      </div>

      <!-- 章节内容模型 -->
      <div class="form-section">
        <h4 class="section-title">📝 章节内容</h4>
        <div class="form-row">
          <div class="form-group" style="grid-column: 1 / -1;">
            <select v-model="selectedModels.section" class="form-select" @change="onModelChange">
              <option value="">使用默认模型</option>
              <optgroup label="推荐模型">
                <option v-for="model in sectionRecommendations" :key="model.id" :value="model.id">
                  {{ model.name }} {{ getPriceTag(model) }} {{ getBadge(model) }}
                </option>
              </optgroup>
              <optgroup label="全部模型">
                <option v-for="model in sectionModels" :key="model.id" :value="model.id">
                  {{ model.name }} {{ getPriceTag(model) }}
                </option>
              </optgroup>
            </select>
            <!-- <p v-if="sectionModel" class="model-desc">
              {{ getModelDesc(sectionModel) }}
            </p> -->
          </div>
        </div>
      </div>

      <!-- 交互仿真模型 -->
      <div class="form-section">
        <h4 class="section-title">🔬 交互仿真</h4>
        <div class="form-row">
          <div class="form-group" style="grid-column: 1 / -1;">
            <select v-model="selectedModels.simulation" class="form-select" @change="onModelChange">
              <option value="">使用默认模型</option>
              <optgroup label="推荐模型">
                <option v-for="model in simulationRecommendations" :key="model.id" :value="model.id">
                  {{ model.name }} {{ getPriceTag(model) }} {{ getBadge(model) }}
                </option>
              </optgroup>
              <optgroup label="全部模型">
                <option v-for="model in simulationModels" :key="model.id" :value="model.id">
                  {{ model.name }} {{ getPriceTag(model) }}
                </option>
              </optgroup>
            </select>
            <!-- <p v-if="simulationModel" class="model-desc">
              {{ getModelDesc(simulationModel) }}
            </p> -->
          </div>
        </div>
      </div>

      <!-- 快速推荐 -->
      <div class="form-section">
        <h4 class="section-title">💡 快速配置</h4>
        <div class="difficulty-options">
          <button v-for="preset in presets" :key="preset.name" class="difficulty-option"
            :class="{ active: isPresetActive(preset) }" @click="applyPreset(preset)" type="button">
            {{ preset.name }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { aiModelsApi, type ModelInfo, type ModelRecommendation } from '@/api/aiModels'

interface ModelSelection {
  outline: string
  section: string
  simulation: string
}

interface Preset {
  name: string
  outline: string
  section: string
  simulation: string
}

// State
const loading = ref(true)
const allModels = ref<ModelInfo[]>([])
const recommendations = ref<{
  outline: ModelRecommendation[]
  section: ModelRecommendation[]
  simulation: ModelRecommendation[]
}>({
  outline: [],
  section: [],
  simulation: []
})

const selectedModels = ref<ModelSelection>({
  outline: '',
  section: '',
  simulation: ''
})

// 预设配置（仅国内模型）
const presets: Preset[] = [
  {
    name: '⚡ 极速',
    outline: 'deepseek-reasoner',
    section: 'deepseek-reasoner',
    simulation: 'deepseek-reasoner'
  },
  {
    name: '⭐ 均衡',
    outline: 'deepseek-reasoner',
    section: 'kimi-k2.5',
    simulation: 'kimi-k2.5'
  },
  {
    name: '🎯 质量',
    outline: 'kimi-k2.5',
    section: 'kimi-k2.5',
    simulation: 'kimi-k2.5'
  },
  {
    name: '🔬 仿真',
    outline: 'deepseek-reasoner',
    section: 'kimi-k2.5',
    simulation: 'Qwen-3.5-Plus'
  }
]

// Computed
const outlineModels = computed(() =>
  allModels.value.filter(m => m.supported_tasks.includes('outline'))
)

const sectionModels = computed(() =>
  allModels.value.filter(m => m.supported_tasks.includes('section'))
)

const simulationModels = computed(() =>
  allModels.value.filter(m => m.supported_tasks.includes('simulation'))
)

const outlineRecommendations = computed(() => recommendations.value.outline)
const sectionRecommendations = computed(() => recommendations.value.section)
const simulationRecommendations = computed(() => recommendations.value.simulation)

const outlineModel = computed(() =>
  allModels.value.find(m => m.id === selectedModels.value.outline)
)

const sectionModel = computed(() =>
  allModels.value.find(m => m.id === selectedModels.value.section)
)

const simulationModel = computed(() =>
  allModels.value.find(m => m.id === selectedModels.value.simulation)
)

// Methods
const loadModels = async () => {
  loading.value = true
  try {
    const [models, outlineRecs, sectionRecs, simulationRecs] = await Promise.all([
      aiModelsApi.getModels(),
      aiModelsApi.getRecommendations('outline'),
      aiModelsApi.getRecommendations('section'),
      aiModelsApi.getRecommendations('simulation')
    ])

    allModels.value = models
    recommendations.value = {
      outline: outlineRecs,
      section: sectionRecs,
      simulation: simulationRecs
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  } finally {
    loading.value = false
  }
}

const getPriceTag = (model: ModelInfo) => {
  if (model.output_price_per_1k < 0.01) return '💰'
  if (model.output_price_per_1k < 0.1) return '💰💰'
  return '💰💰💰'
}

const getBadge = (model: ModelRecommendation) => {
  const badges = []
  if (model.reasons.includes('默认推荐')) badges.push('⭐')
  if (model.reasons.includes('性价比高')) badges.push('🏷️')
  if (model.speed_score >= 4) badges.push('⚡')
  if (model.quality_score >= 5) badges.push('🎯')
  return badges.join(' ')
}

const getModelDesc = (model: ModelInfo) => {
  const parts = []
  if (model.speed_score >= 4) parts.push('速度快')
  if (model.quality_score >= 4) parts.push('质量高')
  parts.push(`¥${model.output_price_per_1k}/1k tokens`)
  return parts.join(' · ')
}

const onModelChange = () => {
  // 触发更新，让父组件获取最新配置
}

const applyPreset = (preset: Preset) => {
  selectedModels.value = {
    outline: preset.outline,
    section: preset.section,
    simulation: preset.simulation
  }
  console.log(selectedModels.value)
}

const isPresetActive = (preset: Preset) => {
  return selectedModels.value.outline === preset.outline &&
    selectedModels.value.section === preset.section &&
    selectedModels.value.simulation === preset.simulation
}

// 暴露方法给父组件
defineExpose({
  getModelConfig: () => ({
    outline_model_id: selectedModels.value.outline || undefined,
    section_model_id: selectedModels.value.section || undefined,
    simulation_model_id: selectedModels.value.simulation || undefined
  }),
  setModelConfig: (config: { outline?: string; section?: string; simulation?: string }) => {
    selectedModels.value.outline = config.outline || ''
    selectedModels.value.section = config.section || ''
    selectedModels.value.simulation = config.simulation || ''
  }
})

// Lifecycle
onMounted(() => {
  loadModels()
})
</script>

<style scoped>
/* 复用 GenerationConfigPanel 的样式 */
.generation-config-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.panel-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.panel-desc {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 16px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: #64748b;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  margin-right: -8px;
  min-height: 0;
}

/* 自定义滚动条 */
.config-form::-webkit-scrollbar {
  width: 6px;
}

.config-form::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.config-form::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.config-form::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.form-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
  width: 100%;
}

.form-select:hover {
  border-color: #3b82f6;
}

.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.model-desc {
  margin-top: 4px;
  font-size: 0.75rem;
  color: #64748b;
}

/* 快速配置按钮样式 - 复用难度选择的样式 */
.difficulty-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.difficulty-option {
  flex: 1;
  min-width: 60px;
  padding: 8px 12px;
  text-align: center;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.difficulty-option:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.difficulty-option.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

@media (max-width: 640px) {
  .difficulty-options {
    flex-direction: column;
  }

  .difficulty-option {
    width: 100%;
  }
}
</style>
