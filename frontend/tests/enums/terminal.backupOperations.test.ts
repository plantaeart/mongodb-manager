import { describe, it, expect } from 'vitest'
import { TerminalCommand } from '~/enums/terminal'

// ── TerminalCommand enum — Backup Operations ────────────────────────────────

describe('TerminalCommand enum — Backup Operations', () => {
  it('BACKUP_CREATE equals "backup create"', () => {
    expect(TerminalCommand.BACKUP_CREATE).toBe('backup create')
  })

  it('BACKUP_LIST equals "backup list"', () => {
    expect(TerminalCommand.BACKUP_LIST).toBe('backup list')
  })

  it('BACKUP_DELETE equals "backup delete"', () => {
    expect(TerminalCommand.BACKUP_DELETE).toBe('backup delete')
  })

  it('BACKUP_RESTORE equals "backup restore"', () => {
    expect(TerminalCommand.BACKUP_RESTORE).toBe('backup restore')
  })
})
