import { describe, it, expect } from 'vitest'
import {
  hasForm,
  getCommandFromFormTitle,
  COMMAND_TO_API_PATH,
  COMMAND_TO_POST_API_PATH,
} from '~/config/terminalForms'

// ── hasForm — Authentication ───────────────────────────────────────────────

describe('hasForm — Authentication', () => {
  it('returns false for "auth change-password" (WebSocket command, no form)', () => {
    expect(hasForm('auth change-password')).toBe(false)
  })

  it('returns false for "auth logout" (WebSocket command, no form)', () => {
    expect(hasForm('auth logout')).toBe(false)
  })
})

// ── getCommandFromFormTitle — Authentication ───────────────────────────────

describe('getCommandFromFormTitle — Authentication', () => {
  it('returns null for an "auth change-password" title (no pattern defined)', () => {
    expect(getCommandFromFormTitle('Change Password - Step 1')).toBeNull()
  })

  it('returns null for an "auth logout" title (no pattern defined)', () => {
    expect(getCommandFromFormTitle('Logout - Step 1')).toBeNull()
  })
})

// ── Registry completeness — Authentication ─────────────────────────────────

describe('COMMAND_TO_API_PATH registry — Authentication entries absent', () => {
  it('"auth change-password" is NOT registered in COMMAND_TO_API_PATH', () => {
    expect('auth change-password' in COMMAND_TO_API_PATH).toBe(false)
  })

  it('"auth logout" is NOT registered in COMMAND_TO_API_PATH', () => {
    expect('auth logout' in COMMAND_TO_API_PATH).toBe(false)
  })
})

describe('COMMAND_TO_POST_API_PATH registry — Authentication entries absent', () => {
  it('"auth change-password" is NOT registered in COMMAND_TO_POST_API_PATH', () => {
    expect('auth change-password' in COMMAND_TO_POST_API_PATH).toBe(false)
  })

  it('"auth logout" is NOT registered in COMMAND_TO_POST_API_PATH', () => {
    expect('auth logout' in COMMAND_TO_POST_API_PATH).toBe(false)
  })
})
