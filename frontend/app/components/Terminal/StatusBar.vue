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
        <span class="status-value">{{ username }}</span>
      </div>
    </div>

    <div class="status-right">
      <!-- Help hint -->
      <div class="status-item status-hint">
        <span class="text-gb-fg-dim">Type 'help' for commands</span>
      </div>

      <!-- Logout button -->
      <BaseButton
        :variant="ButtonVariant.OUTLINE"
        :type="ButtonType.BUTTON"
        :loading="isLoggingOut"
        :disabled="isLoggingOut"
        title="Logout"
        @click="handleLogout"
      >
        {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ConnectionStatus, ConnectionStatusClass, ButtonVariant, ButtonType } from '~/enums'

interface Props {
  isConnected?: boolean
  username?: string
  isLoggingOut?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isConnected: false,
  username: 'admin',
  isLoggingOut: false
})

const emit = defineEmits<{
  logout: []
}>()

const wsStatusClass = computed(() => {
  return props.isConnected ? ConnectionStatusClass.CONNECTED : ConnectionStatusClass.DISCONNECTED
})

const wsStatusText = computed(() => {
  return props.isConnected ? ConnectionStatus.CONNECTED : ConnectionStatus.DISCONNECTED
})

const handleLogout = () => {
  emit('logout')
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
</style>
