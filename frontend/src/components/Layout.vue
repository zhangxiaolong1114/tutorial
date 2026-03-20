<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <Header />
    <div class="flex flex-1 overflow-hidden">
      <Sidebar />
      <main class="flex-1 p-6 overflow-y-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'
</script>
