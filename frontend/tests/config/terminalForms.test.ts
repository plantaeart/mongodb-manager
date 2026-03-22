import { describe, it, expect } from 'vitest'
import {
  getApiPathForCommand,
  getPostApiPathForCommand,
  hasForm,
  getCommandFromFormTitle,
  COMMAND_TO_API_PATH,
  COMMAND_TO_POST_API_PATH,
} from '~/config/terminalForms'

// ── getApiPathForCommand — Connection Management ────────────────────────────

describe('getApiPathForCommand — Connection Management', () => {
  it('returns correct GET path for "connect list"', () => {
    expect(getApiPathForCommand('connect list')).toBe('connect/list')
  })

  it('returns correct GET path for "connect add"', () => {
    expect(getApiPathForCommand('connect add')).toBe('connect/add')
  })

  it('returns correct GET path for "connect remove"', () => {
    expect(getApiPathForCommand('connect remove')).toBe('connect/remove')
  })

  it('returns correct GET path for "connect test"', () => {
    expect(getApiPathForCommand('connect test')).toBe('connect/test')
  })

  it('returns step-1 GET path for "connect update"', () => {
    expect(getApiPathForCommand('connect update')).toBe('connect/update/select')
  })

  it('returns undefined for an unknown connection command', () => {
    expect(getApiPathForCommand('connect unknown')).toBeUndefined()
  })
})

// ── getPostApiPathForCommand — Connection Management ───────────────────────

describe('getPostApiPathForCommand — Connection Management', () => {
  it('returns POST path for "connect add" (same as GET — single-step)', () => {
    expect(getPostApiPathForCommand('connect add')).toBe('connect/add')
  })

  it('returns POST path for "connect remove" (same as GET — single-step)', () => {
    expect(getPostApiPathForCommand('connect remove')).toBe('connect/remove')
  })

  it('returns POST path for "connect test" (same as GET — single-step)', () => {
    expect(getPostApiPathForCommand('connect test')).toBe('connect/test')
  })

  it('falls back to GET path for "connect update" (not in POST map)', () => {
    // connect update is not in COMMAND_TO_POST_API_PATH — falls back to GET path
    expect(getPostApiPathForCommand('connect update')).toBe('connect/update/select')
  })

  it('returns undefined for an unknown command', () => {
    expect(getPostApiPathForCommand('connect nonexistent')).toBeUndefined()
  })
})

// ── hasForm — Connection Management ───────────────────────────────────────

describe('hasForm — Connection Management', () => {
  it('returns true for "connect list"', () => {
    expect(hasForm('connect list')).toBe(true)
  })

  it('returns true for "connect add"', () => {
    expect(hasForm('connect add')).toBe(true)
  })

  it('returns true for "connect remove"', () => {
    expect(hasForm('connect remove')).toBe(true)
  })

  it('returns true for "connect test"', () => {
    expect(hasForm('connect test')).toBe(true)
  })

  it('returns true for "connect update"', () => {
    expect(hasForm('connect update')).toBe(true)
  })

  it('returns false for an unknown command', () => {
    expect(hasForm('connect unknown')).toBe(false)
  })
})

// ── getCommandFromFormTitle — Connection Management ────────────────────────

describe('getCommandFromFormTitle — Connection Management', () => {
  it('returns "connect update" for a title containing "update", "connection" and "Step 1"', () => {
    expect(getCommandFromFormTitle('Update MongoDB Connection - Step 1 of 2')).toBe('connect update')
  })

  it('returns null when title has no "Step 1"', () => {
    expect(getCommandFromFormTitle('Update MongoDB Connection - Step 2 of 2')).toBeNull()
  })

  it('returns null for a completely unrelated Step 1 title', () => {
    expect(getCommandFromFormTitle('Export Data - Step 1 of 3')).toBeNull()
  })

  it('returns null for an empty string', () => {
    expect(getCommandFromFormTitle('')).toBeNull()
  })
})

// ── Registry completeness — Connection Management ──────────────────────────

describe('COMMAND_TO_API_PATH registry — Connection Management entries', () => {
  const connectionCommands = [
    'connect list',
    'connect add',
    'connect remove',
    'connect test',
    'connect update',
  ]

  it.each(connectionCommands)('"%s" is registered in COMMAND_TO_API_PATH', (cmd) => {
    expect(cmd in COMMAND_TO_API_PATH).toBe(true)
  })
})

describe('COMMAND_TO_POST_API_PATH registry — single-step Connection Management entries', () => {
  const singleStepCommands = ['connect add', 'connect remove', 'connect test']

  it.each(singleStepCommands)('"%s" is registered in COMMAND_TO_POST_API_PATH', (cmd) => {
    expect(cmd in COMMAND_TO_POST_API_PATH).toBe(true)
  })
})
