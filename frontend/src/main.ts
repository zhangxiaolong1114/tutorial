import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { useAuthStore } from './stores/auth'

async function initApp() {
  const app = createApp(App)

  app.use(createPinia())

  // 初始化 auth store（恢复登录状态）
  const authStore = useAuthStore()
  await authStore.init()

  app.use(router)
  app.use(i18n)

  app.mount('#app')
}

initApp()
