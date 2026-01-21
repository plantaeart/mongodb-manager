/**
 * Toast notification color variants
 * Used for styling toast messages based on message type
 */
export enum ToastColor {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

/**
 * Toast notification duration constants (in milliseconds)
 * Controls how long toast messages are displayed
 */
export enum ToastDuration {
  SHORT = 3000,      // 3 seconds
  MEDIUM = 5000,     // 5 seconds
  LONG = 10000       // 10 seconds
}
