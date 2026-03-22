import { describe, it, expect } from 'vitest'
import { TerminalCommand } from '~/enums/terminal'

// ── TerminalCommand enum — Connection Management ───────────────────────────

describe('TerminalCommand enum — Connection Management', () => {
  it('CONNECT_LIST equals "connect list"', () => {
    expect(TerminalCommand.CONNECT_LIST).toBe('connect list')
  })

  it('CONNECT_ADD equals "connect add"', () => {
    expect(TerminalCommand.CONNECT_ADD).toBe('connect add')
  })

  it('CONNECT_REMOVE equals "connect remove"', () => {
    expect(TerminalCommand.CONNECT_REMOVE).toBe('connect remove')
  })

  it('CONNECT_TEST equals "connect test"', () => {
    expect(TerminalCommand.CONNECT_TEST).toBe('connect test')
  })

  it('CONNECT_UPDATE equals "connect update"', () => {
    expect(TerminalCommand.CONNECT_UPDATE).toBe('connect update')
  })
})
