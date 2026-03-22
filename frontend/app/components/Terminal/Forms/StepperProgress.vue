<template>
  <div class="terminal-custom-stepper">
    <!-- Stepper Header -->
    <div class="stepper-header">
      <div 
        v-for="(step, index) in steps" 
        :key="index"
        class="stepper-item"
      >
        <div class="step-circle-wrapper">
          <!-- Circle with icon/number -->
          <div 
            class="step-circle" 
            :class="{
              'active': isActive(index),
              'completed': isCompleted(index),
              'disabled': step.disabled,
              'clickable': !step.disabled && !isActive(index)
            }"
            @click="handleStepClick(index)"
          >
            <UIcon v-if="isCompleted(index)" name="i-lucide-check" class="step-icon" />
            <UIcon v-else-if="step.icon" :name="step.icon" class="step-icon" />
            <span v-else class="step-number">{{ index + 1 }}</span>
          </div>
          
          <!-- Connecting line (not for last step) -->
          <div 
            v-if="index < steps.length - 1" 
            class="step-connector" 
            :class="{ 'completed': isCompleted(index) }"
          ></div>
        </div>
        
        <!-- Step info -->
        <div class="step-info">
          <div 
            class="step-title"
            :class="{
              'active': isActive(index),
              'disabled': step.disabled
            }"
          >
            {{ step.title }}
          </div>
          <div 
            class="step-description"
            :class="{
              'disabled': step.disabled
            }"
          >
            {{ step.description }}
          </div>
        </div>
      </div>
    </div>

    <!-- Stepper Content -->
    <div class="stepper-content">
      <slot 
        :current-step="currentStepIndex" 
        :step="currentStep"
        :has-prev="hasPrev"
        :has-next="hasNext"
      ></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface StepItem {
  title: string
  description: string
  icon?: string
  disabled?: boolean
}

interface Props {
  steps: StepItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  stepChange: [index: number]
}>()

// State
const currentStepIndex = ref(0)

// Computed
const currentStep = computed(() => props.steps[currentStepIndex.value])

const hasPrev = computed(() => currentStepIndex.value > 0)

const hasNext = computed(() => {
  const nextIndex = currentStepIndex.value + 1
  return nextIndex < props.steps.length && !props.steps[nextIndex]?.disabled
})

// Methods
const isActive = (index: number) => {
  return currentStepIndex.value === index
}

const isCompleted = (index: number) => {
  return currentStepIndex.value > index
}

const isDisabled = (index: number) => {
  return props.steps[index]?.disabled || false
}

const next = () => {
  if (hasNext.value) {
    currentStepIndex.value++
    emit('stepChange', currentStepIndex.value)
  }
}

const prev = () => {
  if (hasPrev.value) {
    currentStepIndex.value--
    emit('stepChange', currentStepIndex.value)
  }
}

const goToStep = (index: number) => {
  if (index >= 0 && index < props.steps.length && !isDisabled(index)) {
    currentStepIndex.value = index
  }
}

const handleStepClick = (index: number) => {
  // Don't navigate if clicking current step or disabled step
  if (isActive(index) || isDisabled(index)) {
    return
  }
  
  // Allow going back to previous steps
  if (index < currentStepIndex.value) {
    goToStep(index)
    emit('stepChange', index)
    return
  }
  
  // Allow going forward only to next enabled step
  if (index === currentStepIndex.value + 1 && !isDisabled(index)) {
    goToStep(index)
    emit('stepChange', index)
  }
}

// Expose methods to parent
defineExpose({
  next,
  prev,
  goToStep,
  hasPrev,
  hasNext,
  currentStepIndex
})
</script>

<style scoped>
.terminal-custom-stepper {
  width: 100%;
}

.stepper-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  position: relative;
}

.stepper-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.step-circle-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.step-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--gb-gray, #504945);
  background: var(--gb-bg-hard, #1d2021);
  color: var(--gb-fg-dim, #a89984);
  font-weight: 600;
  font-size: 18px;
  transition: all 0.3s ease;
  z-index: 2;
  position: relative;
}

.step-circle.active {
  border-color: var(--gb-blue, #83a598);
  background: var(--gb-blue, #83a598);
  color: var(--gb-bg-hard, #1d2021);
  box-shadow: 0 0 0 4px rgba(131, 165, 152, 0.2);
}

.step-circle.completed {
  border-color: var(--gb-green, #b8bb26);
  background: var(--gb-green, #b8bb26);
  color: var(--gb-bg-hard, #1d2021);
}

.step-circle.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.step-circle.clickable {
  cursor: pointer;
}

.step-circle.clickable:hover:not(.disabled) {
  transform: scale(1.1);
  box-shadow: 0 0 0 4px rgba(131, 165, 152, 0.1);
}

.step-icon {
  width: 24px;
  height: 24px;
}

.step-number {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.step-connector {
  position: absolute;
  top: 24px;
  left: calc(50% + 24px);
  width: calc(100% - 48px);
  height: 2px;
  background: transparent;
  border-top: 2px dashed var(--gb-gray, #504945);
  z-index: 1;
  transition: all 0.3s ease;
}

.step-connector.completed {
  background: var(--gb-green, #b8bb26);
  border-top: 2px solid var(--gb-green, #b8bb26);
}

.step-info {
  text-align: center;
  max-width: 200px;
}

.step-title {
  font-weight: 600;
  color: var(--gb-fg, #ebdbb2);
  font-size: 14px;
  margin-bottom: 4px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  transition: color 0.3s ease;
}

.step-title.active {
  color: var(--gb-blue, #83a598);
}

.step-title.disabled {
  opacity: 0.5;
}

.step-description {
  font-size: 12px;
  color: var(--gb-fg-dim, #a89984);
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  line-height: 1.4;
  transition: opacity 0.3s ease;
}

.step-description.disabled {
  opacity: 0.4;
}

.stepper-content {
  min-height: 200px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .stepper-header {
    flex-direction: column;
    gap: 20px;
  }
  
  .stepper-item {
    width: 100%;
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
  }
  
  .step-circle-wrapper {
    width: auto;
    margin-bottom: 0;
    margin-right: 16px;
  }
  
  .step-connector {
    display: none;
  }
  
  .step-info {
    text-align: left;
    max-width: none;
  }
}
</style>
