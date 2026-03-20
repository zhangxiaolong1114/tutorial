<template>
  <div class="max-w-6xl mx-auto h-full flex flex-col min-h-0">
    <!-- 顶部导航 -->
    <div class="flex items-center justify-between mb-6 shrink-0">
      <div class="flex items-center gap-4">
        <button @click="$router.back()"
          class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors bg-white shadow-sm">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </button>
        <h1 class="text-2xl font-bold text-gray-900">{{ doc?.title || '文档详情' }}</h1>
      </div>
      <div class="flex gap-3">
        <button @click="downloadDocument"
          class="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors">
          下载 HTML
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-12 flex-1">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <!-- 文档内容 - 使用 iframe 展示完整 HTML -->
    <div v-else-if="doc" class="bg-white rounded-xl shadow-sm overflow-hidden flex-1 min-h-0">
      <iframe 
        ref="iframeRef"
        class="w-full h-full border-0"
        sandbox="allow-scripts allow-same-origin"
      ></iframe>
    </div>

    <!-- 错误状态 -->
    <div v-else class="text-center py-12 bg-white rounded-xl shadow-sm flex-1">
      <p class="text-gray-500">文档不存在或已被删除</p>
      <router-link to="/documents"
        class="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
        返回文档列表
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/index'

interface Document {
  id: number
  title: string
  html_content: string
  created_at: string
}

const route = useRoute()
const router = useRouter()
const documentId = route.params.id as string

const doc = ref<Document | null>(null)
const loading = ref(true)
const iframeRef = ref<HTMLIFrameElement | null>(null)

const loadDocument = async () => {
  loading.value = true
  try {
    // 使用统一的 api 模块，它会自动处理 token 和 401 跳转
    const data = await api.get<Document>(`/documents/${documentId}`)
    doc.value = data
    
    // 使用 setTimeout 确保 iframe 已经渲染
    setTimeout(() => {
      writeToIframe(data.html_content)
    }, 100)
  } catch (error: any) {
    console.error('加载文档失败:', error)
    // api 模块已经处理了 401 跳转，这里只需要处理其他错误
    if (error.message?.includes('404')) {
      doc.value = null
    }
  } finally {
    loading.value = false
  }
}

const writeToIframe = (htmlContent: string) => {
  if (!iframeRef.value || !htmlContent) {
    console.error('iframe 或内容不存在')
    return
  }
  
  const iframe = iframeRef.value
  
  try {
    // 使用 srcdoc 属性直接设置内容
    iframe.srcdoc = htmlContent
    console.log('文档已写入 iframe，内容长度:', htmlContent.length)
  } catch (e) {
    console.error('写入 iframe 失败:', e)
    // 降级方案：使用传统方式
    const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
    if (iframeDoc) {
      iframeDoc.open()
      iframeDoc.write(htmlContent)
      iframeDoc.close()
    }
  }
}

const downloadDocument = async () => {
  if (!doc.value) return

  try {
    const safeTitle = doc.value.title.replace(/[\\/:*?"<>|]/g, '_').trim() || 'document'
    await api.download(`/documents/${documentId}/download`, `${safeTitle}.html`)
  } catch (error) {
    console.error('下载失败:', error)
    alert('下载失败')
  }
}

onMounted(() => {
  loadDocument()
})
</script>
