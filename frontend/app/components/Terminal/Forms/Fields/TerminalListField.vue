<template>
  <div class="terminal-list-field">
    <label v-if="field.label" class="field-label">
      {{ field.label }}
    </label>
    
    <div class="list-container">
      <div v-if="!field.items || field.items.length === 0" class="empty-message">
        No items to display
      </div>
      
      <div v-else class="list-items">
        <div 
          v-for="(item, index) in field.items" 
          :key="index" 
          class="list-item-panel"
        >
          <!-- Panel Header with Name -->
          <div class="panel-header">
            <span class="icon">📌</span>
            <span class="item-name">{{ item.name }}</span>
          </div>
          
          <!-- Panel Body with Details -->
          <div class="panel-body">
            <!-- URI -->
            <div v-if="item.uri" class="detail-row">
              <span class="detail-icon">🔗</span>
              <span class="detail-label">URI:</span>
              <span class="detail-value">{{ item.uri }}</span>
            </div>
            
            <!-- Description -->
            <div v-if="item.description" class="detail-row">
              <span class="detail-icon">📝</span>
              <span class="detail-label">Description:</span>
              <span class="detail-value">{{ item.description }}</span>
            </div>
            
            <!-- Added Date -->
            <div v-if="item.added_at" class="detail-row">
              <span class="detail-icon">📅</span>
              <span class="detail-label">Added:</span>
              <span class="detail-value">{{ formatDate(item.added_at) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Total Count -->
      <div v-if="field.items && field.items.length > 0" class="total-count">
        Total: {{ field.items.length }} connection(s)
      </div>
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

// Format date for display
const formatDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// List fields are always valid
emit('valid')
</script>

<style scoped>
.terminal-list-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  color: var(--color-text-primary, #ebdbb2);
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-message {
  padding: 16px;
  background: var(--color-bg-tertiary, #282828);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  color: var(--color-text-tertiary, #928374);
  font-size: 13px;
  text-align: center;
  font-style: italic;
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-item-panel {
  background: var(--color-bg-secondary, #282828);
  border: 1px solid var(--color-border-primary, #665c54);
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.2s;
}

.list-item-panel:hover {
  border-color: var(--color-primary, #83a598);
  box-shadow: 0 2px 8px rgba(131, 165, 152, 0.15);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-bg-tertiary, #3c3836);
  border-bottom: 1px solid var(--color-border-secondary, #504945);
}

.icon {
  font-size: 16px;
}

.item-name {
  color: var(--color-primary, #83a598);
  font-weight: 600;
  font-size: 14px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.panel-body {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.detail-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.detail-label {
  color: var(--color-text-secondary, #a89984);
  font-weight: 500;
  min-width: 90px;
  flex-shrink: 0;
}

.detail-value {
  color: var(--color-text-primary, #ebdbb2);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  word-break: break-all;
  flex: 1;
}

.total-count {
  padding: 8px 12px;
  background: var(--color-bg-tertiary, #282828);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  color: var(--color-text-secondary, #a89984);
  font-size: 12px;
  text-align: right;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.help-text {
  font-size: 12px;
  color: var(--color-text-tertiary, #928374);
  font-style: italic;
}

@media (max-width: 768px) {
  .panel-header {
    padding: 10px 12px;
  }
  
  .panel-body {
    padding: 10px 12px;
  }
  
  .detail-row {
    flex-direction: column;
    gap: 4px;
  }
  
  .detail-label {
    min-width: auto;
  }
}
</style>
