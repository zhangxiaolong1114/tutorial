<template>
  <header class="bg-white shadow-sm border-b border-gray-200">
    <div class="px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <h1 class="text-xl font-bold text-gray-900">{{ $t('app.name') }}</h1>
      </div>
      <div class="flex items-center space-x-4">
        <!-- 语言切换 -->
        <div class="relative">
          <button 
            @click="showLangMenu = !showLangMenu"
            class="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <span>{{ currentLangLabel }}</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div v-if="showLangMenu" class="absolute right-0 mt-2 w-32 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
            <button
              v-for="lang in languages"
              :key="lang.code"
              @click="switchLang(lang.code)"
              class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100"
              :class="{ 'text-blue-600 bg-blue-50': locale === lang.code }"
            >
              {{ lang.label }}
            </button>
          </div>
        </div>
        
        <span class="text-sm text-gray-600">{{ $t('nav.welcome') }}, 用户</span>
        <button 
          @click="logout"
          class="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
        >
          {{ $t('nav.logout') }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { locale } = useI18n()

const showLangMenu = ref(false)

const languages = [
  { code: 'zh', label: '中文' },
  { code: 'en', label: 'English' }
]

const currentLangLabel = computed(() => {
  return languages.find(l => l.code === locale.value)?.label || '中文'
})

const switchLang = (code: string) => {
  locale.value = code
  showLangMenu.value = false
  localStorage.setItem('locale', code)
}

const logout = () => {
  router.push('/login')
}

// 点击外部关闭菜单
const closeMenu = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.relative')) {
    showLangMenu.value = false
  }
}

if (typeof window !== 'undefined') {
  document.addEventListener('click', closeMenu)
}
</script>
