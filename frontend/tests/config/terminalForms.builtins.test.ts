import { describe, it, expect } from 'vitest'
import {
  hasForm,
  getCommandFromFormTitle,
  COMMAND_TO_API_PATH,
  COMMAND_TO_POST_API_PATH,
} from '~/config/terminalForms'

// ── hasForm — Built-in Commands ───────────────────────────────────────────

describe('hasForm — Built-in Commands', () => {
  it('returns false for "help" (built-in, no form)', () => {
    expect(hasForm('help')).toBe(false)
  })

  it('returns false for "clear" (built-in, no form)', () => {
    expect(hasForm('clear')).toBe(false)
  })
})

// ── getCommandFromFormTitle — Built-in Commands ───────────────────────────

describe('getCommandFromFormTitle — Built-in Commands', () => {
  it('returns null for a "help" title (no pattern defined)', () => {
    expect(getCommandFromFormTitle('Help - Step 1')).toBeNull()
  })

  it('returns null for a "clear" title (no pattern defined)', () => {
    expect(getCommandFromFormTitle('Clear - Step 1')).toBeNull()
  })
})

// ── Registry completeness — Built-in Commands ─────────────────────────────

describe('COMMAND_TO_API_PATH registry — Built-in entries absent', () => {
  it('"help" is NOT registered in COMMAND_TO_API_PATH', () => {
    expect('help' in COMMAND_TO_API_PATH).toBe(false)
  })

  it('"clear" is NOT registered in COMMAND_TO_API_PATH', () => {
    expect('clear' in COMMAND_TO_API_PATH).toBe(false)
  })
})

describe('COMMAND_TO_POST_API_PATH registry — Built-in entries absent', () => {
  it('"help" is NOT registered in COMMAND_TO_POST_API_PATH', () => {
    expect('help' in COMMAND_TO_POST_API_PATH).toBe(false)
  })

  it('"clear" is NOT registered in COMMAND_TO_POST_API_PATH', () => {
    expect('clear' in COMMAND_TO_POST_API_PATH).toBe(false)
  })
})
