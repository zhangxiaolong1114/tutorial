import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api'

interface Document {
  id: number
  title: string
  content: string
  status: 'draft' | 'generating' | 'completed'
  createdAt: string
  updatedAt: string
}

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<Document[]>([])
  const currentDocument = ref<Document | null>(null)
  const isLoading = ref(false)
  
  const fetchDocuments = async () => {
    isLoading.value = true
    try {
      // TODO: Implement actual API call
      // documents.value = await api.get<Document[]>('/documents')
    } finally {
      isLoading.value = false
    }
  }
  
  const fetchDocument = async (id: number) => {
    isLoading.value = true
    try {
      // TODO: Implement actual API call
      // currentDocument.value = await api.get<Document>(`/documents/${id}`)
    } finally {
      isLoading.value = false
    }
  }
  
  const createDocument = async (title: string, prompt: string) => {
    // TODO: Implement actual API call
    // return await api.post<Document>('/documents', { title, prompt })
  }
  
  const updateDocument = async (id: number, data: Partial<Document>) => {
    // TODO: Implement actual API call
    // return await api.put<Document>(`/documents/${id}`, data)
  }
  
  const deleteDocument = async (id: number) => {
    // TODO: Implement actual API call
    // await api.delete(`/documents/${id}`)
  }
  
  return {
    documents,
    currentDocument,
    isLoading,
    fetchDocuments,
    fetchDocument,
    createDocument,
    updateDocument,
    deleteDocument
  }
})
