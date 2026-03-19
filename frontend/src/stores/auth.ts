import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: number
  name: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  
  const isAuthenticated = computed(() => !!token.value)
  
  const login = async (email: string, password: string) => {
    // TODO: Implement actual login API call
    user.value = { id: 1, name: 'User', email }
    token.value = 'fake-token'
    localStorage.setItem('token', token.value)
  }
  
  const register = async (name: string, email: string, password: string) => {
    // TODO: Implement actual register API call
    user.value = { id: 1, name, email }
    token.value = 'fake-token'
    localStorage.setItem('token', token.value)
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }
  
  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout
  }
})
