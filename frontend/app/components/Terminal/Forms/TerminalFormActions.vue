<template>
  <div class="form-actions">
    <button
      v-for="action in actions"
      :key="action.action"
      :class="['action-button', `action-${action.style}`]"
      :disabled="isActionDisabled(action.action)"
      @click="handleAction(action.action)"
    >
      <span v-if="isSubmitting && action.action === 'submit'" class="loading-content">
        <span class="spinner"></span>
        {{ action.label }}...
      </span>
      <span v-else>{{ action.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { FormAction } from '~/types/terminal'

interface Props {
  actions: FormAction[]
  canSubmit: boolean
  isSubmitting: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  submit: [action: string]
  cancel: []
}>()

const isActionDisabled = (action: string): boolean => {
  if (action === 'submit') {
    return !props.canSubmit || props.isSubmitting
  }
  if (props.isSubmitting) {
    return true
  }
  return false
}

const handleAction = (action: string) => {
  if (action === 'cancel') {
    emit('cancel')
  } else {
    emit('submit', action)
  }
}
</script>

<style scoped>
.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-secondary, #504945);
  margin-top: 16px;
}

.action-button {
  padding: 8px 16px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  border: none;
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-primary {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
}

.action-primary:hover:not(:disabled) {
  background: var(--color-primary-hover, #8ec07c);
}

.action-secondary {
  background: transparent;
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
}

.action-secondary:hover:not(:disabled) {
  background: var(--color-bg-secondary, #3c3836);
}

.action-danger {
  background: var(--color-danger, #fb4934);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
}

.action-danger:hover:not(:disabled) {
  background: var(--color-danger-hover, #cc241d);
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
    justify-content: center;
  }
}
</style>
