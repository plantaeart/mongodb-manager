import { defineStore } from 'pinia'
import { setToken, getToken, removeToken, isTokenExpired, getTimeUntilExpiration, isRememberMeEnabled } from '~/utils/token'
import type { LoginResult, PasswordChangeResult, LoginResponse, PasswordChangeResponse } from '~/types/auth'
import { SessionTimeout } from '~/enums'

interface AuthState {
  token: string | null
  username: string
  loading: boolean
  error: string | null
  sessionTimeoutWarning: boolean
  refreshTimer: NodeJS.Timeout | null
  warningTimer: NodeJS.Timeout | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    username: 'admin',
    loading: false,
    error: null,
    sessionTimeoutWarning: false,
    refreshTimer: null,
    warningTimer: null
  }),

  getters: {
    // Derive authentication status from token existence (single source of truth)
    isAuthenticated: (state): boolean => {
      return !!state.token
    },
    
    getUsername: (state): string => {
      return state.username
    },

    isLoading: (state): boolean => {
      return state.loading
    },

    getError: (state): string | null => {
      return state.error
    },

    hasSessionWarning: (state): boolean => {
      return state.sessionTimeoutWarning
    }
  },

  actions: {
    /**
     * Load token from storage and validate
     */
    loadTokenFromStorage() {
      const savedToken = getToken()
      if (!savedToken) {
        return
      }

      // Check if token is expired
      if (isTokenExpired(savedToken)) {
        removeToken()
        this.token = null
        return
      }

      this.token = savedToken
      
      // Setup automatic refresh and expiration warning
      this.setupTokenRefresh()
    },

    /**
     * Setup automatic token refresh before expiration
     */
    setupTokenRefresh() {
      // Clear existing timers
      this.clearTimers()

      if (!this.token) return

      const timeUntilExpiration = getTimeUntilExpiration(this.token)
      
      if (timeUntilExpiration <= 0) {
        this.logout()
        return
      }

      // Setup warning timer (5 minutes before expiration)
      const warningTime = timeUntilExpiration - SessionTimeout.WARNING_TIME
      if (warningTime > 0) {
        this.warningTimer = setTimeout(() => {
          this.sessionTimeoutWarning = true
        }, warningTime)
      }

      // Setup auto-refresh timer (2 minutes before expiration)
      const refreshTime = timeUntilExpiration - SessionTimeout.REFRESH_BUFFER
      if (refreshTime > 0) {
        this.refreshTimer = setTimeout(() => {
          this.refreshToken()
        }, refreshTime)
      }
    },

    /**
     * Clear refresh and warning timers
     */
    clearTimers() {
      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer)
        this.refreshTimer = null
      }
      if (this.warningTimer) {
        clearTimeout(this.warningTimer)
        this.warningTimer = null
      }
      this.sessionTimeoutWarning = false
    },

    /**
     * Refresh authentication token
     */
    async refreshToken(): Promise<boolean> {
      if (!this.token) {
        return false
      }

      const config = useRuntimeConfig()
      
      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          
          if (data.access_token) {
            this.token = data.access_token
            const rememberMe = isRememberMeEnabled()
            setToken(data.access_token, rememberMe)
            
            // Setup next refresh cycle
            this.setupTokenRefresh()
            
            // Clear session warning
            this.sessionTimeoutWarning = false
            
            return true
          }
        }
        
        this.logout()
        return false
      } catch (error) {
        this.logout()
        return false
      }
    },

    /**
     * Login with password
     */
    async login(password: string, rememberMe: boolean = false): Promise<LoginResult> {
      this.loading = true
      this.error = null
      
      const config = useRuntimeConfig()
      
      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password })
        })

        const data: LoginResponse = await response.json()

        if (response.ok) {
          if (data.needs_password_change) {
            return {
              success: true,
              needsPasswordChange: true,
              message: 'You must change your password to continue'
            }
          }
          
          if (data.access_token) {
            this.token = data.access_token
            this.username = data.username || 'admin'
            setToken(data.access_token, rememberMe)
            
            // Setup automatic refresh
            this.setupTokenRefresh()
            
            return {
              success: true,
              needsPasswordChange: false,
              message: `Welcome back, ${this.username}!`
            }
          }
          
          this.error = 'Invalid server response'
          return {
            success: false,
            error: 'Invalid server response'
          }
        } else {
          this.error = data.message || 'Login failed'
          return {
            success: false,
            error: data.message || 'Login failed'
          }
        }
      } catch (error) {
        this.error = 'Network error'
        return {
          success: false,
          error: 'Network error'
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * Change password (first time or regular)
     */
    async changePassword(oldPassword: string, newPassword: string): Promise<PasswordChangeResult> {
      this.loading = true
      this.error = null
      
      const config = useRuntimeConfig()
      
      try {
        const response = await fetch(`${config.public.apiUrl}/api/auth/first-time-password-change`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            old_password: oldPassword,
            new_password: newPassword
          })
        })

        const data: PasswordChangeResponse = await response.json()

        if (response.ok && data.access_token) {
          this.token = data.access_token
          this.username = data.username || 'admin'
          const rememberMe = isRememberMeEnabled()
          setToken(data.access_token, rememberMe)
          
          // Setup automatic refresh
          this.setupTokenRefresh()
          
          return { 
            success: true,
            message: 'Your password has been updated successfully'
          }
        } else {
          this.error = data.message || 'Password change failed'
          return {
            success: false,
            error: data.message || 'Password change failed'
          }
        }
      } catch (error) {
        this.error = 'Network error'
        return {
          success: false,
          error: 'Network error'
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * Logout and clear state
     */
    async logout() {
      const config = useRuntimeConfig()
      
      try {
        if (this.token) {
          await fetch(`${config.public.apiUrl}/api/auth/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.token}`
            }
          })
        }
      } catch (error) {
        // Silent fail for logout errors
      } finally {
        this.clearTimers()
        this.token = null
        this.username = 'admin'
        this.error = null
        this.sessionTimeoutWarning = false
        removeToken()
      }
    },

    /**
     * Clear error state
     */
    clearError() {
      this.error = null
    },

    /**
     * Dismiss session timeout warning
     */
    dismissSessionWarning() {
      this.sessionTimeoutWarning = false
    }
  }
})
