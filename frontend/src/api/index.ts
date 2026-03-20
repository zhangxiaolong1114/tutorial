// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  params?: Record<string, string>
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options

  let url = `${API_BASE_URL}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams(params)
    url += `?${searchParams.toString()}`
  }

  // 从 localStorage 获取 token
  const token = localStorage.getItem('token')

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers as Record<string, string>
  }

  // 如果有 token，添加到请求头
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers
  })

  if (!response.ok) {
    // 401 未授权，清除 token 并跳转登录页
    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      throw new Error('登录已过期，请重新登录')
    }
    throw new Error(`API Error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: 'GET' }),
  
  post: <T>(endpoint: string, data: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'POST', body: JSON.stringify(data) }),
  
  put: <T>(endpoint: string, data: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  
  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' })
}

export default api
