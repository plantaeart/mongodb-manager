<template>
  <span class="terminal-prompt">
    <span class="prompt-user">{{ TERMINAL_PROMPT.user }}</span>
    <span class="prompt-separator">@</span>
    <span class="prompt-host">{{ TERMINAL_PROMPT.host }}</span>
    <span class="prompt-path">{{ TERMINAL_PROMPT.path }}</span>
    <span class="prompt-symbol">{{ TERMINAL_PROMPT.symbol }}</span>
    <span v-if="command" class="prompt-command">{{ command }}</span>
  </span>
</template>

<script setup lang="ts">
import { TERMINAL_PROMPT } from '~/config/terminal'

interface Props {
  /** Optional command text displayed after the prompt symbol */
  command?: string
}

defineProps<Props>()
</script>

<style scoped>
.terminal-prompt {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
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

.prompt-command {
  color: var(--gb-yellow);
  user-select: text;
}
</style>
