<template>
  <aside class="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-64px)]">
    <nav class="p-4 space-y-2">
      <router-link
        to="/generate"
        class="flex items-center px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
        :class="{ 'bg-blue-50 text-blue-600': $route.path === '/generate' }"
      >
        <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        {{ $t('nav.generate') }}
      </router-link>
      <router-link
        to="/documents"
        class="flex items-center px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
        :class="{ 'bg-blue-50 text-blue-600': $route.path === '/documents' }"
      >
        <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {{ $t('nav.documents') }}
      </router-link>
      <router-link
        to="/tasks"
        class="flex items-center px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
        :class="{ 'bg-blue-50 text-blue-600': $route.path === '/tasks' }"
      >
        <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        任务中心
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
</script>
