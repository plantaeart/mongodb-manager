<template>
  <div class="command-input-container">
    <div class="input-wrapper">
      <!-- Command prompt -->
      <TerminalPrompt class="prompt" />

      <!-- Input field -->
      <input
        ref="inputField"
        v-model="currentCommand"
        type="text"
        class="command-input"
        :placeholder="hasActiveForm ? 'Waiting for form input...' : 'Type a command...'"
        :disabled="isExecuting || disabled || hasActiveForm"
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
        <span class="suggestion-command" v-html="highlightMatch(suggestion, currentCommand)"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TerminalCommand, TerminalConfig } from '~/enums'

interface Props {
  isExecuting?: boolean
  favorites?: string[]
  suggestions?: string[]
  disabled?: boolean
  hasActiveForm?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isExecuting: false,
  favorites: () => [],
  suggestions: () => Object.values(TerminalCommand),
  disabled: false,
  hasActiveForm: false
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
// Priority: prefix matches first, then substring-only matches
const computedSuggestions = computed(() => {
  if (!currentCommand.value) return []

  const input = currentCommand.value.toLowerCase()

  // Prefix matches (start with input, not exact)
  const prefixMatches = availableCommands.filter(cmd => {
    const cmdLower = cmd.toLowerCase()
    return cmdLower.startsWith(input) && cmdLower !== input
  })

  // Substring-only matches (contain input but don't start with it)
  const substringMatches = availableCommands.filter(cmd => {
    const cmdLower = cmd.toLowerCase()
    return cmdLower.includes(input) && !cmdLower.startsWith(input)
  })

  // Favorite matches: same two-tier logic, deduplicated against command matches
  const existingMatches = new Set([...prefixMatches, ...substringMatches])
  const favPrefixMatches = props.favorites.filter(fav => {
    const favLower = fav.toLowerCase()
    return favLower.startsWith(input) && favLower !== input && !existingMatches.has(fav)
  })
  const favSubstringMatches = props.favorites.filter(fav => {
    const favLower = fav.toLowerCase()
    return favLower.includes(input) && !favLower.startsWith(input) && !existingMatches.has(fav)
  })

  return [
    ...prefixMatches,
    ...favPrefixMatches,
    ...substringMatches,
    ...favSubstringMatches
  ].slice(0, TerminalConfig.MAX_SUGGESTIONS)
})

// Highlight the matched substring within a suggestion
const highlightMatch = (suggestion: string, input: string): string => {
  if (!input) return suggestion
  const idx = suggestion.toLowerCase().indexOf(input.toLowerCase())
  if (idx === -1) return suggestion
  const before = suggestion.slice(0, idx)
  const match = suggestion.slice(idx, idx + input.length)
  const after = suggestion.slice(idx + input.length)
  return `${before}<mark>${match}</mark>${after}`
}

// Watch command input to show/hide suggestions
watch(currentCommand, (value) => {
  showSuggestions.value = value.length > 0 && computedSuggestions.value.length > 0
  selectedSuggestionIndex.value = 0
  isNavigatingSuggestions.value = false
})

// Watch isExecuting to refocus input when command completes
watch(() => props.isExecuting, (newValue, oldValue) => {
  if (oldValue === true && newValue === false) {
    nextTick(() => {
      inputField.value?.focus()
    })
  }
})

const handleSubmit = async () => {
  if (!currentCommand.value.trim() || props.isExecuting || props.disabled) return

  const command = currentCommand.value.trim()
  
  // Add to local history (capped at MAX_LOCAL_INPUT_HISTORY)
  localHistory.value.unshift(command)
  if (localHistory.value.length > TerminalConfig.MAX_LOCAL_INPUT_HISTORY) {
    localHistory.value = localHistory.value.slice(0, TerminalConfig.MAX_LOCAL_INPUT_HISTORY)
  }
  
  emit('executeCommand', command)
  
  currentCommand.value = ''
  historyIndex.value = -1
  showSuggestions.value = false
  
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
    isNavigatingSuggestions.value = true
    selectedSuggestionIndex.value = selectedSuggestionIndex.value > 0 
      ? selectedSuggestionIndex.value - 1 
      : computedSuggestions.value.length - 1
  } else {
    navigateHistory('up')
  }
}

const handleArrowDown = () => {
  if (showSuggestions.value && computedSuggestions.value.length > 0) {
    isNavigatingSuggestions.value = true
    selectedSuggestionIndex.value = selectedSuggestionIndex.value < computedSuggestions.value.length - 1
      ? selectedSuggestionIndex.value + 1
      : 0
  } else {
    navigateHistory('down')
  }
}

const handleEnterKey = () => {
  if (showSuggestions.value && computedSuggestions.value.length > 0) {
    const suggestion = computedSuggestions.value[selectedSuggestionIndex.value]
    if (suggestion) {
      applySuggestion(suggestion)
      return
    }
  }
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
  max-height: none;
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

.suggestion-command :deep(mark) {
  background: transparent !important;
  color: var(--gb-yellow-bright);
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.suggestion-item.active .suggestion-command :deep(mark) {
  background: transparent !important;
  color: var(--gb-aqua);
}
</style>
