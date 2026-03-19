<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
      <h2 class="text-2xl font-bold text-center text-gray-900 mb-6">{{ $t('auth.register') }}</h2>

      <!-- 错误提示 -->
      <div v-if="authStore.error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-600">{{ authStore.error }}</p>
      </div>

      <!-- 密码不匹配提示 -->
      <div v-if="passwordMismatch" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-600">{{ $t('auth.passwordMismatch') }}</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.username') }}</label>
          <input
            v-model="username"
            type="text"
            required
            autocomplete="off"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.usernamePlaceholder')"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.email') }}</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="off"
            :disabled="verificationSent"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            :placeholder="$t('auth.emailPlaceholder')"
          />
        </div>

        <!-- 验证码输入 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.verificationCode') }}</label>
          <VerificationCodeInput
            v-model="verificationCode"
            :email="email"
            purpose="register"
            :disabled="!email || authStore.loading"
            @send-code="handleSendCode"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.password') }}</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="6"
            autocomplete="new-password"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.passwordPlaceholder')"
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
        <button
          type="submit"
          :disabled="authStore.loading || !verificationCode"
          class="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="authStore.loading">{{ $t('auth.registering') }}</span>
          <span v-else>{{ $t('auth.registerButton') }}</span>
        </button>
      </form>
      <p class="mt-4 text-center text-sm text-gray-600">
        {{ $t('auth.hasAccount') }}
        <router-link to="/login" class="text-blue-600 hover:underline">{{ $t('auth.goLogin') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/auth'
import VerificationCodeInput from '../components/VerificationCodeInput.vue'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const verificationCode = ref('')
const verificationSent = ref(false)
const verificationInputRef = ref<InstanceType<typeof VerificationCodeInput> | null>(null)

const passwordMismatch = computed(() => {
  return confirmPassword.value && password.value !== confirmPassword.value
})

const handleSendCode = async () => {
  try {
    await authApi.sendVerificationCode(email.value, 'register')
    verificationSent.value = true
    authStore.error = null
  } catch (err: any) {
    authStore.error = err.response?.data?.detail || '发送验证码失败，请稍后重试'
    throw err
  }
}

const handleRegister = async () => {
  // 验证密码是否匹配
  if (password.value !== confirmPassword.value) {
    return
  }

  // 验证验证码
  if (!verificationCode.value) {
    authStore.error = '请输入验证码'
    return
  }

  const success = await authStore.register({
    username: username.value,
    email: email.value,
    password: password.value,
    verificationCode: verificationCode.value
  })

  if (success) {
    // 注册成功，跳转到首页
    router.push('/generate')
  }
}

// 清除之前的错误信息
onMounted(() => {
  authStore.error = null
})

// 清理定时器
onUnmounted(() => {
  verificationInputRef.value?.cleanup()
})
</script>
