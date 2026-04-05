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
          <!-- Panel Header with Primary Field -->
          <div class="panel-header">
            <span class="icon">{{ getHeaderIcon(item) }}</span>
            <span class="item-name">{{ getPrimaryFieldValue(item) }}</span>
          </div>
          
          <!-- Panel Body with Details -->
          <div class="panel-body">
            <div 
              v-for="fieldConfig in getDetailFields()" 
              :key="fieldConfig.key" 
              class="detail-row"
            >
              <template v-if="hasValue(item, fieldConfig.key)">
                <span v-if="fieldConfig.icon" class="detail-icon">{{ fieldConfig.icon }}</span>
                <span class="detail-label">{{ fieldConfig.label }}:</span>
                
                <!-- Render based on field type -->
                <template v-if="fieldConfig.type === 'list'">
                  <div class="detail-value">
                    <div 
                      v-for="(listItem, listIndex) in item[fieldConfig.key]" 
                      :key="listIndex" 
                      class="path-item"
                    >
                      <span class="path-indicator">•</span>
                      <span>{{ stripBackupSuffix(listItem) }}</span>
                    </div>
                  </div>
                </template>
                
                <template v-else-if="fieldConfig.type === 'date'">
                  <span class="detail-value">{{ formatDate(item[fieldConfig.key]) }}</span>
                </template>
                
                <template v-else>
                  <span class="detail-value">{{ stripBackupSuffix(item[fieldConfig.key]) }}</span>
                </template>
              </template>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Total Count -->
      <div v-if="field.items && field.items.length > 0" class="total-count">
        Total: {{ field.items.length }} {{ getCountLabel() }}
      </div>
    </div>
    
    <span v-if="field.help_text" class="help-text">{{ field.help_text }}</span>
  </div>
</template>

<script setup lang="ts">
import type { FormField, ListItemField } from '~/types/terminal'
import { stripBackupSuffix } from '~/utils/backupHelpers'

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

// Get header icon (from config or default)
const getHeaderIcon = (item: any): string => {
  if (props.field.list_config?.header_icon) {
    return props.field.list_config.header_icon
  }
  
  // Fallback icons based on item type
  if (item.connection_name) return '📁'
  if (item.name) return '📌'
  return '📄'
}

// Get primary field value (the main identifier shown in header)
const getPrimaryFieldValue = (item: any): string => {
  if (!props.field.list_config) {
    // Fallback: try common primary fields
    return item.connection_name || item.name || item.id || 'Unknown'
  }
  
  const primaryField = props.field.list_config.fields.find(f => f.primary)
  if (primaryField && item[primaryField.key]) {
    return item[primaryField.key]
  }
  
  // Fallback to first field
  const firstField = props.field.list_config.fields[0]
  return firstField ? item[firstField.key] : 'Unknown'
}

// Get detail fields (non-primary fields)
const getDetailFields = (): ListItemField[] => {
  if (!props.field.list_config) {
    return []
  }
  
  return props.field.list_config.fields.filter(f => !f.primary)
}

// Check if item has a value for a given key
const hasValue = (item: any, key: string): boolean => {
  const value = item[key]
  if (value === null || value === undefined) return false
  if (typeof value === 'string' && value.trim() === '') return false
  if (Array.isArray(value) && value.length === 0) return false
  return true
}

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

// Get count label from config or default
const getCountLabel = () => {
  return props.field.list_config?.count_label || 'item(s)'
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

.path-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
}

.path-indicator {
  color: var(--color-success, #b8bb26);
  font-weight: bold;
  width: 16px;
  flex-shrink: 0;
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
