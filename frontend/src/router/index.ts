import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'

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
      path: '/',
      component: Layout,
      redirect: '/generate',
      children: [
        {
          path: 'generate',
          name: 'generate',
          component: () => import('../views/GenerateView.vue')
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/DocumentsView.vue')
        },
        {
          path: 'document/:id',
          name: 'document-detail',
          component: () => import('../views/DocumentDetailView.vue')
        }
      ]
    }
  ]
})

export default router
