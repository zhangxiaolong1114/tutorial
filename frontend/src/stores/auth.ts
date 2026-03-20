import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User, type LoginRequest, type RegisterRequest, type VerifyLoginRequest } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)

  // Actions
  const login = async (credentials: LoginRequest & { verification_code?: string }): Promise<boolean | 'need_verification'> => {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.login(credentials)

      // 检查是否需要验证码
      if ('require_verification' in response && response.require_verification) {
        return 'need_verification'
      }

      // 正常登录成功
      if ('access_token' in response) {
        token.value = response.access_token
        refreshToken.value = response.refresh_token
        localStorage.setItem('token', response.access_token)
        localStorage.setItem('refreshToken', response.refresh_token)

        // 登录成功后获取用户信息
        await fetchUser()
        return true
      }

      return false
    } catch (err: any) {
      // 检查是否需要验证码 (403 错误)
      if (err.response?.status === 403) {
        const detail = err.response?.data?.detail
        if (detail && typeof detail === 'object' && detail.code === 'VERIFICATION_REQUIRED') {
          return 'need_verification'
        }
      }
      error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
      return false
    } finally {
      loading.value = false
    }
  }

  // 验证码登录（异常设备）
  const verifyLogin = async (data: VerifyLoginRequest): Promise<boolean> => {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.verifyLogin(data)
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('refreshToken', response.refresh_token)

      // 登录成功后获取用户信息
      await fetchUser()
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '验证码登录失败，请检查验证码'
      return false
    } finally {
      loading.value = false
    }
  }

  // 带验证码的密码登录（异常设备登录）
  const loginWithVerification = async (data: { email: string; password: string; verificationCode: string }): Promise<boolean> => {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.loginWithVerification(data)
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('refreshToken', response.refresh_token)

      // 登录成功后获取用户信息
      await fetchUser()
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '登录失败，请检查验证码'
      return false
    } finally {
      loading.value = false
    }
  }

  const register = async (data: RegisterRequest): Promise<boolean> => {
    loading.value = true
    error.value = null

    try {
      const response = await authApi.register(data)
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('refreshToken', response.refresh_token)

      // 注册成功后获取用户信息
      await fetchUser()
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '注册失败，请检查输入信息'
      return false
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    refreshToken.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  const fetchUser = async () => {
    if (!token.value) return false

    try {
      const userData = await authApi.getMe()
      user.value = userData
      return true
    } catch (err: any) {
      // 获取用户信息失败，可能是 token 无效
      if (err.response?.status === 401) {
        logout()
      }
      return false
    }
  }

  // 初始化时尝试获取用户信息
  const init = async () => {
    if (token.value) {
      await fetchUser()
    }
  }

  // 重置密码
  const resetPassword = async (data: { email: string; verificationCode: string; newPassword: string }): Promise<boolean> => {
    loading.value = true
    error.value = null

    try {
      await authApi.resetPassword(data)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '重置密码失败，请检查验证码'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    token,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    login,
    verifyLogin,
    loginWithVerification,
    register,
    resetPassword,
    logout,
    fetchUser,
    init
  }
})
