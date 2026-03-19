<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
      <h2 class="text-2xl font-bold text-center text-gray-900 mb-6">{{ $t('auth.resetPassword') }}</h2>

      <!-- 错误提示 -->
      <div v-if="authStore.error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-600">{{ authStore.error }}</p>
      </div>

      <!-- 成功提示 -->
      <div v-if="resetSuccess" class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
        <p class="text-sm text-green-600">{{ $t('auth.resetSuccess') }}</p>
      </div>

      <form v-if="!resetSuccess" @submit.prevent="handleResetPassword" class="space-y-4">
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

        <!-- 验证码 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.verificationCode') }}</label>
          <VerificationCodeInput
            v-model="verificationCode"
            :email="email"
            purpose="reset"
            :disabled="authStore.loading"
            @send-code="handleSendCode"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.newPassword') }}</label>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="6"
            autocomplete="new-password"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.newPasswordPlaceholder')"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.confirmPassword') }}</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            autocomplete="new-password"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.confirmPasswordPlaceholder')"
          />
        </div>

        <!-- 密码不匹配提示 -->
        <div v-if="passwordMismatch" class="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-sm text-red-600">{{ $t('auth.passwordMismatch') }}</p>
        </div>

        <button
          type="submit"
          :disabled="authStore.loading || !!passwordMismatch"
          class="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="authStore.loading">{{ $t('auth.resetting') }}</span>
          <span v-else>{{ $t('auth.resetPasswordButton') }}</span>
        </button>
      </form>

      <div class="mt-6 text-center space-y-2">
        <router-link v-if="resetSuccess" to="/login" class="text-blue-600 hover:underline">
          {{ $t('auth.goLogin') }}
        </router-link>
        <router-link v-else to="/login" class="text-sm text-gray-600 hover:text-gray-900">
          ← {{ $t('auth.backToLogin') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/auth'
import VerificationCodeInput from '../components/VerificationCodeInput.vue'

const authStore = useAuthStore()

const email = ref('')
const verificationCode = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const resetSuccess = ref(false)

const passwordMismatch = computed(() => {
  return confirmPassword.value && newPassword.value !== confirmPassword.value
})

const handleSendCode = async () => {
  try {
    if (!email.value) {
      authStore.error = '请输入邮箱地址'
      return
    }
    await authApi.sendVerificationCode(email.value, 'reset' as any)
    authStore.error = null
  } catch (err: any) {
    authStore.error = err.response?.data?.detail || '发送验证码失败，请稍后重试'
    throw err
  }
}

const handleResetPassword = async () => {
  if (!email.value || !verificationCode.value || !newPassword.value) {
    authStore.error = '请填写所有字段'
    return
  }

  if (passwordMismatch.value) {
    authStore.error = '两次输入的密码不一致'
    return
  }

  const success = await authStore.resetPassword({
    email: email.value,
    verificationCode: verificationCode.value,
    newPassword: newPassword.value
  })

  if (success) {
    resetSuccess.value = true
  }
}

// 清除之前的错误信息
onMounted(() => {
  authStore.error = null
})
</script>
