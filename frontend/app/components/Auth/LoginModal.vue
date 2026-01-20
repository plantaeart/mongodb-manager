<template>
  <div class="login-overlay">
    <div class="login-modal">
      <div class="login-header">
        <h1 class="text-2xl font-bold text-gb-green mb-2">MongoDB Manager</h1>
        <p class="text-gb-fg-dim text-sm">Enter your password to continue</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="password" class="text-gb-fg text-sm mb-2 block">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter password"
            class="terminal-input w-full"
            :disabled="authStore.isLoading"
            autofocus
          />
        </div>

        <div class="form-group-checkbox">
          <label class="checkbox-label">
            <input
              type="checkbox"
              v-model="rememberMe"
              class="checkbox-input"
              :disabled="authStore.isLoading"
            />
            <span class="checkbox-text">Remember me</span>
          </label>
        </div>

        <button 
          type="submit" 
          class="terminal-button w-full"
          :disabled="authStore.isLoading || !password"
        >
          {{ authStore.isLoading ? 'Logging in...' : 'Login' }}
        </button>

        <div v-if="needsPasswordChange" class="warning-message">
          Default password detected. You must change your password.
        </div>
      </form>

      <div class="login-footer">
        <p class="text-gb-fg-dim text-xs">
          Default password: <code class="text-gb-yellow">admin</code>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()
const password = ref('')
const rememberMe = ref(false)
const needsPasswordChange = ref(false)

const emit = defineEmits<{
  needsPasswordChange: []
}>()

const handleLogin = async () => {
  needsPasswordChange.value = false

  try {
    const result = await authStore.login(password.value, rememberMe.value)
    
    if (result.success) {
      if (result.needsPasswordChange) {
        needsPasswordChange.value = true
        emit('needsPasswordChange')
      }
    }
  } catch (err) {
    // Error handling is done in the store with toast notifications
  }
}
</script>

<style scoped>
.login-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.login-modal {
  background: var(--gb-bg-hard);
  border: 2px solid var(--gb-gray);
  border-radius: 8px;
  padding: 2rem;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group-checkbox {
  display: flex;
  align-items: center;
  margin: -0.5rem 0 0.5rem 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--gb-green);
}

.checkbox-text {
  color: var(--gb-fg);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.checkbox-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.terminal-input {
  background: var(--gb-bg);
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  padding: 0.75rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  transition: border-color 0.2s;
}

.terminal-input:focus {
  outline: none;
  border-color: var(--gb-green);
}

.terminal-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.terminal-button {
  background: var(--gb-green);
  color: var(--gb-bg-hard);
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.terminal-button:hover:not(:disabled) {
  background: var(--gb-green-bright);
  transform: translateY(-1px);
}

.terminal-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  background: rgba(251, 73, 52, 0.1);
  border: 1px solid var(--gb-red);
  color: var(--gb-red);
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
}

.warning-message {
  background: rgba(250, 189, 47, 0.1);
  border: 1px solid var(--gb-yellow);
  color: var(--gb-yellow);
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid var(--gb-gray);
}

code {
  background: var(--gb-bg);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'JetBrains Mono', monospace;
}
</style>
