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
        <h1 class="terminal-title">
          <img src="/logo/logo.png" alt="MongoDB Manager" class="terminal-logo" />
          MongoDB Manager <span class="version-badge">{{ versionString }}</span>
        </h1>
      </div>
    </div>

    <!-- Main content area -->
    <div class="terminal-content">
      <div class="terminal-section">
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
import { TerminalCommand } from '~/enums'
import TerminalOutput from './TerminalOutput.vue'
import CommandInput from './CommandInput.vue'
import StatusBar from './StatusBar.vue'

// Access services at orchestrator level
const { commandHistory, isExecuting, hasActiveForm, favorites, executeCommand } = useTerminal()
const { isConnected } = useWebSocket()
const { versionString } = useVersion()
const authStore = useAuthStore()

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

// Event handlers
const handleExecuteCommand = async (command: string) => {
  await executeCommand(command)
}

const handleLogout = async () => {
  await authStore.logout()
  window.location.reload()
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

.terminal-logo {
  width: 20px;
  height: 20px;
  object-fit: contain;
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
}
</style>
