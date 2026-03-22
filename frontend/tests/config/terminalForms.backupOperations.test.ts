import { describe, it, expect } from 'vitest'
import {
  getApiPathForCommand,
  getPostApiPathForCommand,
  hasForm,
  getCommandFromFormTitle,
  COMMAND_TO_API_PATH,
  COMMAND_TO_POST_API_PATH,
} from '~/config/terminalForms'

// ── getApiPathForCommand — Backup Operations ────────────────────────────────

describe('getApiPathForCommand — Backup Operations', () => {
  it('returns correct GET path for "backup create"', () => {
    expect(getApiPathForCommand('backup create')).toBe('backup/create/select')
  })

  it('returns correct GET path for "backup list"', () => {
    expect(getApiPathForCommand('backup list')).toBe('backup/list')
  })

  it('returns correct GET path for "backup delete"', () => {
    expect(getApiPathForCommand('backup delete')).toBe('backup/delete')
  })

  it('returns correct GET path for "backup restore"', () => {
    expect(getApiPathForCommand('backup restore')).toBe('backup/restore/select')
  })
})

// ── getPostApiPathForCommand — Backup Operations ────────────────────────────

describe('getPostApiPathForCommand — Backup Operations', () => {
  it('returns DIFFERENT POST path for "backup create" (final step endpoint)', () => {
    // GET = backup/create/select (step 1)
    // POST = backup/create/configure (step 2 — final submission)
    expect(getPostApiPathForCommand('backup create')).toBe('backup/create/configure')
  })

  it('returns POST path for "backup list" (same as GET)', () => {
    expect(getPostApiPathForCommand('backup list')).toBe('backup/list')
  })

  it('returns POST path for "backup delete" (same as GET)', () => {
    expect(getPostApiPathForCommand('backup delete')).toBe('backup/delete')
  })

  it('returns DIFFERENT POST path for "backup restore" (final step endpoint)', () => {
    // GET = backup/restore/select (step 1)
    // POST = backup/restore/configure (step 2 — final submission)
    expect(getPostApiPathForCommand('backup restore')).toBe('backup/restore/configure')
  })
})

// ── hasForm — Backup Operations ────────────────────────────────────────────

describe('hasForm — Backup Operations', () => {
  it('returns true for "backup create"', () => {
    expect(hasForm('backup create')).toBe(true)
  })

  it('returns true for "backup list"', () => {
    expect(hasForm('backup list')).toBe(true)
  })

  it('returns true for "backup delete"', () => {
    expect(hasForm('backup delete')).toBe(true)
  })

  it('returns true for "backup restore"', () => {
    expect(hasForm('backup restore')).toBe(true)
  })
})

// ── getCommandFromFormTitle — Backup Operations ────────────────────────────

describe('getCommandFromFormTitle — Backup Operations', () => {
  it('returns "backup create" for a title containing "create", "backup" and "Step 1"', () => {
    expect(getCommandFromFormTitle('Create Backup - Step 1 of 2')).toBe('backup create')
  })

  it('returns "backup restore" for a title containing "restore", "backup" and "Step 1"', () => {
    expect(getCommandFromFormTitle('Restore Backup - Step 1 of 2')).toBe('backup restore')
  })

  it('returns null for "backup list" title (no matching pattern defined)', () => {
    // getCommandFromFormTitle has no pattern for backup list
    expect(getCommandFromFormTitle('List Backups - Step 1')).toBeNull()
  })

  it('returns null for "backup delete" title (no matching pattern defined)', () => {
    // getCommandFromFormTitle has no pattern for backup delete
    expect(getCommandFromFormTitle('Delete Backup - Step 1')).toBeNull()
  })

  it('returns null when title contains "create" and "backup" but no "Step 1"', () => {
    expect(getCommandFromFormTitle('Create Backup - Step 2 of 2')).toBeNull()
  })

  it('returns null when title contains "restore" and "backup" but no "Step 1"', () => {
    expect(getCommandFromFormTitle('Restore Backup - Step 2 of 2')).toBeNull()
  })
})

// ── Registry completeness — Backup Operations ──────────────────────────────

describe('COMMAND_TO_API_PATH registry — Backup Operations entries', () => {
  const backupOpsCommands = [
    'backup create',
    'backup list',
    'backup delete',
    'backup restore',
  ]

  it.each(backupOpsCommands)('"%s" is registered in COMMAND_TO_API_PATH', (cmd) => {
    expect(cmd in COMMAND_TO_API_PATH).toBe(true)
  })
})

describe('COMMAND_TO_POST_API_PATH registry — Backup Operations entries', () => {
  const backupOpsPostCommands = [
    'backup create',
    'backup list',
    'backup delete',
    'backup restore',
  ]

  it.each(backupOpsPostCommands)('"%s" is registered in COMMAND_TO_POST_API_PATH', (cmd) => {
    expect(cmd in COMMAND_TO_POST_API_PATH).toBe(true)
  })
})
