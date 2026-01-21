/**
 * Authentication type definitions
 */

export interface LoginResponse {
  access_token: string
  username: string
  needs_password_change: boolean
  message?: string
}

export interface LoginResult {
  success: boolean
  username?: string
  needsPasswordChange?: boolean
  error?: string
  message?: string
}

export interface PasswordChangeResult {
  success: boolean
  error?: string
  message?: string
}

export interface PasswordChangeResponse {
  access_token: string
  username: string
  message?: string
}
