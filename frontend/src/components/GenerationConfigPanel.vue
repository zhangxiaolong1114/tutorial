<template>
  <div class="generation-config-panel">
    <h3 class="panel-title">⚙️ 生成配置</h3>
    <p class="panel-desc">自定义 AI 生成内容的风格、深度和格式</p>

    <form class="config-form" @submit.prevent>
      <!-- 风格层 -->
      <div class="form-section">
        <h4 class="section-title">🎭 风格设置</h4>
        
        <div class="form-row">
          <div class="form-group">
            <label>语气风格</label>
            <select v-model="config.tone" class="form-select">
              <option v-for="(label, value) in configLabels.tone" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>目标受众</label>
            <select v-model="config.target_audience" class="form-select">
              <option v-for="(label, value) in configLabels.target_audience" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- 难度设置（突出显示） -->
      <div class="form-section difficulty-section">
        <h4 class="section-title">🎯 难度等级</h4>
        
        <div class="difficulty-options">
          <label 
            v-for="(label, value) in configLabels.difficulty" 
            :key="value"
            class="difficulty-option"
            :class="{ active: config.difficulty === value }"
          >
            <input 
              type="radio" 
              :value="value" 
              v-model="config.difficulty"
              class="sr-only"
            />
            <span class="difficulty-label">{{ label }}</span>
          </label>
        </div>
      </div>

      <!-- 结构层 -->
      <div class="form-section">
        <h4 class="section-title">📚 内容结构</h4>
        
        <div class="form-row">
          <div class="form-group">
            <label>教学风格</label>
            <select v-model="config.teaching_style" class="form-select">
              <option v-for="(label, value) in configLabels.teaching_style" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>内容样式</label>
            <select v-model="config.content_style" class="form-select">
              <option v-for="(label, value) in configLabels.content_style" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- 深度层 -->
      <div class="form-section">
        <h4 class="section-title">📐 公式与推导</h4>
        
        <div class="form-row">
          <div class="form-group">
            <label>公式详细度</label>
            <select v-model="config.formula_detail" class="form-select">
              <option v-for="(label, value) in configLabels.formula_detail" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>内容样式</label>
            <select v-model="config.content_style" class="form-select">
              <option v-for="(label, value) in configLabels.content_style" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- 格式设置 -->
      <div class="form-section">
        <h4 class="section-title">📄 格式设置</h4>
        
        <div class="form-row">
          <div class="form-group">
            <label>输出格式</label>
            <select v-model="config.output_format" class="form-select">
              <option v-for="(label, value) in configLabels.output_format" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>代码语言</label>
            <select v-model="config.code_language" class="form-select">
              <option v-for="(label, value) in configLabels.code_language" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>章节粒度</label>
            <select v-model="config.chapter_granularity" class="form-select">
              <option v-for="(label, value) in configLabels.chapter_granularity" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>引用规范</label>
            <select v-model="config.citation_style" class="form-select">
              <option v-for="(label, value) in configLabels.citation_style" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- 增强选项 -->
      <div class="form-section">
        <h4 class="section-title">✨ 增强选项</h4>
        
        <div class="form-row">
          <div class="form-group">
            <label>互动元素</label>
            <select v-model="config.interactive_elements" class="form-select">
              <option v-for="(label, value) in configLabels.interactive_elements" :key="value" :value="value">
                {{ label }}
              </option>
            </select>
          </div>
        </div>
        
        <div class="checkbox-row">
          <label class="checkbox-label">
            <input type="checkbox" v-model="config.need_images" />
            <span>包含配图建议</span>
          </label>
        </div>
      </div>

      <!-- 仿真设置 -->
      <div class="form-section">
        <h4 class="section-title">🔬 仿真设置</h4>
        
        <div class="checkbox-row">
          <label class="checkbox-label">
            <input type="checkbox" v-model="config.need_simulation" />
            <span>生成交互仿真</span>
          </label>
        </div>
        
        <div v-if="config.need_simulation" class="simulation-types">
          <p class="hint">选择仿真类型（可多选）：</p>
          <div class="checkbox-group">
            <label 
              v-for="(label, value) in configLabels.simulation_types" 
              :key="value" 
              class="checkbox-label"
            >
              <input 
                type="checkbox" 
                :value="value" 
                v-model="config.simulation_types"
              />
              <span>{{ label }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- 操作按钮已移除，配置会在生成时自动保存 -->
    </form>

    <!-- 历史配置 -->
    <div v-if="history.length > 0" class="config-history">
      <h4 class="section-title">📜 历史配置</h4>
      <div class="history-list">
        <div 
          v-for="item in history" 
          :key="item.id" 
          class="history-item"
          @click="loadConfig(item)"
        >
          <div class="history-info">
            <span class="history-tone">{{ configLabels.tone[item.tone] }}</span>
            <span class="history-style">{{ configLabels.teaching_style[item.teaching_style] }}</span>
            <span class="history-difficulty">{{ configLabels.difficulty[item.difficulty] }}</span>
          </div>
          <span class="history-date">{{ formatDate(item.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { generationConfigApi } from '@/api/generationConfig'
import { 
  type GenerationConfig, 
  type GenerationConfigCreate,
  configLabels, 
  defaultConfig 
} from '@/types/generationConfig'

// Props & Emits
const props = defineProps<{
  initialConfig?: GenerationConfigCreate
}>()

const emit = defineEmits<{
  (e: 'save', config: GenerationConfigCreate): void
  (e: 'load', config: GenerationConfig): void
}>()

// State
const config = ref<GenerationConfigCreate>({ ...defaultConfig })
const history = ref<GenerationConfig[]>([])

// 初始化
onMounted(async () => {
  // 加载初始配置
  if (props.initialConfig) {
    config.value = { ...props.initialConfig }
  } else {
    // 尝试加载最新配置
    try {
      const latest = await generationConfigApi.getLatest()
      if (latest) {
        config.value = {
          tone: latest.tone,
          teaching_style: latest.teaching_style,
          content_style: latest.content_style,
          difficulty: latest.difficulty,
          formula_detail: latest.formula_detail,
          target_audience: latest.target_audience,
          output_format: latest.output_format,
          code_language: latest.code_language,
          chapter_granularity: latest.chapter_granularity,
          citation_style: latest.citation_style,
          interactive_elements: latest.interactive_elements,
          need_simulation: latest.need_simulation,
          simulation_types: latest.simulation_types,
          need_images: latest.need_images
        }
      }
    } catch (error) {
      console.error('加载最新配置失败:', error)
    }
  }
  
  // 加载历史
  loadHistory()
})

// 加载历史配置
const loadHistory = async () => {
  try {
    const response = await generationConfigApi.getHistory(5)
    history.value = response.configs
  } catch (error) {
    console.error('加载配置历史失败:', error)
  }
}

// 保存配置（供父组件调用）
const saveConfig = async (): Promise<boolean> => {
  try {
    // 验证仿真类型
    if (config.value.need_simulation && config.value.simulation_types.length === 0) {
      console.error('保存配置失败: 未选择仿真类型')
      alert('请选择至少一种仿真类型')
      return false
    }

    console.log('正在保存配置:', JSON.stringify(config.value, null, 2))

    // 保存到后端
    const response = await generationConfigApi.create(config.value)
    console.log('配置保存成功:', response)

    // 通知父组件
    emit('save', { ...config.value })

    // 刷新历史
    loadHistory()

    return true
  } catch (error: any) {
    console.error('保存配置失败:', error)

    // 详细错误信息
    const errorDetails = {
      message: error.message,
      name: error.name,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url,
      config: config.value
    }
    console.error('错误详情:', errorDetails)

    // 根据错误类型显示不同提示
    if (error.message === 'Failed to fetch') {
      alert('保存配置失败: 无法连接到服务器，请检查后端服务是否启动')
    } else if (error.response?.status === 500) {
      alert(`保存配置失败: 服务器内部错误 (${error.response?.data?.detail || '未知错误'})`)
    } else if (error.response?.status === 401) {
      alert('保存配置失败: 登录已过期，请重新登录')
    } else if (error.response?.status === 422) {
      alert(`保存配置失败: 数据验证错误 (${JSON.stringify(error.response?.data)})`)
    } else {
      alert(`保存配置失败: ${error.message || '未知错误'}`)
    }

    return false
  }
}

// 重置配置
const resetConfig = () => {
  config.value = { ...defaultConfig }
}

// 加载历史配置
const loadConfig = (item: GenerationConfig) => {
  config.value = {
    tone: item.tone,
    teaching_style: item.teaching_style,
    content_style: item.content_style,
    difficulty: item.difficulty,
    formula_detail: item.formula_detail,
    target_audience: item.target_audience,
    output_format: item.output_format,
    code_language: item.code_language,
    chapter_granularity: item.chapter_granularity,
    citation_style: item.citation_style,
    interactive_elements: item.interactive_elements,
    need_simulation: item.need_simulation,
    simulation_types: item.simulation_types,
    need_images: item.need_images
  }
  emit('load', item)
}

// 格式化日期（后端已返回本地时间格式）
const formatDate = (dateStr: string) => {
  // 后端返回格式: '2026-03-23 15:30:00'
  if (!dateStr) return ''
  
  // 如果已经是格式化字符串，直接显示
  if (dateStr.includes(' ')) {
    const [date, time] = dateStr.split(' ')
    const [year, month, day] = date.split('-')
    const [hour, minute] = time.split(':')
    return `${month}月${day}日 ${hour}:${minute}`
  }
  
  // 兼容 ISO 格式
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 暴露方法给父组件
defineExpose({
  getConfig: () => ({ ...config.value }),
  setConfig: (newConfig: GenerationConfigCreate) => {
    config.value = { ...newConfig }
  },
  saveConfig
})
</script>

<style scoped>
.generation-config-panel {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  margin-right: -8px;
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

.panel-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.panel-desc {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 20px;
}



.form-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 16px;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.form-select:hover {
  border-color: #3b82f6;
}

.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.checkbox-row {
  margin-top: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  color: #374151;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.simulation-types {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.hint {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 8px;
}

.checkbox-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.btn-primary {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #f3f4f6;
}

.config-history {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #e0e7ff;
}

.history-info {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.history-info span {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: white;
}

.history-tone {
  color: #3b82f6;
}

.history-style {
  color: #8b5cf6;
}

.history-difficulty {
  color: #10b981;
}

.history-date {
  font-size: 0.75rem;
  color: #64748b;
}

/* 难度选择特殊样式 */
.difficulty-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #bae6fd;
}

.difficulty-options {
  display: flex;
  gap: 8px;
}

.difficulty-option {
  flex: 1;
  cursor: pointer;
}

.difficulty-option input {
  position: absolute;
  opacity: 0;
}

.difficulty-label {
  display: block;
  padding: 10px 16px;
  text-align: center;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  transition: all 0.2s;
}

.difficulty-option:hover .difficulty-label {
  border-color: #3b82f6;
  color: #3b82f6;
}

.difficulty-option.active .difficulty-label {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .checkbox-group {
    flex-direction: column;
    gap: 8px;
  }
  
  .difficulty-options {
    flex-direction: column;
  }
}
</style>
