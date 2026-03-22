import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { isTokenExpired, getTokenExpirationTime, getTimeUntilExpiration } from '~/utils/token'

// ── JWT test helper ────────────────────────────────────────────────────────
/**
 * Build a minimal, structurally valid JWT (unsigned — only for payload decoding tests).
 * format: base64(header).base64(payload).fakesig
 */
function makeJwt(payload: Record<string, unknown>): string {
  const header = { alg: 'HS256', typ: 'JWT' }
  const encodedHeader = btoa(JSON.stringify(header))
  const encodedPayload = btoa(JSON.stringify(payload))
  return `${encodedHeader}.${encodedPayload}.fakesig`
}

// exp in seconds relative to "now"
function expInSeconds(secondsFromNow: number): number {
  return Math.floor(Date.now() / 1000) + secondsFromNow
}

// ── isTokenExpired ─────────────────────────────────────────────────────────
describe('isTokenExpired', () => {
  it('returns false for a token with exp in the future', () => {
    const token = makeJwt({ username: 'admin', exp: expInSeconds(3600) })
    expect(isTokenExpired(token)).toBe(false)
  })

  it('returns true for a token with exp in the past', () => {
    const token = makeJwt({ username: 'admin', exp: expInSeconds(-1) })
    expect(isTokenExpired(token)).toBe(true)
  })

  it('returns false for a token with no exp claim (treated as valid)', () => {
    const token = makeJwt({ username: 'admin' })
    expect(isTokenExpired(token)).toBe(false)
  })

  it('returns true for a completely invalid token string', () => {
    expect(isTokenExpired('not-a-token')).toBe(true)
  })

  it('returns true for a token with only two parts', () => {
    expect(isTokenExpired('header.payload')).toBe(true)
  })

  it('returns true for an empty string', () => {
    expect(isTokenExpired('')).toBe(true)
  })

  it('returns true for a token with a non-JSON payload', () => {
    expect(isTokenExpired('aaa.!!!.ccc')).toBe(true)
  })
})

// ── getTokenExpirationTime ─────────────────────────────────────────────────
describe('getTokenExpirationTime', () => {
  it('returns exp * 1000 (milliseconds) for a valid token', () => {
    const expSec = expInSeconds(3600)
    const token = makeJwt({ exp: expSec })
    expect(getTokenExpirationTime(token)).toBe(expSec * 1000)
  })

  it('returns null when there is no exp claim', () => {
    const token = makeJwt({ username: 'admin' })
    expect(getTokenExpirationTime(token)).toBeNull()
  })

  it('returns null for an invalid token string', () => {
    expect(getTokenExpirationTime('invalid')).toBeNull()
  })

  it('returns null for empty string', () => {
    expect(getTokenExpirationTime('')).toBeNull()
  })
})

// ── getTimeUntilExpiration ─────────────────────────────────────────────────
describe('getTimeUntilExpiration', () => {
  it('returns a positive number of ms for a future token', () => {
    const token = makeJwt({ exp: expInSeconds(3600) })
    const timeLeft = getTimeUntilExpiration(token)
    expect(timeLeft).toBeGreaterThan(0)
    // Should be close to 3600 * 1000 ms (within 5 seconds tolerance)
    expect(timeLeft).toBeLessThanOrEqual(3600 * 1000)
    expect(timeLeft).toBeGreaterThan(3595 * 1000)
  })

  it('returns 0 for an already-expired token (never negative)', () => {
    const token = makeJwt({ exp: expInSeconds(-100) })
    expect(getTimeUntilExpiration(token)).toBe(0)
  })

  it('returns 0 for a token with no exp claim', () => {
    const token = makeJwt({ username: 'admin' })
    expect(getTimeUntilExpiration(token)).toBe(0)
  })

  it('returns 0 for an invalid token', () => {
    expect(getTimeUntilExpiration('bad')).toBe(0)
  })
})
