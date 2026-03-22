import { describe, it, expect } from 'vitest'
import { getStepperConfig, isStepperCommand } from '~/config/stepperRegistry'

// ── isStepperCommand — Built-in Commands ──────────────────────────────────

describe('isStepperCommand — Built-in Commands', () => {
  it('returns false for "help" (no stepper, built-in command)', () => {
    expect(isStepperCommand('help')).toBe(false)
  })

  it('returns false for "clear" (no stepper, built-in command)', () => {
    expect(isStepperCommand('clear')).toBe(false)
  })
})

// ── getStepperConfig — Built-in Commands ──────────────────────────────────

describe('getStepperConfig — Built-in Commands', () => {
  it('returns null for "help"', () => {
    expect(getStepperConfig('help', 'form-1')).toBeNull()
  })

  it('returns null for "clear"', () => {
    expect(getStepperConfig('clear', 'form-1')).toBeNull()
  })
})
