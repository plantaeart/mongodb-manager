<template>
  <div class="terminal-readonly-field">
    <label v-if="field.label" class="field-label">
      {{ field.label }}
    </label>
    
    <div class="readonly-content">
      <pre>{{ field.content }}</pre>
    </div>
    
    <span v-if="field.help_text" class="help-text">{{ field.help_text }}</span>
  </div>
</template>

<script setup lang="ts">
import type { FormField } from '~/types/terminal'

interface Props {
  field: FormField
  modelValue?: any
  disabled?: boolean
  readonly?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any]
  blur: []
  valid: []
  invalid: [error: string]
  enter: []
}>()

// Readonly fields are always valid
emit('valid')
</script>

<style scoped>
.terminal-readonly-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  color: var(--color-text-primary, #ebdbb2);
  font-size: 13px;
  font-weight: 500;
}

.readonly-content {
  background: var(--color-bg-tertiary, #282828);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 3px;
  padding: 12px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  color: var(--color-text-primary, #ebdbb2);
  overflow-x: auto;
}

.readonly-content pre {
  margin: 0;
  white-space: pre;
  font-size: 13px;
  line-height: 1.5;
  font-family: inherit;
}

.help-text {
  font-size: 12px;
  color: var(--color-text-tertiary, #928374);
  font-style: italic;
}
</style>
