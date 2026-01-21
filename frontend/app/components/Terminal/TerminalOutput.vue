<template>
  <div ref="outputContainer" class="terminal-output">
    <div v-if="history.length === 0" class="welcome-message">
      <p class="text-gb-green">Welcome to MongoDB Manager</p>
      <p class="text-gb-fg-dim">Type 'help' to see available commands</p>
    </div>

    <div
      v-for="entry in history"
      :key="entry.id"
      class="terminal-entry"
      :class="{ 'entry-error': entry.status === CommandStatus.ERROR }"
    >
      <!-- Command prompt -->
      <div class="command-line">
        <span class="prompt-user">admin</span>
        <span class="prompt-separator">@</span>
        <span class="prompt-host">mongodb-manager</span>
        <span class="prompt-path">~</span>
        <span class="prompt-symbol">$</span>
        <span class="command-text">{{ entry.command }}</span>
      </div>

      <!-- Output lines -->
      <div v-if="entry.output.length > 0" class="output-lines">
        <div
          v-for="(line, index) in entry.output"
          :key="index"
          class="output-line"
          :class="{
            'text-gb-green': isSuccessLine(line),
            'text-gb-red': isErrorLine(line),
            'text-gb-yellow': isWarningLine(line),
            'text-gb-blue': isInfoLine(line)
          }"
        >
          {{ line }}
        </div>
      </div>

      <!-- Status indicator -->
      <div v-if="entry.status === CommandStatus.RUNNING" class="status-indicator">
        <span class="spinner"></span>
        <span class="text-gb-blue">Running...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CommandStatus, OutputLinePattern } from '~/enums'
import type { TerminalEntry } from '~/types/terminal'

interface Props {
  history: TerminalEntry[]
  autoScroll?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoScroll: true
})

const outputContainer = ref<HTMLElement | null>(null)

// Auto-scroll to bottom when new output arrives
watch(
  () => props.history,
  () => {
    if (props.autoScroll) {
      nextTick(() => {
        if (outputContainer.value) {
          outputContainer.value.scrollTop = outputContainer.value.scrollHeight
        }
      })
    }
  },
  { deep: true }
)

// Helper functions for syntax highlighting
const isSuccessLine = (line: string): boolean => {
  return new RegExp(OutputLinePattern.SUCCESS, 'i').test(line)
}

const isErrorLine = (line: string): boolean => {
  return new RegExp(OutputLinePattern.ERROR, 'i').test(line)
}

const isWarningLine = (line: string): boolean => {
  return new RegExp(OutputLinePattern.WARNING, 'i').test(line)
}

const isInfoLine = (line: string): boolean => {
  return new RegExp(OutputLinePattern.INFO, 'i').test(line)
}
</script>

<style scoped>
.terminal-output {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  background: var(--gb-bg-hard);
  color: var(--gb-fg);
}

.terminal-output::-webkit-scrollbar {
  width: 8px;
}

.terminal-output::-webkit-scrollbar-track {
  background: var(--gb-bg);
}

.terminal-output::-webkit-scrollbar-thumb {
  background: var(--gb-gray);
  border-radius: 4px;
}

.terminal-output::-webkit-scrollbar-thumb:hover {
  background: var(--gb-fg-dim);
}

.welcome-message {
  margin-bottom: 2rem;
}

.welcome-message p {
  margin: 0.5rem 0;
}

.terminal-entry {
  margin-bottom: 1.5rem;
}

.terminal-entry.entry-error {
  border-left: 3px solid var(--gb-red);
  padding-left: 0.75rem;
}

.command-line {
  margin-bottom: 0.5rem;
  user-select: none;
}

.prompt-user {
  color: var(--gb-green);
  font-weight: 600;
}

.prompt-separator {
  color: var(--gb-fg-dim);
  margin: 0 0.25rem;
}

.prompt-host {
  color: var(--gb-blue);
  font-weight: 600;
}

.prompt-path {
  color: var(--gb-purple);
  margin: 0 0.5rem;
}

.prompt-symbol {
  color: var(--gb-fg);
  margin-right: 0.5rem;
}

.command-text {
  color: var(--gb-yellow);
}

.output-lines {
  margin-left: 1rem;
}

.output-line {
  color: var(--gb-fg);
  white-space: pre-wrap;
  word-break: break-word;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  margin-left: 1rem;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid var(--gb-gray);
  border-top-color: var(--gb-blue);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Utility color classes */
.text-gb-green {
  color: var(--gb-green);
}

.text-gb-red {
  color: var(--gb-red);
}

.text-gb-yellow {
  color: var(--gb-yellow);
}

.text-gb-blue {
  color: var(--gb-blue);
}

.text-gb-fg-dim {
  color: var(--gb-fg-dim);
}
</style>
