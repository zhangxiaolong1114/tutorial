<template>
  <div class="max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ $t('document.title') }}</h1>
      <router-link
        to="/generate"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        {{ $t('nav.generate') }}
      </router-link>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm">
      <div v-if="documents.length === 0" class="p-12 text-center">
        <p class="text-gray-500 mb-4">{{ $t('document.noDocuments') }}</p>
        <router-link to="/generate" class="text-blue-600 hover:underline">
          {{ $t('document.createFirst') }}
        </router-link>
      </div>
      
      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-6 py-4 text-left text-sm font-medium text-gray-700">{{ $t('generate.knowledgePoint') }}</th>
            <th class="px-6 py-4 text-left text-sm font-medium text-gray-700">{{ $t('generate.courseName') }}</th>
            <th class="px-6 py-4 text-left text-sm font-medium text-gray-700">{{ $t('document.createTime') }}</th>
            <th class="px-6 py-4 text-left text-sm font-medium text-gray-700">{{ $t('document.actions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="doc in documents" :key="doc.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm text-gray-900">{{ doc.title }}</td>
            <td class="px-6 py-4 text-sm text-gray-600">{{ doc.course }}</td>
            <td class="px-6 py-4 text-sm text-gray-600">{{ doc.createdAt }}</td>
            <td class="px-6 py-4 text-sm space-x-2">
              <router-link
                :to="`/document/${doc.id}`"
                class="text-blue-600 hover:text-blue-800"
              >
                {{ $t('document.view') }}
              </router-link>
              <button class="text-red-600 hover:text-red-800" @click="deleteDoc(doc.id)">
                {{ $t('document.delete') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Document {
  id: number
  title: string
  course: string
  createdAt: string
}

const documents = ref<Document[]>([
  // 示例数据
  { id: 1, title: '牛顿第二定律', course: '大学物理', createdAt: '2026-03-19' },
  { id: 2, title: '欧姆定律', course: '电路原理', createdAt: '2026-03-18' },
])

const deleteDoc = (id: number) => {
  if (confirm('确定要删除吗？')) {
    documents.value = documents.value.filter(d => d.id !== id)
  }
}
</script>
