/**
 * UI button color variants
 * Used for visual panel quick command buttons
 */
export enum ButtonColor {
  GREEN = 'green',
  BLUE = 'blue',
  PURPLE = 'purple',
  YELLOW = 'yellow'
}

/**
 * BaseButton visual variants
 * Maps to CSS modifier classes and color-scheme
 */
export enum ButtonVariant {
  PRIMARY = 'primary',
  SECONDARY = 'secondary',
  DANGER = 'danger',
  /** Auth modals — green Gruvbox theme */
  AUTH_GREEN = 'auth-green',
  /** Auth modals — yellow Gruvbox theme */
  AUTH_YELLOW = 'auth-yellow',
  /** Status bar outline style */
  OUTLINE = 'outline'
}

/**
 * HTML button type attribute values
 */
export enum ButtonType {
  BUTTON = 'button',
  SUBMIT = 'submit',
  RESET = 'reset'
}
