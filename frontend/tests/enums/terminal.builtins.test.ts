import { describe, it, expect } from 'vitest'
import { TerminalCommand } from '~/enums/terminal'

// ── TerminalCommand enum — Built-in Commands ───────────────────────────────

describe('TerminalCommand enum — Built-in Commands', () => {
  it('HELP equals "help"', () => {
    expect(TerminalCommand.HELP).toBe('help')
  })

  it('CLEAR equals "clear"', () => {
    expect(TerminalCommand.CLEAR).toBe('clear')
  })
})
