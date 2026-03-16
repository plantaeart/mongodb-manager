import { CommandStatus, WebSocketMessageType } from '~/enums'

export interface TerminalEntry {
  id: number | string
  command: string
  output: string[]
  timestamp: Date
  status: CommandStatus
  form?: FormRequestMessage | FormStepperMessage | null
}

export interface WebSocketMessage {
  type: Exclude<WebSocketMessageType, WebSocketMessageType.EXECUTE>
  line?: string
  status?: CommandStatus.SUCCESS | CommandStatus.ERROR
  exit_code?: number
  error?: string
  timestamp?: string
}

export interface CommandExecuteRequest {
  type: WebSocketMessageType.EXECUTE
  command: string
}

// Form Types
export interface ValidationRule {
  pattern?: string
  message: string
  min?: number
  max?: number
}

export interface SelectOption {
  value: string
  label: string
  description?: string
  metadata?: Record<string, any>
}

export type FieldType = 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'checkbox-list' | 'date' | 'readonly' | 'password' | 'list'

// List Item Display Configuration
export interface ListItemField {
  key: string           // The property key in the item object
  label: string         // Display label for this field
  icon?: string         // Optional emoji icon
  type?: 'text' | 'date' | 'list' | 'badge'  // How to render the value
  primary?: boolean     // If true, this field is the main identifier (shown in header)
  badge_key?: string    // For type='badge', the key to compare for active state
}

export interface ListDisplayConfig {
  header_icon?: string  // Icon for the header (default based on first primary field)
  fields: ListItemField[]
  count_label?: string  // Label for total count (e.g., "connection(s)", "folder(s)")
}

export interface FormField {
  id: string
  label: string
  type: FieldType
  required: boolean
  placeholder?: string
  default?: any
  validation?: ValidationRule
  help_text?: string
  tooltip?: string  // Tooltip text to display on info icon hover
  // Type-specific
  rows?: number
  min?: number
  max?: number
  step?: number
  options?: SelectOption[]
  content?: string
  items?: any[]  // For 'list' type - array of items to display
  list_config?: ListDisplayConfig  // Configuration for how to display list items
}

export interface FormAction {
  label: string
  style: 'primary' | 'secondary' | 'danger'
  action: string
}

export interface FormRequestMessage {
  type: 'form_request'
  form_id: string
  title: string
  description?: string
  fields: FormField[]
  actions: FormAction[]
}

export interface FormStep {
  id: string
  title: string
  description?: string
  fields: FormField[]
}

export interface FormStepperMessage {
  type: 'form_stepper'
  form_id: string
  title: string
  description?: string
  steps: FormStep[]
  actions: Record<string, FormAction>
}

export interface FormSubmitRequest {
  type: 'form_submit'
  form_id: string
  data: Record<string, any>
}

export interface FormCancelRequest {
  type: 'form_cancel'
  form_id: string
}
