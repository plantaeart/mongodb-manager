<template>
  <div class="status-bar">
    <div class="status-left">
      <!-- Connection status -->
      <div class="status-item">
        <span class="status-icon" :class="wsStatusClass">●</span>
        <span class="status-text">{{ wsStatusText }}</span>
      </div>

      <!-- Current user -->
      <div class="status-item">
        <span class="status-label">User:</span>
        <span class="status-value">{{ authStore.getUsername }}</span>
      </div>
    </div>

    <div class="status-right">
      <!-- Help hint -->
      <div class="status-item status-hint">
        <span class="text-gb-fg-dim">Type 'help' for commands</span>
      </div>

      <!-- Logout button -->
      <button @click="handleLogout" class="logout-button" title="Logout">
        <span>Logout</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()
const { isConnected } = useWebSocket()

const wsStatusClass = computed(() => {
  return isConnected.value ? 'status-connected' : 'status-disconnected'
})

const wsStatusText = computed(() => {
  return isConnected.value ? 'Connected' : 'Disconnected'
})

const handleLogout = async () => {
  await authStore.logout()
  // Reload page to reset state
  window.location.reload()
}
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: var(--gb-bg);
  border-top: 1px solid var(--gb-gray);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--gb-fg);
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-icon {
  font-size: 8px;
}

.status-icon.status-connected {
  color: var(--gb-green);
  animation: pulse 2s infinite;
}

.status-icon.status-disconnected {
  color: var(--gb-red);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-label {
  color: var(--gb-fg-dim);
}

.status-value {
  color: var(--gb-fg);
  font-weight: 500;
}

.status-text {
  color: var(--gb-fg);
}

.status-hint {
  color: var(--gb-fg-dim);
  font-style: italic;
}

.logout-button {
  background: transparent;
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  background: var(--gb-red);
  border-color: var(--gb-red);
  color: var(--gb-bg-hard);
}
</style>
