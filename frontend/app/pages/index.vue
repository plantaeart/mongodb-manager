<template>
  <div class="app-container">
    <!-- Session timeout warning -->
    <div v-if="authStore.hasSessionWarning" class="session-warning">
      <div class="warning-content">
        <span class="warning-icon">⚠️</span>
        <span class="warning-text">Your session will expire in 5 minutes. Please save your work.</span>
        <button @click="authStore.dismissSessionWarning" class="dismiss-button">Dismiss</button>
      </div>
    </div>

    <!-- Show terminal when authenticated -->
    <TerminalWindow v-if="authStore.isAuthenticated && !showPasswordChange" />

    <!-- Show password change modal when needed -->
    <ChangePasswordModal 
      v-if="showPasswordChange" 
      @success="handlePasswordChangeSuccess"
    />

    <!-- Show login modal when not authenticated -->
    <LoginModal 
      v-if="!authStore.isAuthenticated" 
      @needsPasswordChange="handleNeedsPasswordChange"
    />
  </div>
</template>

<script setup lang="ts">
import TerminalWindow from '~/components/Terminal/TerminalWindow.vue'
import LoginModal from '~/components/Auth/LoginModal.vue'
import ChangePasswordModal from '~/components/Auth/ChangePasswordModal.vue'

const authStore = useAuthStore()
const showPasswordChange = ref(false)

const handleNeedsPasswordChange = () => {
  showPasswordChange.value = true
}

const handlePasswordChangeSuccess = () => {
  showPasswordChange.value = false
}

// Load token from storage when app mounts
onMounted(() => {
  authStore.loadTokenFromStorage()
})
</script>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.session-warning {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
  background: linear-gradient(135deg, rgba(250, 189, 47, 0.95), rgba(214, 153, 8, 0.95));
  padding: 1rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
  }
  to {
    transform: translateY(0);
  }
}

.warning-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.warning-icon {
  font-size: 1.5rem;
}

.warning-text {
  color: var(--gb-bg-hard);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 14px;
  flex: 1;
}

.dismiss-button {
  background: var(--gb-bg-hard);
  color: var(--gb-yellow);
  border: 2px solid var(--gb-bg-hard);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.dismiss-button:hover {
  background: var(--gb-yellow);
  color: var(--gb-bg-hard);
  transform: translateY(-1px);
}
</style>
