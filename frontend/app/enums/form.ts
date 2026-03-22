/**
 * Form-related timing constants
 */

/**
 * Form timeout durations (in milliseconds)
 */
export const FormTimeout = {
  /** Total form lifetime before it expires (5 minutes) */
  TOTAL_MS: 300_000,
  /** Time at which a "form expiring soon" warning is shown (4 minutes) */
  WARNING_MS: 240_000
} as const

/**
 * Delays used during password change flow (in milliseconds)
 */
export const PasswordChangeDelay = {
  /** How long to show the success state before closing the modal */
  SUCCESS_MS: 800
} as const
