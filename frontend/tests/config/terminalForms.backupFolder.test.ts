import { describe, it, expect } from 'vitest'
import {
  getApiPathForCommand,
  getPostApiPathForCommand,
  hasForm,
  getCommandFromFormTitle,
  COMMAND_TO_API_PATH,
  COMMAND_TO_POST_API_PATH,
} from '~/config/terminalForms'

// ── getApiPathForCommand — Backup Folder Management ────────────────────────

describe('getApiPathForCommand — Backup Folder Management', () => {
  it('returns correct GET path for "backup folder add"', () => {
    expect(getApiPathForCommand('backup folder add')).toBe('backup/folder/add/configure')
  })

  it('returns correct GET path for "backup folder delete"', () => {
    expect(getApiPathForCommand('backup folder delete')).toBe('backup/folder/delete/select')
  })

  it('returns correct GET path for "backup folder list"', () => {
    expect(getApiPathForCommand('backup folder list')).toBe('backup/folder/list')
  })
})

// ── getPostApiPathForCommand — Backup Folder Management ────────────────────

describe('getPostApiPathForCommand — Backup Folder Management', () => {
  it('returns POST path for "backup folder add" (same as GET)', () => {
    expect(getPostApiPathForCommand('backup folder add')).toBe('backup/folder/add/configure')
  })

  it('returns DIFFERENT POST path for "backup folder delete" (final step endpoint)', () => {
    // GET = backup/folder/delete/select (step 1)
    // POST = backup/folder/delete/confirm (step 2 — final submission)
    expect(getPostApiPathForCommand('backup folder delete')).toBe('backup/folder/delete/confirm')
  })

  it('returns POST path for "backup folder list" (same as GET)', () => {
    expect(getPostApiPathForCommand('backup folder list')).toBe('backup/folder/list')
  })
})

// ── hasForm — Backup Folder Management ────────────────────────────────────

describe('hasForm — Backup Folder Management', () => {
  it('returns true for "backup folder add"', () => {
    expect(hasForm('backup folder add')).toBe(true)
  })

  it('returns true for "backup folder delete"', () => {
    expect(hasForm('backup folder delete')).toBe(true)
  })

  it('returns true for "backup folder list"', () => {
    expect(hasForm('backup folder list')).toBe(true)
  })
})

// ── getCommandFromFormTitle — Backup Folder Management ────────────────────

describe('getCommandFromFormTitle — Backup Folder Management', () => {
  it('returns "backup folder add" for a title containing "add", "backup", "folder" and "Step 1"', () => {
    expect(getCommandFromFormTitle('Add Backup Folder - Step 1 of 2')).toBe('backup folder add')
  })

  it('returns null for "backup folder delete" title (no matching pattern defined)', () => {
    // getCommandFromFormTitle has no pattern for backup folder delete
    expect(getCommandFromFormTitle('Delete Backup Folder - Step 1 of 2')).toBeNull()
  })

  it('returns null when title contains "backup folder" but no "Step 1"', () => {
    expect(getCommandFromFormTitle('Add Backup Folder - Step 2 of 2')).toBeNull()
  })
})

// ── Registry completeness — Backup Folder Management ──────────────────────

describe('COMMAND_TO_API_PATH registry — Backup Folder Management entries', () => {
  const backupFolderCommands = [
    'backup folder add',
    'backup folder delete',
    'backup folder list',
  ]

  it.each(backupFolderCommands)('"%s" is registered in COMMAND_TO_API_PATH', (cmd) => {
    expect(cmd in COMMAND_TO_API_PATH).toBe(true)
  })
})

describe('COMMAND_TO_POST_API_PATH registry — Backup Folder Management entries', () => {
  const backupFolderPostCommands = [
    'backup folder add',
    'backup folder delete',
    'backup folder list',
  ]

  it.each(backupFolderPostCommands)('"%s" is registered in COMMAND_TO_POST_API_PATH', (cmd) => {
    expect(cmd in COMMAND_TO_POST_API_PATH).toBe(true)
  })
})
