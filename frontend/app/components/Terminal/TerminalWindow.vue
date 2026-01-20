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
        <h1 class="terminal-title">MongoDB Manager</h1>
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
        <TerminalOutput />
        <CommandInput />
      </div>

      <!-- Visual panel (optional) -->
      <transition name="slide">
        <div v-if="showPanel" class="panel-section">
          <VisualPanel @close="togglePanel" />
        </div>
      </transition>
    </div>

    <!-- Status bar -->
    <StatusBar />
  </div>
</template>

<script setup lang="ts">
import TerminalOutput from './TerminalOutput.vue'
import CommandInput from './CommandInput.vue'
import StatusBar from './StatusBar.vue'
import VisualPanel from '../Panel/VisualPanel.vue'

const showPanel = ref(false)

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
