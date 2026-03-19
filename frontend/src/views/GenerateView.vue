<template>
  <div class="max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ $t('generate.title') }}</h1>
    
    <div class="bg-white rounded-xl shadow-sm p-6 mb-6">
      <p class="text-gray-600 mb-6">{{ $t('generate.tip') }}</p>
      
      <form @submit.prevent="handleGenerate" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.courseName') }}</label>
            <input
              v-model="form.course"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="$t('generate.coursePlaceholder')"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.knowledgePoint') }}</label>
            <input
              v-model="form.knowledge"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="$t('generate.knowledgePlaceholder')"
            />
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.difficulty') }}</label>
            <select
              v-model="form.difficulty"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="easy">{{ $t('generate.difficultyEasy') }}</option>
              <option value="medium">{{ $t('generate.difficultyMedium') }}</option>
              <option value="hard">{{ $t('generate.difficultyHard') }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">{{ $t('generate.grade') }}</label>
            <input
              v-model="form.grade"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="$t('generate.gradePlaceholder')"
            />
          </div>
        </div>
        
        <button
          type="submit"
          :disabled="isGenerating"
          class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isGenerating ? $t('generate.generating') : $t('generate.generateButton') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isGenerating = ref(false)

const form = ref({
  course: '',
  knowledge: '',
  difficulty: 'medium',
  grade: ''
})

const handleGenerate = async () => {
  isGenerating.value = true
  // TODO: 调用 API 生成文档
  setTimeout(() => {
    isGenerating.value = false
    router.push('/documents')
  }, 2000)
}
</script>
