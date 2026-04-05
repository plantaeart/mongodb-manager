<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="['base-btn', `base-btn--${variant}`, { 'base-btn--loading': loading, 'base-btn--full': fullWidth }]"
    v-bind="$attrs"
  >
    <span v-if="loading" class="base-btn__spinner" aria-hidden="true"></span>
    <slot />
  </button>
</template>

<script setup lang="ts">
import { ButtonVariant, ButtonType } from '~/enums'

interface Props {
  /** Visual style variant */
  variant?: ButtonVariant
  /** HTML type attribute */
  type?: ButtonType
  /** Whether the button is functionally disabled (not loading) */
  disabled?: boolean
  /** Show spinner and disable interaction */
  loading?: boolean
  /** Stretch to full container width */
  fullWidth?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: ButtonVariant.PRIMARY,
  type: ButtonType.BUTTON,
  disabled: false,
  loading: false,
  fullWidth: false
})
</script>

<style scoped>
/* ── Base ── */
.base-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: none;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  padding: 8px 16px;
}

.base-btn--full {
  width: 100%;
}

.base-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Variants: Terminal (--color-* semantic vars) ── */

.base-btn--primary {
  background: var(--color-primary, #83a598);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
}

.base-btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover, #8ec07c);
}

.base-btn--secondary {
  background: transparent;
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
}

.base-btn--secondary:hover:not(:disabled) {
  background: var(--color-bg-secondary, #3c3836);
}

.base-btn--danger {
  background: var(--color-danger, #fb4934);
  color: var(--color-bg-primary, #1d2021);
  font-weight: 500;
}

.base-btn--danger:hover:not(:disabled) {
  background: var(--color-danger-hover, #cc241d);
}

/* ── Variants: Auth modals (--gb-* Gruvbox vars) ── */

.base-btn--auth-green {
  background: var(--gb-green);
  color: var(--gb-bg-hard);
  font-weight: 600;
  font-size: 14px;
  padding: 0.75rem;
  border-radius: 4px;
}

.base-btn--auth-green:hover:not(:disabled) {
  background: var(--gb-green-bright);
  transform: translateY(-1px);
}

.base-btn--auth-yellow {
  background: var(--gb-yellow);
  color: var(--gb-bg-hard);
  font-weight: 600;
  font-size: 14px;
  padding: 0.75rem;
  border-radius: 4px;
}

.base-btn--auth-yellow:hover:not(:disabled) {
  background: var(--gb-yellow-bright);
  transform: translateY(-1px);
}

/* ── Variant: StatusBar outline (--gb-* Gruvbox vars) ── */

.base-btn--outline {
  background: transparent;
  border: 1px solid var(--gb-gray);
  color: var(--gb-fg);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  padding: 0.25rem 0.75rem;
}

.base-btn--outline:hover:not(:disabled) {
  background: var(--gb-red);
  border-color: var(--gb-red);
  color: var(--gb-bg-hard);
}

/* ── Spinner ── */
.base-btn__spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: base-btn-spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes base-btn-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
