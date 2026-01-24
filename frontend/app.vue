<template>
  <div id="app">
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
// Global styles are imported via nuxt.config.ts

// Set dynamic page title based on connection status
const { isConnected } = useWebSocket()
const authStore = useAuthStore()

// Update page title dynamically
useHead({
  title: computed(() => {
    if (!authStore.isAuthenticated) {
      return 'MongoDB Manager - Login'
    }
    if (!isConnected.value) {
      return 'MongoDB Manager - Connecting...'
    }
    return 'MongoDB Manager'
  }),
  titleTemplate: '%s'
})
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

#app {
  height: 100vh;
  width: 100vw;
}
</style>
