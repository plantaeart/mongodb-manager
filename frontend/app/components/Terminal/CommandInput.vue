<template>
  <div class="command-input-container">
    <div class="input-wrapper">
      <!-- Command prompt -->
      <div class="prompt">
        <span class="prompt-user">admin</span>
        <span class="prompt-separator">@</span>
        <span class="prompt-host">mongodb-manager</span>
        <span class="prompt-path">~</span>
        <span class="prompt-symbol">$</span>
      </div>

      <!-- Input field -->
      <input
        ref="inputField"
        v-model="currentCommand"
        type="text"
        class="command-input"
        placeholder="Type a command..."
        :disabled="isExecuting || disabled"
        @keydown.enter="handleEnterKey"
        @keydown.up.prevent="handleArrowUp"
        @keydown.down.prevent="handleArrowDown"
        @keydown.tab.prevent="handleTabComplete"
        @keydown.esc="dismissSuggestions"
      />
    </div>

    <!-- Autocomplete suggestions -->
    <div v-if="showSuggestions && computedSuggestions.length > 0" class="suggestions-dropdown">
      <div
        v-for="(suggestion, index) in computedSuggestions"
        :key="index"
        class="suggestion-item"
        :class="{ active: index === selectedSuggestionIndex }"
        @click="applySuggestion(suggestion)"
      >
        <span class="suggestion-command">{{ suggestion }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TerminalCommand } from '~/enums'

interface Props {
  isExecuting?: boolean
  favorites?: string[]
  suggestions?: string[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isExecuting: false,
  favorites: () => [],
  suggestions: () => Object.values(TerminalCommand),
  disabled: false
})

const emit = defineEmits<{
  executeCommand: [command: string]
  toggleFavorite: [command: string]
}>()

const inputField = ref<HTMLInputElement | null>(null)
const currentCommand = ref('')
const historyIndex = ref(-1)
const localHistory = ref<string[]>([])
const showSuggestions = ref(false)
const selectedSuggestionIndex = ref(0)
const isNavigatingSuggestions = ref(false)

// Available commands for autocomplete
const availableCommands = props.suggestions

// Compute suggestions based on current input
const computedSuggestions = computed(() => {
  if (!currentCommand.value) return []
  
  const input = currentCommand.value.toLowerCase()
  
  // Filter commands that start with input BUT exclude exact matches
  const matches: string[] = availableCommands.filter(cmd => {
    const cmdLower = cmd.toLowerCase()
    return cmdLower.startsWith(input) && cmdLower !== input
  })
  
  // Also include favorites that match (but not exact matches)
  const favoriteMatches = props.favorites.filter(fav => {
    const favLower = fav.toLowerCase()
    return favLower.startsWith(input) && 
           favLower !== input && 
           !matches.includes(fav)
  })
  
  return [...matches, ...favoriteMatches].slice(0, 5)
})

// Watch command input to show/hide suggestions
watch(currentCommand, (value) => {
  showSuggestions.value = value.length > 0 && computedSuggestions.value.length > 0
  selectedSuggestionIndex.value = 0
  isNavigatingSuggestions.value = false
})

const handleSubmit = async () => {
  if (!currentCommand.value.trim() || props.isExecuting || props.disabled) return

  const command = currentCommand.value.trim()
  
  // Add to local history
  localHistory.value.unshift(command)
  if (localHistory.value.length > 50) {
    localHistory.value = localHistory.value.slice(0, 50)
  }
  
  // Emit command execution
  emit('executeCommand', command)
  
  // Clear input and reset history index
  currentCommand.value = ''
  historyIndex.value = -1
  showSuggestions.value = false
  
  // Keep input focused for next command
  await nextTick()
  inputField.value?.focus()
}

const navigateHistory = (direction: 'up' | 'down') => {
  if (localHistory.value.length === 0) return

  if (direction === 'up') {
    if (historyIndex.value < localHistory.value.length - 1) {
      historyIndex.value++
      currentCommand.value = localHistory.value[historyIndex.value] || ''
    }
  } else {
    if (historyIndex.value > 0) {
      historyIndex.value--
      currentCommand.value = localHistory.value[historyIndex.value] || ''
    } else if (historyIndex.value === 0) {
      historyIndex.value = -1
      currentCommand.value = ''
    }
  }
}

const handleArrowUp = () => {
  if (showSuggestions.value && computedSuggestions.value.length > 0) {
    // Navigate suggestions (move selection up with wrapping)
    isNavigatingSuggestions.value = true
    selectedSuggestionIndex.value = selectedSuggestionIndex.value > 0 
      ? selectedSuggestionIndex.value - 1 
      : computedSuggestions.value.length - 1
  } else {
    // Navigate command history (existing behavior)
    navigateHistory('up')
  }
}

const handleArrowDown = () => {
  if (showSuggestions.value && computedSuggestions.value.length > 0) {
    // Navigate suggestions (move selection down with wrapping)
    isNavigatingSuggestions.value = true
    selectedSuggestionIndex.value = selectedSuggestionIndex.value < computedSuggestions.value.length - 1
      ? selectedSuggestionIndex.value + 1
      : 0
  } else {
    // Navigate command history (existing behavior)
    navigateHistory('down')
  }
}

const handleEnterKey = () => {
  // If suggestions visible and user has selected one, apply it
  if (showSuggestions.value && computedSuggestions.value.length > 0) {
    const suggestion = computedSuggestions.value[selectedSuggestionIndex.value]
    if (suggestion) {
      applySuggestion(suggestion)
      return // Don't execute, just apply
    }
  }
  
  // Otherwise, execute the typed command
  handleSubmit()
}

const dismissSuggestions = () => {
  showSuggestions.value = false
  isNavigatingSuggestions.value = false
  selectedSuggestionIndex.value = 0
}

const handleTabComplete = () => {
  if (computedSuggestions.value.length > 0) {
    const suggestion = computedSuggestions.value[selectedSuggestionIndex.value]
    if (suggestion) {
      applySuggestion(suggestion)
    }
  }
}

const applySuggestion = (suggestion: string) => {
  currentCommand.value = suggestion
  showSuggestions.value = false
  isNavigatingSuggestions.value = false
  selectedSuggestionIndex.value = 0
  inputField.value?.focus()
}

// Focus input on mount
onMounted(() => {
  inputField.value?.focus()
})
</script>

<style scoped>
.command-input-container {
  position: relative;
  border-top: 1px solid var(--gb-gray);
  background: var(--gb-bg-hard);
}

.input-wrapper {
  display: flex;
  align-items: center;
  padding: 1rem;
  gap: 0.5rem;
}

.prompt {
  flex-shrink: 0;
  user-select: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
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

.command-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--gb-yellow);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  outline: none;
  padding: 0;
}

.command-input::placeholder {
  color: var(--gb-fg-dim);
  opacity: 0.5;
}

.command-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.suggestions-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: var(--gb-bg);
  border: 1px solid var(--gb-gray);
  border-bottom: none;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
}

.suggestion-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.1s;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
}

.suggestion-item:hover,
.suggestion-item.active {
  background: var(--gb-bg-soft);
}

.suggestion-command {
  color: var(--gb-fg);
}

.suggestion-item.active .suggestion-command {
  color: var(--gb-yellow);
}
</style>
