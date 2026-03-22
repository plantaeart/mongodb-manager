<template>
  <div class="password-overlay">
    <div class="password-modal">
      <div class="password-header">
        <h2 class="text-xl font-bold text-gb-yellow mb-2">Change Password Required</h2>
        <p class="text-gb-fg-dim text-sm">You must change your password to continue</p>
      </div>

      <form @submit.prevent="handleChangePassword" class="password-form">
        <div class="form-group">
          <label for="oldPassword" class="text-gb-fg text-sm mb-2 block">Current Password</label>
          <input
            id="oldPassword"
            v-model="oldPassword"
            type="password"
            placeholder="Enter current password"
            class="terminal-input w-full"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="newPassword" class="text-gb-fg text-sm mb-2 block">New Password</label>
          <input
            id="newPassword"
            v-model="newPassword"
            type="password"
            placeholder="Enter new password (min 8 chars)"
            class="terminal-input w-full"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword" class="text-gb-fg text-sm mb-2 block">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Confirm new password"
            class="terminal-input w-full"
            :disabled="isLoading"
          />
        </div>

        <div v-if="validationError" class="error-message">
          {{ validationError }}
        </div>

        <div v-if="success" class="success-message">
          Password changed successfully! Logging in...
        </div>

        <div class="button-group">
          <button 
            type="submit" 
            class="terminal-button"
            :disabled="isLoading || !isFormValid"
          >
            {{ isLoading ? 'Changing...' : 'Change Password' }}
          </button>
        </div>
      </form>

      <div class="password-footer">
        <ul class="requirements-list">
          <li :class="{ valid: newPassword.length >= 8 }">
            Minimum 8 characters
          </li>
          <li :class="{ valid: newPassword === confirmPassword && newPassword.length > 0 }">
            Passwords match
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ToastColor, ToastDuration, PasswordChangeDelay } from '~/enums'
import type { PasswordChangeResult } from '~/types/auth'

interface Props {
  isLoading?: boolean
  showToasts?: boolean
  onChangePassword?: (oldPassword: string, newPassword: string) => Promise<PasswordChangeResult>
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  showToasts: true
})

const emit = defineEmits<{
  success: []
  cancel: []
  error: [error: string]
}>()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const validationError = ref('')
const success = ref(false)
const toast = useToast()

const isFormValid = computed(() => {
  return (
    oldPassword.value.length > 0 &&
    newPassword.value.length >= 8 &&
    newPassword.value === confirmPassword.value
  )
})

watch([newPassword, confirmPassword], () => {
  validationError.value = ''
  
  if (newPassword.value.length > 0 && newPassword.value.length < 8) {
    validationError.value = 'Password must be at least 8 characters'
  } else if (
    newPassword.value.length > 0 && 
    confirmPassword.value.length > 0 && 
    newPassword.value !== confirmPassword.value
  ) {
    validationError.value = 'Passwords do not match'
  }
})

const handleChangePassword = async () => {
  validationError.value = ''

  if (!props.onChangePassword) {
    return
  }

  try {
    const result = await props.onChangePassword(oldPassword.value, newPassword.value)
    
    if (result.success) {
      success.value = true
      
      if (props.showToasts) {
        toast.add({
          title: 'Password Changed',
          description: result.message || 'Your password has been updated successfully',
          color: ToastColor.SUCCESS,
          duration: ToastDuration.SHORT
        })
      }
      
      // Close modal after brief delay
      setTimeout(() => {
        emit('success')
      }, PasswordChangeDelay.SUCCESS_MS)
    } else {
      emit('error', result.error || 'Unable to change password')
      
      if (props.showToasts) {
        toast.add({
          title: 'Password Change Failed',
          description: result.error || 'Unable to change password',
          color: ToastColor.ERROR,
          duration: ToastDuration.MEDIUM
        })
      }
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'An unexpected error occurred'
    emit('error', errorMsg)
    
    if (props.showToasts) {
      toast.add({
        title: 'Error',
        description: errorMsg,
        color: ToastColor.ERROR,
        duration: ToastDuration.MEDIUM
      })
    }
  }
}
</script>

<style scoped>
.password-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.password-modal {
  background: var(--gb-bg-hard);
  border: 2px solid var(--gb-yellow);
  border-radius: 8px;
  padding: 2rem;
  width: 100%;
  max-width: 450px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}

.password-header {
  text-align: center;
  margin-bottom: 2rem;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Change password inputs use yellow focus to match the modal's yellow theme */
.terminal-input:focus {
  border-color: var(--gb-yellow);
}

/* Change password button uses yellow theme */
.terminal-button {
  background: var(--gb-yellow);
  color: var(--gb-bg-hard);
}

.terminal-button:hover:not(:disabled) {
  background: var(--gb-yellow-bright);
}

.button-group {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.success-message {
  background: rgba(184, 187, 38, 0.1);
  border: 1px solid var(--gb-green);
  color: var(--gb-green);
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
}

.password-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--gb-gray);
}

.requirements-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  color: var(--gb-fg-dim);
}

.requirements-list li {
  padding: 0.25rem 0;
  padding-left: 1.5rem;
  position: relative;
}

.requirements-list li::before {
  content: '✗';
  position: absolute;
  left: 0;
  color: var(--gb-red);
  font-weight: bold;
}

.requirements-list li.valid {
  color: var(--gb-green);
}

.requirements-list li.valid::before {
  content: '✓';
  color: var(--gb-green);
}
</style>
