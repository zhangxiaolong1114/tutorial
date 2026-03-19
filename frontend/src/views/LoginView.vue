<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
      <h2 class="text-2xl font-bold text-center text-gray-900 mb-6">{{ $t('auth.login') }}</h2>
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.email') }}</label>
          <input
            v-model="email"
            type="email"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.emailPlaceholder')"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('auth.password') }}</label>
          <input
            v-model="password"
            type="password"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :placeholder="$t('auth.passwordPlaceholder')"
          />
        </div>
        <button
          type="submit"
          class="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          {{ $t('auth.loginButton') }}
        </button>
      </form>
      <p class="mt-4 text-center text-sm text-gray-600">
        {{ $t('auth.noAccount') }}
        <router-link to="/register" class="text-blue-600 hover:underline">{{ $t('auth.goRegister') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')

const handleLogin = () => {
  router.push('/generate')
}
</script>
