import { describe, it, expect } from 'vitest'
import { TerminalCommand } from '~/enums/terminal'

// ── TerminalCommand enum — Authentication ──────────────────────────────────

describe('TerminalCommand enum — Authentication', () => {
  it('AUTH_CHANGE_PASSWORD equals "auth change-password"', () => {
    expect(TerminalCommand.AUTH_CHANGE_PASSWORD).toBe('auth change-password')
  })

  it('AUTH_LOGOUT equals "auth logout"', () => {
    expect(TerminalCommand.AUTH_LOGOUT).toBe('auth logout')
  })
})
