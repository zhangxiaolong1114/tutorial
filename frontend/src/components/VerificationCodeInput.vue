<template>
  <div class="flex gap-2">
    <div class="flex-1">
      <input
        v-model="code"
        type="text"
        maxlength="6"
        required
        :disabled="disabled"
        class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center tracking-widest font-mono"
        :placeholder="$t('auth.verificationCodePlaceholder')"
        @input="handleInput"
      />
    </div>
    <button
      type="button"
      :disabled="isSending || countdown > 0 || disabled"
      class="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
      @click="handleSendCode"
    >
      <span v-if="countdown > 0">{{ countdown }}s</span>
      <span v-else-if="isSending">{{ $t('auth.sending') }}</span>
      <span v-else-if="hasSent">{{ $t('auth.resendCode') }}</span>
      <span v-else>{{ $t('auth.sendCode') }}</span>
    </button>
  </div>
  <p v-if="error" class="mt-1 text-sm text-red-600">{{ error }}</p>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  email: string
  purpose: 'register' | 'login' | 'reset'
  disabled?: boolean
  modelValue: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'send-code'): void
}>()

const code = ref(props.modelValue)
const countdown = ref(0)
const isSending = ref(false)
const hasSent = ref(false)
const error = ref('')

let countdownTimer: ReturnType<typeof setInterval> | null = null

// 同步外部 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  code.value = newVal
})

// 同步内部 code 变化到外部
watch(code, (newVal) => {
  emit('update:modelValue', newVal)
})

const handleInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  // 只允许数字
  code.value = target.value.replace(/\D/g, '').slice(0, 6)
  emit('update:modelValue', code.value)
}

const handleSendCode = async () => {
  // 验证邮箱格式
  if (!props.email) {
    error.value = t('auth.emailRequired')
    return
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(props.email)) {
    error.value = t('auth.emailInvalid')
    return
  }

  error.value = ''
  isSending.value = true

  try {
    emit('send-code')
    hasSent.value = true
    startCountdown()
  } finally {
    isSending.value = false
  }
}

const startCountdown = () => {
  countdown.value = 60
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      if (countdownTimer) {
        clearInterval(countdownTimer)
      }
    }
  }, 1000)
}

// 组件卸载时清理定时器
const cleanup = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
}

defineExpose({
  cleanup,
  startCountdown
})
</script>
