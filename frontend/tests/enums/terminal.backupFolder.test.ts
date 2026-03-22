import { describe, it, expect } from 'vitest'
import { TerminalCommand } from '~/enums/terminal'

// ── TerminalCommand enum — Backup Folder Management ────────────────────────

describe('TerminalCommand enum — Backup Folder Management', () => {
  it('BACKUP_FOLDER_ADD equals "backup folder add"', () => {
    expect(TerminalCommand.BACKUP_FOLDER_ADD).toBe('backup folder add')
  })

  it('BACKUP_FOLDER_DELETE equals "backup folder delete"', () => {
    expect(TerminalCommand.BACKUP_FOLDER_DELETE).toBe('backup folder delete')
  })

  it('BACKUP_FOLDER_LIST equals "backup folder list"', () => {
    expect(TerminalCommand.BACKUP_FOLDER_LIST).toBe('backup folder list')
  })
})
