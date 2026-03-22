import { describe, it, expect } from 'vitest'
import { getStepperConfig, isStepperCommand } from '~/config/stepperRegistry'

// ── isStepperCommand — Authentication ─────────────────────────────────────

describe('isStepperCommand — Authentication', () => {
  it('returns false for "auth change-password" (no stepper, WebSocket command)', () => {
    expect(isStepperCommand('auth change-password')).toBe(false)
  })

  it('returns false for "auth logout" (no stepper, WebSocket command)', () => {
    expect(isStepperCommand('auth logout')).toBe(false)
  })
})

// ── getStepperConfig — Authentication ─────────────────────────────────────

describe('getStepperConfig — Authentication', () => {
  it('returns null for "auth change-password"', () => {
    expect(getStepperConfig('auth change-password', 'form-1')).toBeNull()
  })

  it('returns null for "auth logout"', () => {
    expect(getStepperConfig('auth logout', 'form-1')).toBeNull()
  })
})
