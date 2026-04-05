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
      <div v-if="entry.command" class="command-line">
        <TerminalPrompt :command="entry.command" />
      </div>

      <!-- Form rendering -->
      <TerminalForm
        v-if="entry.form && entry.form.type === WebSocketMessageType.FORM_REQUEST"
        :form-data="entry.form"
        :form-id="entry.form.form_id"
        :readonly="entry.status !== CommandStatus.RUNNING"
        :status="entry.status"
        @submit="handleFormSubmit(entry.form.form_id, $event)"
        @cancel="handleFormCancel(entry.form.form_id)"
      />

      <!-- File widget rendering (backup/connect export & import) -->
      <TerminalFileWidget
        v-else-if="entry.fileWidget"
        :widget-data="entry.fileWidget"
        :readonly="entry.status !== CommandStatus.RUNNING"
        @done="handleFileWidgetDone(entry.id, $event)"
        @cancel="handleFileWidgetCancel(entry.id)"
      />

      <!-- Output lines (show after form submitted or for non-form commands) -->
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
          {{ stripBackupSuffixFromLine(line) }}
        </div>
      </div>

      <!-- Status indicator -->
      <div v-if="entry.status === CommandStatus.RUNNING && !entry.form" class="status-indicator">
        <span class="spinner"></span>
        <span class="text-gb-blue">Running...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CommandStatus, OutputLinePattern, WebSocketMessageType } from '~/enums'
import type { TerminalEntry } from '~/types/terminal'
import { stripBackupSuffixFromLine } from '~/utils/backupHelpers'
import TerminalForm from './Forms/TerminalForm.vue'
import TerminalFileWidget from './Forms/TerminalFileWidget.vue'

interface Props {
  history: TerminalEntry[]
  autoScroll?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoScroll: true
})

const outputContainer = ref<HTMLElement | null>(null)
const { submitForm, cancelForm, resolveFileWidget, cancelFileWidget } = useTerminal()

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

// Form handlers
const handleFormSubmit = (formId: string | number, data: Record<string, any>) => {
  submitForm(String(formId), data)
}

const handleFormCancel = (formId: string | number) => {
  cancelForm(String(formId))
}

// File widget handlers
const handleFileWidgetDone = (entryId: string | number, message: string) => {
  resolveFileWidget(String(entryId), message)
}

const handleFileWidgetCancel = (entryId: string | number) => {
  cancelFileWidget(String(entryId))
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
