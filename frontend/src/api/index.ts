// API client configuration with auto token refresh
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  params?: Record<string, string>
}

// 是否正在刷新 token 的标志
let isRefreshing = false
// 等待刷新完成的请求队列
let refreshSubscribers: ((token: string) => void)[] = []

// 订阅 token 刷新
function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback)
}

// 通知所有订阅者新 token
function onTokenRefreshed(newToken: string) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// 尝试刷新 token
async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refreshToken')
  
  if (!refreshToken) {
    return null
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    })
    
    if (!response.ok) {
      throw new Error('刷新失败')
    }
    
    const data = await response.json()
    localStorage.setItem('token', data.access_token)
    return data.access_token
  } catch (error) {
    // 刷新失败，清除所有 token
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    return null
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}, retry = true): Promise<T> {
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

  // 处理 401 错误
  if (response.status === 401) {
    // 检查是否是认证接口
    const isAuthEndpoint = endpoint.includes('/auth/login') || 
                          endpoint.includes('/auth/register') ||
                          endpoint.includes('/auth/verify-login') ||
                          endpoint.includes('/auth/reset-password') ||
                          endpoint.includes('/auth/refresh')
    
    // 认证接口的 401 直接抛出错误
    if (isAuthEndpoint || !retry) {
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      window.location.href = '/login'
      throw new Error('登录已过期，请重新登录')
    }
    
    // 已经在刷新中，加入队列等待
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh((newToken) => {
          // 使用新 token 重试请求
          request<T>(endpoint, options, false)
            .then(resolve)
            .catch(reject)
        })
      })
    }
    
    // 尝试刷新 token
    isRefreshing = true
    
    try {
      const newToken = await tryRefreshToken()
      
      if (!newToken) {
        window.location.href = '/login'
        throw new Error('登录已过期，请重新登录')
      }
      
      // 通知队列中的请求
      onTokenRefreshed(newToken)
      
      // 使用新 token 重试原请求
      return request<T>(endpoint, options, false)
    } finally {
      isRefreshing = false
    }
  }

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }

  return response.json()
}

// 下载文件（处理 blob 和 token 刷新）
async function downloadFile(endpoint: string, filename: string): Promise<void> {
  const token = localStorage.getItem('token')
  
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  let response = await fetch(`${API_BASE_URL}${endpoint}`, { headers })
  
  // 处理 401，尝试刷新 token
  if (response.status === 401) {
    const isAuthEndpoint = endpoint.includes('/auth/')
    
    if (!isAuthEndpoint) {
      const newToken = await tryRefreshToken()
      
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`
        response = await fetch(`${API_BASE_URL}${endpoint}`, { headers })
      } else {
        window.location.href = '/login'
        throw new Error('登录已过期')
      }
    }
  }
  
  if (!response.ok) {
    throw new Error(`下载失败: ${response.status}`)
  }
  
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export { generationConfigApi } from './generationConfig'
export { aiModelsApi } from './aiModels'

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: 'GET' }),
  
  post: <T>(endpoint: string, data: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'POST', body: JSON.stringify(data) }),
  
  put: <T>(endpoint: string, data: unknown, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  
  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
  
  // 下载文件
  download: downloadFile
}

export default api
