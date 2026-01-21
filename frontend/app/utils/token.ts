/**
 * Centralized token management utilities
 */

import { StorageKey } from '~/enums'

export function setToken(token: string, rememberMe: boolean = false): void {
  if (import.meta.client) {
    if (rememberMe) {
      localStorage.setItem(StorageKey.AUTH_TOKEN, token)
      localStorage.setItem(StorageKey.AUTH_REMEMBER_ME, 'true')
    } else {
      sessionStorage.setItem(StorageKey.AUTH_TOKEN, token)
      localStorage.removeItem(StorageKey.AUTH_REMEMBER_ME)
    }
  }
}

export function getToken(): string | null {
  if (import.meta.client) {
    // Check localStorage first (remember me)
    const localToken = localStorage.getItem(StorageKey.AUTH_TOKEN)
    if (localToken) return localToken
    
    // Fall back to sessionStorage (current session only)
    const sessionToken = sessionStorage.getItem(StorageKey.AUTH_TOKEN)
    if (sessionToken) return sessionToken
  }
  return null
}

export function removeToken(): void {
  if (import.meta.client) {
    localStorage.removeItem(StorageKey.AUTH_TOKEN)
    localStorage.removeItem(StorageKey.AUTH_REMEMBER_ME)
    sessionStorage.removeItem(StorageKey.AUTH_TOKEN)
  }
}

export function isRememberMeEnabled(): boolean {
  if (import.meta.client) {
    return localStorage.getItem(StorageKey.AUTH_REMEMBER_ME) === 'true'
  }
  return false
}

export function isTokenExpired(token: string): boolean {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3 || !parts[1]) return true
    
    // Decode payload (base64url)
    const payload = JSON.parse(atob(parts[1]))
    
    // Check expiration (exp is in seconds, Date.now() is in milliseconds)
    if (payload.exp) {
      return Date.now() >= payload.exp * 1000
    }
    
    // No expiration claim - treat as valid
    return false
  } catch {
    // Invalid token format
    return true
  }
}

export function getTokenExpirationTime(token: string): number | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3 || !parts[1]) return null
    
    const payload = JSON.parse(atob(parts[1]))
    
    if (payload.exp) {
      return payload.exp * 1000 // Convert to milliseconds
    }
    
    return null
  } catch {
    return null
  }
}

export function getTimeUntilExpiration(token: string): number {
  const expirationTime = getTokenExpirationTime(token)
  if (!expirationTime) return 0
  
  return Math.max(0, expirationTime - Date.now())
}
