<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
      <h2 class="text-2xl font-bold text-center text-gray-900 mb-6">{{ $t('auth.login') }}</h2>

      <!-- 错误提示 -->
      <div v-if="authStore.error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start justify-between">
        <p class="text-sm text-red-600">{{ authStore.error }}</p>
        <button 
          @click="authStore.error = null"
          class="text-red-400 hover:text-red-600 ml-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.email') }}</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="off"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.emailPlaceholder')"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.password') }}</label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="new-password"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.passwordPlaceholder')"
          />
        </div>

        <!-- 需要验证码时显示 -->
        <div v-if="requireVerification">
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.verificationCode') }}</label>
          <VerificationCodeInput
            v-model="verificationCode"
            :email="email"
            purpose="login"
            :disabled="authStore.loading"
            @send-code="handleSendVerificationCode"
          />
        </div>

        <button
          type="submit"
          :disabled="authStore.loading"
          class="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="authStore.loading">{{ $t('auth.loggingIn') }}</span>
          <span v-else>{{ $t('auth.loginButton') }}</span>
        </button>
      </form>

      <!-- 忘记密码链接 -->
      <div class="mt-4 text-center">
        <router-link to="/forgot-password" class="text-sm text-blue-600 hover:underline">
          {{ $t('auth.forgotPassword') }}
        </router-link>
      </div>

      <p class="mt-4 text-center text-sm text-gray-600">
        {{ $t('auth.noAccount') }}
        <router-link to="/register" class="text-blue-600 hover:underline">{{ $t('auth.goRegister') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/auth'
import VerificationCodeInput from '../components/VerificationCodeInput.vue'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const verificationCode = ref('')
const requireVerification = ref(false)

const handleSendVerificationCode = async () => {
  try {
    if (!email.value) {
      authStore.error = '请输入邮箱地址'
      return
    }
    await authApi.sendVerificationCode(email.value, 'login')
    authStore.error = null
  } catch (err: any) {
    authStore.error = err.response?.data?.detail || '发送验证码失败，请稍后重试'
    throw err
  }
}

const handleLogin = async () => {
  if (!email.value || !password.value) {
    authStore.error = '请输入邮箱和密码'
    return
  }

  // 如果需要验证码
  if (requireVerification.value) {
    if (!verificationCode.value) {
      authStore.error = '请输入验证码'
      return
    }

    const success = await authStore.loginWithVerification({
      email: email.value,
      password: password.value,
      verificationCode: verificationCode.value
    })

    if (success) {
      router.push('/generate')
    }
    return
  }

  // 普通密码登录
  const result = await authStore.login({
    username: email.value,
    password: password.value
  })

  if (result === 'need_verification') {
    requireVerification.value = true
    authStore.error = '检测到新设备登录，验证码已发送至您的邮箱'
    // 自动发送验证码
    try {
      await authApi.sendVerificationCode(email.value, 'login')
    } catch (err: any) {
      console.error('自动发送验证码失败:', err)
    }
  } else if (result === true) {
    router.push('/generate')
  }
}

// 组件挂载时不清除错误，保留之前的错误信息
// 只在页面初始化时清除一次
let isFirstMount = true
onMounted(() => {
  if (isFirstMount) {
    authStore.error = null
    isFirstMount = false
  }
})
</script>
