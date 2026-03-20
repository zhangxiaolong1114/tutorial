<template>
  <div class="max-w-6xl mx-auto h-full flex flex-col">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">我的文档</h1>
      <router-link
        to="/generate"
        class="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
      >
        新建文档
      </router-link>
    </div>

    <!-- 文档列表 -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <div v-else-if="documents.length === 0" class="text-center py-12 bg-white rounded-xl shadow-sm">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无文档</h3>
      <p class="mt-1 text-sm text-gray-500">点击上方按钮创建你的第一个教学文档</p>
    </div>

    <div v-else class="space-y-4 overflow-y-auto flex-1 pb-6 min-h-0">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ doc.title }}</h3>
            <div class="flex items-center gap-4 text-sm text-gray-500">
              <span>创建于 {{ formatDate(doc.created_at) }}</span>
              <span v-if="doc.sections">{{ doc.sections.length }} 个章节</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="viewDocument(doc.id)"
              class="px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
            >
              查看
            </button>
            <button
              @click="downloadDocument(doc.id)"
              class="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              下载
            </button>
            <button
              @click="deleteDocument(doc.id)"
              class="px-3 py-1.5 text-sm bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/index'

interface Document {
  id: number
  title: string
  outline_id: number
  sections: any[]
  created_at: string
}

const router = useRouter()
const documents = ref<Document[]>([])
const loading = ref(true)

const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await api.get('/documents/')
    console.log('加载文档响应:', response)
    documents.value = response || []
  } catch (error) {
    console.error('加载文档失败:', error)
    alert('加载文档失败: ' + (error as Error).message)
  } finally {
    loading.value = false
  }
}

const viewDocument = (id: number) => {
  router.push(`/document/${id}`)
}

const downloadDocument = async (id: number) => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/documents/${id}/download`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 获取文档标题作为文件名
    const doc = documents.value.find(d => d.id === id)
    const safeTitle = doc?.title?.replace(/[\\/:*?"<>|]/g, '_').trim() || `document-${id}`
    link.download = `${safeTitle}.html`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    alert('下载失败')
  }
}

const deleteDocument = async (id: number) => {
  if (!confirm('确定要删除这个文档吗？')) return

  try {
    await api.delete(`/documents/${id}`)
    documents.value = documents.value.filter(d => d.id !== id)
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败')
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadDocuments()
})
</script>
