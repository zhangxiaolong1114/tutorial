import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { public: true }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPasswordView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      component: Layout,
      redirect: '/generate',
      children: [
        {
          path: 'generate',
          name: 'generate',
          component: () => import('../views/GenerateView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'outline/:id/edit',
          name: 'outline-edit',
          component: () => import('../views/OutlineEditView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/DocumentsView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'document/:id',
          name: 'document-detail',
          component: () => import('../views/DocumentDetailView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'tasks',
          name: 'tasks',
          component: () => import('../views/TasksView.vue'),
          meta: { requiresAuth: true }
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated

  // 已登录用户访问登录/注册页，跳转到首页
  if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/generate')
    return
  }

  // 需要登录的页面，未登录则跳转登录页
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
    return
  }

  next()
})

export default router
