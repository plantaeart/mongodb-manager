/**
 * Tests for fieldHelpers.ts (previously formHelpers.ts).
 *
 * Note: getFieldComponentName() was removed during the Phase 4 refactor because
 * it was dead code — component resolution at runtime uses component references
 * via useFieldComponent.ts, not string names. Those tests have been removed.
 */
import { describe, it, expect } from 'vitest'
import { decodeConnectionData } from '~/utils/fieldHelpers'

// ── decodeConnectionData ───────────────────────────────────────────────────
describe('decodeConnectionData', () => {
  it('converts string port to number', () => {
    const result = decodeConnectionData({ port: '5432' }, 'connect add')
    expect(result.port).toBe(5432)
    expect(typeof result.port).toBe('number')
  })

  it('converts empty port to default 27017', () => {
    const result = decodeConnectionData({ port: '' }, 'connect add')
    expect(result.port).toBe(27017)
  })

  it('converts null port to default 27017', () => {
    const result = decodeConnectionData({ port: null }, 'connect add')
    expect(result.port).toBe(27017)
  })

  it('keeps numeric port as number', () => {
    const result = decodeConnectionData({ port: 5432 }, 'connect add')
    expect(result.port).toBe(5432)
  })

  it('removes empty optional string fields (username)', () => {
    const result = decodeConnectionData({ port: 27017, username: '' }, 'connect add')
    expect('username' in result).toBe(false)
  })

  it('removes empty optional string fields (password)', () => {
    const result = decodeConnectionData({ port: 27017, password: '' }, 'connect add')
    expect('password' in result).toBe(false)
  })

  it('removes empty optional string fields (database)', () => {
    const result = decodeConnectionData({ port: 27017, database: '' }, 'connect add')
    expect('database' in result).toBe(false)
  })

  it('removes empty optional string fields (auth_source)', () => {
    const result = decodeConnectionData({ port: 27017, auth_source: '' }, 'connect add')
    expect('auth_source' in result).toBe(false)
  })

  it('keeps non-empty optional fields', () => {
    const result = decodeConnectionData({ port: 27017, username: 'admin', password: 'secret' }, 'connect add')
    expect(result.username).toBe('admin')
    expect(result.password).toBe('secret')
  })

  it('does not mutate the original data object', () => {
    const original = { port: '27017', username: '' }
    decodeConnectionData(original, 'connect add')
    expect(original.port).toBe('27017')
    expect(original.username).toBe('')
  })

  it('removes all null-converted optional fields in a single pass', () => {
    const result = decodeConnectionData(
      { port: 27017, username: '', password: '', database: '', auth_source: '', description: '' },
      'connect add'
    )
    expect('username' in result).toBe(false)
    expect('password' in result).toBe(false)
    expect('database' in result).toBe(false)
    expect('auth_source' in result).toBe(false)
    expect('description' in result).toBe(false)
  })
})
