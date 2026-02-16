<template>
  <span v-if="text" class="tooltip-wrapper" :data-tooltip="text">
    <UIcon name="i-heroicons-information-circle" class="info-icon" />
  </span>
</template>

<script setup lang="ts">
defineProps<{
  text?: string
}>()
</script>

<style scoped>
.tooltip-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: help;
}

.info-icon {
  width: 14px;
  height: 14px;
  color: var(--color-text-tertiary, #928374);
  opacity: 0.7;
  transition: all 0.2s;
}

.tooltip-wrapper:hover .info-icon {
  opacity: 1;
  color: var(--color-primary, #83a598);
}

/* Tooltip - Default centered position */
.tooltip-wrapper::before {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-bg-tertiary, #282828);
  color: var(--color-text-primary, #ebdbb2);
  border: 1px solid var(--color-border-secondary, #504945);
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  z-index: 1000;
  min-width: 200px;
  max-width: min(350px, calc(100vw - 32px));
  width: max-content;
  line-height: 1.5;
  white-space: normal;
}

/* Hover state */
.tooltip-wrapper:hover::before {
  opacity: 1;
}

/* Grid layout: Left column (first child in grid) - align tooltip to left */
.form-body.two-columns > .terminal-field:nth-child(odd) .tooltip-wrapper::before {
  left: 0;
  transform: none;
}

/* Grid layout: Right column - keep centered (default) */
.form-body.two-columns > .terminal-field:nth-child(even) .tooltip-wrapper::before {
  left: 50%;
  transform: translateX(-50%);
}

/* Single column layout: Check if field is at the start (potential left edge) */
.form-body:not(.two-columns) > .terminal-field:first-child .tooltip-wrapper::before,
.form-body:not(.two-columns) > .terminal-field:nth-child(2) .tooltip-wrapper::before {
  left: 0;
  transform: none;
}

/* Responsive: Smaller screens always align to left */
@media (max-width: 768px) {
  .tooltip-wrapper::before {
    left: 0;
    transform: none;
    min-width: 180px;
    max-width: min(280px, calc(100vw - 32px));
  }
}
</style>
