<template>
  <div class="visual-panel">
    <!-- Panel header -->
    <div class="panel-header">
      <h2 class="panel-title">Quick Actions</h2>
      <button @click="emit('close')" class="close-button" title="Close panel">✕</button>
    </div>

    <!-- Panel sections -->
    <div class="panel-content">
      <!-- Favorites section -->
      <div class="panel-section">
        <h3 class="section-title">
          <span class="section-icon">★</span>
          Favorite Commands
        </h3>
        <div class="section-content">
          <div v-if="favorites.length === 0" class="empty-state">
            <p class="text-gb-fg-dim">No favorites yet</p>
            <p class="text-gb-fg-dim text-xs">Commands you favorite will appear here</p>
          </div>
          <div v-else class="favorite-list">
            <button
              v-for="(favorite, index) in favorites"
              :key="index"
              @click="runCommand(favorite)"
              class="favorite-item"
            >
              <span class="favorite-command">{{ favorite }}</span>
              <span class="favorite-icon">→</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Quick commands section -->
      <div class="panel-section">
        <h3 class="section-title">
          <span class="section-icon">⚡</span>
          Quick Commands
        </h3>
        <div class="section-content">
          <div class="quick-commands-grid">
            <button
              v-for="cmd in quickCommands"
              :key="cmd.command"
              @click="runCommand(cmd.command)"
              class="quick-command-button"
              :class="`color-${cmd.color}`"
            >
              <span class="command-icon">{{ cmd.icon }}</span>
              <span class="command-label">{{ cmd.label }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Help section -->
      <div class="panel-section">
        <h3 class="section-title">
          <span class="section-icon">?</span>
          Common Commands
        </h3>
        <div class="section-content">
          <div class="help-list">
            <div v-for="item in commonCommands" :key="item.command" class="help-item">
              <code class="help-command">{{ item.command }}</code>
              <p class="help-description">{{ item.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TerminalCommand, ButtonColor } from '~/enums'

interface QuickCommand {
  command: string
  label: string
  icon: string
  color: ButtonColor
}

interface CommonCommand {
  command: string
  description: string
}

interface Props {
  favorites?: string[]
  quickCommands?: QuickCommand[]
  commonCommands?: CommonCommand[]
}

const props = withDefaults(defineProps<Props>(), {
  favorites: () => [],
  quickCommands: () => [
    { command: TerminalCommand.CONNECT_LIST, label: 'Connections', icon: '🔗', color: ButtonColor.GREEN },
    { command: TerminalCommand.BACKUP_LIST, label: 'Backups', icon: '💾', color: ButtonColor.BLUE },
    { command: TerminalCommand.HELP, label: 'Help', icon: '❓', color: ButtonColor.YELLOW }
  ],
  commonCommands: () => [
    { command: TerminalCommand.CONNECT_LIST, description: 'List all MongoDB connections' },
    { command: TerminalCommand.CONNECT_ADD, description: 'Add a new connection' },
    { command: TerminalCommand.BACKUP_CREATE, description: 'Create a backup' },
    { command: TerminalCommand.BACKUP_LIST, description: 'List all backups' },
    { command: TerminalCommand.CLEAR, description: 'Clear terminal output' }
  ]
})

const emit = defineEmits<{
  executeCommand: [command: string]
  close: []
}>()

const runCommand = (command: string) => {
  emit('executeCommand', command)
}
</script>

<style scoped>
.visual-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: 'JetBrains Mono', monospace;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--gb-gray);
  background: var(--gb-bg-soft);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gb-aqua);
  margin: 0;
}

.close-button {
  background: transparent;
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s;
}

.close-button:hover {
  background: var(--gb-red);
  border-color: var(--gb-red);
  color: var(--gb-bg);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.panel-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gb-fg);
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-icon {
  color: var(--gb-yellow);
}

.section-content {
  padding-left: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
}

/* Favorites */
.favorite-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.favorite-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--gb-bg-hard);
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  padding: 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.favorite-item:hover {
  background: var(--gb-bg-soft);
  border-color: var(--gb-yellow);
  transform: translateX(4px);
}

.favorite-command {
  color: var(--gb-yellow);
  font-size: 13px;
}

.favorite-icon {
  color: var(--gb-fg-dim);
}

/* Quick commands */
.quick-commands-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.quick-command-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--gb-bg-hard);
  border: 2px solid var(--gb-gray);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--gb-fg);
}

.quick-command-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.quick-command-button.color-green:hover {
  border-color: var(--gb-green);
  background: rgba(184, 187, 38, 0.1);
}

.quick-command-button.color-blue:hover {
  border-color: var(--gb-blue);
  background: rgba(131, 165, 152, 0.1);
}

.quick-command-button.color-purple:hover {
  border-color: var(--gb-purple);
  background: rgba(211, 134, 155, 0.1);
}

.quick-command-button.color-yellow:hover {
  border-color: var(--gb-yellow);
  background: rgba(250, 189, 47, 0.1);
}

.command-icon {
  font-size: 24px;
}

.command-label {
  font-size: 12px;
  font-weight: 500;
}

/* Help */
.help-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.help-item {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--gb-gray);
}

.help-item:last-child {
  border-bottom: none;
}

.help-command {
  display: inline-block;
  background: var(--gb-bg-hard);
  color: var(--gb-yellow);
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 12px;
  margin-bottom: 0.5rem;
}

.help-description {
  font-size: 12px;
  color: var(--gb-fg-dim);
  margin: 0;
}
</style>
