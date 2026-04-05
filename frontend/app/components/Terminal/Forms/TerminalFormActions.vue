<template>
  <div class="form-actions">
    <BaseButton
      v-for="action in actions"
      :key="action.action"
      :variant="actionVariant(action.style)"
      :type="ButtonType.BUTTON"
      :disabled="isActionDisabled(action.action)"
      :loading="isSubmitting && action.action === 'submit'"
      @click="handleAction(action.action)"
    >
      {{ action.label }}
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import type { FormAction } from '~/types/terminal'
import { ButtonVariant, ButtonType } from '~/enums'

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

const actionVariant = (style: string): ButtonVariant => {
  if (style === 'primary') return ButtonVariant.PRIMARY
  if (style === 'danger') return ButtonVariant.DANGER
  return ButtonVariant.SECONDARY
}

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

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }

  .form-actions :deep(.base-btn) {
    width: 100%;
  }
}
</style>
