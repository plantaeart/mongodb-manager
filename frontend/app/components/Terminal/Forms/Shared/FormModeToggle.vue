<template>
  <div class="form-mode-toggle">
    <button 
      type="button"
      class="mode-button" 
      :class="{ 'active': !modelValue }"
      @click="emit('update:modelValue', false)"
      :disabled="disabled || readonly"
    >
      Simple
    </button>
    <button 
      type="button"
      class="mode-button" 
      :class="{ 'active': modelValue }"
      @click="emit('update:modelValue', true)"
      :disabled="disabled || readonly"
    >
      Advanced
    </button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean  // false = Simple, true = Advanced
  disabled?: boolean
  readonly?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<style scoped>
.form-mode-toggle {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.mode-button {
  padding: 8px 16px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
}

.mode-button:hover:not(:disabled) {
  background: var(--color-bg-secondary, #3c3836);
}

.mode-button.active {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
  border-color: var(--color-primary, #83a598);
}

.mode-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
