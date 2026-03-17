<template>
  <div class="terminal-window">
    <!-- Header -->
    <div class="terminal-header">
      <div class="header-left">
        <div class="window-controls">
          <span class="control close"></span>
          <span class="control minimize"></span>
          <span class="control maximize"></span>
        </div>
        <h1 class="terminal-title">MongoDB Manager <span class="version-badge">{{ versionString }}</span></h1>
      </div>
      <div class="header-right">
        <button 
          @click="togglePanel" 
          class="panel-toggle-button"
          :class="{ active: showPanel }"
        >
          {{ showPanel ? 'Hide Panel' : 'Show Panel' }}
        </button>
      </div>
    </div>

    <!-- Main content area -->
    <div class="terminal-content">
      <!-- Terminal section -->
      <div class="terminal-section" :class="{ 'with-panel': showPanel }">
        <TerminalOutput 
          :history="terminalHistory"
          :auto-scroll="true"
        />
        <CommandInput 
          :is-executing="isExecuting"
          :has-active-form="hasActiveForm"
          :favorites="favorites"
          :suggestions="availableCommands"
          @execute-command="handleExecuteCommand"
        />
      </div>

      <!-- Visual panel (optional) -->
      <transition name="slide">
        <div v-if="showPanel" class="panel-section">
          <VisualPanel 
            :favorites="favorites"
            :quick-commands="quickCommands"
            :common-commands="commonCommands"
            @execute-command="handleExecuteCommand"
            @close="togglePanel"
          />
        </div>
      </transition>
    </div>

    <!-- Status bar -->
    <StatusBar 
      :is-connected="wsConnected"
      :username="currentUser"
      @logout="handleLogout"
    />
  </div>
</template>

<script setup lang="ts">
import { TerminalCommand, ButtonColor } from '~/enums'
import TerminalOutput from './TerminalOutput.vue'
import CommandInput from './CommandInput.vue'
import StatusBar from './StatusBar.vue'
import VisualPanel from '../Panel/VisualPanel.vue'

// Access services at orchestrator level
const { commandHistory, isExecuting, hasActiveForm, favorites, executeCommand } = useTerminal()
const { isConnected } = useWebSocket()
const { versionString } = useVersion()
const authStore = useAuthStore()

const showPanel = ref(false)

// Computed values to pass as props
const wsConnected = computed(() => isConnected.value)
const currentUser = computed(() => authStore.getUsername)
// Deep copy to remove readonly constraints from nested arrays
const terminalHistory = computed(() => 
  commandHistory.value.map(entry => {
    const newEntry: any = {
      ...entry,
      output: [...entry.output]
    }
    
    // Deep copy form to remove readonly constraints
    if (entry.form) {
      newEntry.form = {
        ...entry.form,
        fields: [...entry.form.fields],
        actions: [...entry.form.actions]
      }
    }
    
    return newEntry
  })
)

// Available commands for autocomplete
const availableCommands = Object.values(TerminalCommand)

// Quick commands configuration
const quickCommands = [
  { command: TerminalCommand.CONNECT_LIST, label: 'Connections', icon: '🔗', color: ButtonColor.GREEN },
  { command: TerminalCommand.BACKUP_LIST, label: 'Backups', icon: '💾', color: ButtonColor.BLUE },
  { command: TerminalCommand.HELP, label: 'Help', icon: '❓', color: ButtonColor.YELLOW }
]

// Common commands reference
const commonCommands = [
  { command: TerminalCommand.CONNECT_LIST, description: 'List all MongoDB connections' },
  { command: TerminalCommand.CONNECT_ADD, description: 'Add a new connection' },
  { command: TerminalCommand.BACKUP_CREATE, description: 'Create a backup' },
  { command: TerminalCommand.BACKUP_LIST, description: 'List all backups' },
  { command: TerminalCommand.CLEAR, description: 'Clear terminal output' }
]

// Event handlers
const handleExecuteCommand = async (command: string) => {
  await executeCommand(command)
}

const handleLogout = async () => {
  await authStore.logout()
  window.location.reload()
}

const togglePanel = () => {
  showPanel.value = !showPanel.value
}
</script>

<style scoped>
.terminal-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--gb-bg-hard);
  color: var(--gb-fg);
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--gb-bg);
  border-bottom: 2px solid var(--gb-gray);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.window-controls {
  display: flex;
  gap: 0.5rem;
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: opacity 0.2s;
}

.control:hover {
  opacity: 0.8;
}

.control.close {
  background: var(--gb-red);
}

.control.minimize {
  background: var(--gb-yellow);
}

.control.maximize {
  background: var(--gb-green);
}

.terminal-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gb-fg);
  font-family: 'JetBrains Mono', monospace;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.version-badge {
  font-size: 10px;
  font-weight: 500;
  color: var(--gb-fg-dim);
  background: var(--gb-bg-hard);
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  border: 1px solid var(--gb-gray);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.panel-toggle-button {
  background: transparent;
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.panel-toggle-button:hover {
  background: var(--gb-bg-soft);
  border-color: var(--gb-aqua);
}

.panel-toggle-button.active {
  background: var(--gb-aqua);
  border-color: var(--gb-aqua);
  color: var(--gb-bg-hard);
  font-weight: 600;
}

.terminal-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.terminal-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: flex 0.3s ease;
}

.terminal-section.with-panel {
  flex: 0 0 65%;
}

.panel-section {
  flex: 0 0 35%;
  border-left: 2px solid var(--gb-gray);
  background: var(--gb-bg);
  overflow-y: auto;
}

/* Slide transition for panel */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
