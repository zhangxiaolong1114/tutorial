<template>
  <div class="min-h-screen flex flex-col">
    <Header />
    <div class="flex flex-1">
      <Sidebar />
      <main class="flex-1 p-6 overflow-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from './Header.vue'
import Sidebar from './Sidebar.vue'
</script>
