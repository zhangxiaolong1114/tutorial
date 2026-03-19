import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { getDeviceFingerprint } from '../utils/device'

const API_BASE_URL = 'http://localhost:8000'

// 创建 axios 实例
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 token 和设备指纹
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 添加设备指纹到请求头
    config.headers['X-Device-Fingerprint'] = getDeviceFingerprint()
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 错误处理：只在访问需要认证的接口时跳转登录页
    // 登录接口本身的 401（密码错误）不跳转
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || ''
      const isAuthEndpoint = requestUrl.includes('/auth/login') || 
                            requestUrl.includes('/auth/register') ||
                            requestUrl.includes('/auth/verify-login') ||
                            requestUrl.includes('/auth/reset-password')
      
      // 如果不是认证接口的 401，则清除 token 并跳转
      if (!isAuthEndpoint) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// 用户类型
export interface User {
  id: number
  username: string
  email: string
  created_at?: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 注册请求
export interface RegisterRequest {
  username: string
  email: string
  password: string
  verificationCode: string
}

// 验证码登录请求
export interface VerifyLoginRequest {
  email: string
  code: string
}

// 认证响应
export interface AuthResponse {
  access_token: string
  token_type: string
}

// 需要验证码错误响应
export interface VerificationRequiredResponse {
  require_verification: true
  message: string
}

// API 函数
export const authApi = {
  // 登录
  login: async (data: LoginRequest): Promise<AuthResponse | VerificationRequiredResponse> => {
    const params = new URLSearchParams()
    params.append('username', data.username)
    params.append('password', data.password)

    const response: AxiosResponse<AuthResponse | VerificationRequiredResponse> = await apiClient.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  },

  // 发送验证码
  sendVerificationCode: async (email: string, purpose: 'register' | 'login' = 'register'): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await apiClient.post('/auth/send-verification-code', {
      email,
      purpose
    })
    return response.data
  },

  // 验证码登录（验证码登录模式）
  verifyLogin: async (data: VerifyLoginRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/verify-login-code', {
      email: data.email,
      code: data.code
    })
    return response.data
  },

  // 带验证码的密码登录（异常设备登录）
  loginWithVerification: async (data: { email: string; password: string; verificationCode: string }): Promise<AuthResponse> => {
    const { getDeviceFingerprint } = await import('../utils/device')
    const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/verify-login', {
      email: data.email,
      password: data.password,
      verification_code: data.verificationCode,
      device_fingerprint: getDeviceFingerprint()
    })
    return response.data
  },

  // 注册
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/register', data)
    return response.data
  },

  // 获取当前用户信息
  getMe: async (): Promise<User> => {
    const response: AxiosResponse<User> = await apiClient.get('/auth/me')
    return response.data
  },

  // 重置密码
  resetPassword: async (data: { email: string; verificationCode: string; newPassword: string }): Promise<{ message: string }> => {
    const response: AxiosResponse<{ message: string }> = await apiClient.post('/auth/reset-password', {
      email: data.email,
      verification_code: data.verificationCode,
      new_password: data.newPassword
    })
    return response.data
  }
}
