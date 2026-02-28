/**
 * Logger Service
 * 
 * Centralized logging utility with color-coded output for debugging.
 * Each module can create its own logger instance with a custom prefix.
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4
}

export interface LoggerConfig {
  /** Module name/prefix for logs */
  module: string
  /** Minimum log level to display */
  level?: LogLevel
  /** Enable/disable logging */
  enabled?: boolean
}

export class Logger {
  private module: string
  private level: LogLevel
  private enabled: boolean

  constructor(config: LoggerConfig) {
    this.module = config.module
    this.level = config.level ?? LogLevel.DEBUG
    this.enabled = config.enabled ?? true
  }

  /**
   * Debug log (gray) - detailed debugging information
   */
  debug(message: string, ...args: any[]) {
    if (!this.enabled || this.level > LogLevel.DEBUG) return
    console.log(
      `%c[${this.module}]%c ${message}`,
      'color: #928374; font-weight: bold',
      'color: #a89984',
      ...args
    )
  }

  /**
   * Info log (blue) - general information
   */
  info(message: string, ...args: any[]) {
    if (!this.enabled || this.level > LogLevel.INFO) return
    console.log(
      `%c[${this.module}]%c ${message}`,
      'color: #83a598; font-weight: bold',
      'color: #ebdbb2',
      ...args
    )
  }

  /**
   * Warning log (yellow) - potential issues
   */
  warn(message: string, ...args: any[]) {
    if (!this.enabled || this.level > LogLevel.WARN) return
    console.warn(
      `%c[${this.module}]%c ${message}`,
      'color: #fabd2f; font-weight: bold',
      'color: #ebdbb2',
      ...args
    )
  }

  /**
   * Error log (red) - errors and critical issues
   */
  error(message: string, ...args: any[]) {
    if (!this.enabled || this.level > LogLevel.ERROR) return
    console.error(
      `%c[${this.module}]%c ${message}`,
      'color: #fb4934; font-weight: bold',
      'color: #ebdbb2',
      ...args
    )
  }

  /**
   * Success log (green) - successful operations
   */
  success(message: string, ...args: any[]) {
    if (!this.enabled || this.level > LogLevel.INFO) return
    console.log(
      `%c[${this.module}]%c ✓ ${message}`,
      'color: #b8bb26; font-weight: bold',
      'color: #ebdbb2',
      ...args
    )
  }

  /**
   * Group start - collapse multiple logs
   */
  group(label: string) {
    if (!this.enabled) return
    console.group(`%c[${this.module}] ${label}`, 'color: #83a598; font-weight: bold')
  }

  /**
   * Group end
   */
  groupEnd() {
    if (!this.enabled) return
    console.groupEnd()
  }

  /**
   * Table display - useful for objects/arrays
   */
  table(data: any) {
    if (!this.enabled || this.level > LogLevel.DEBUG) return
    console.table(data)
  }

  /**
   * Log object with pretty formatting
   */
  object(label: string, obj: any) {
    if (!this.enabled || this.level > LogLevel.DEBUG) return
    console.log(
      `%c[${this.module}]%c ${label}:`,
      'color: #d3869b; font-weight: bold',
      'color: #a89984'
    )
    console.dir(obj, { depth: 3, colors: true })
  }

  /**
   * Set log level dynamically
   */
  setLevel(level: LogLevel) {
    this.level = level
  }

  /**
   * Enable/disable logging
   */
  setEnabled(enabled: boolean) {
    this.enabled = enabled
  }
}

/**
 * Create a logger instance for a module
 */
export function createLogger(module: string, level?: LogLevel): Logger {
  return new Logger({ module, level })
}

/**
 * Pre-configured loggers for common modules
 */
export const loggers = {
  stepper: createLogger('Stepper'),
  form: createLogger('Form'),
  validation: createLogger('Validation'),
  terminal: createLogger('Terminal'),
  websocket: createLogger('WebSocket'),
  auth: createLogger('Auth'),
  api: createLogger('API')
}
