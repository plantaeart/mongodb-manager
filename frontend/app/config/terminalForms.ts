/**
 * Terminal Forms Configuration
 * 
 * Centralized configuration for all interactive terminal forms.
 * This file defines the structure, fields, and validation rules for forms
 * displayed in the WebSocket terminal.
 */

import type { FormField, FormAction } from '~/types/terminal'

export interface FormMode {
  fields: FormField[]
  description?: string
}

export interface FormConfiguration {
  title: string
  description?: string
  modes?: Record<string, FormMode>
  fields?: FormField[]
  actions?: FormAction[]
}

/**
 * Terminal Forms Registry
 * 
 * Each key represents a command or form type.
 * Forms can have multiple modes (e.g., simple vs advanced)
 */
export const TERMINAL_FORMS: Record<string, FormConfiguration> = {
  /**
   * Connection Add Form
   * 
   * Two modes:
   * - Simple: Quick connection via MongoDB URI
   * - Advanced: Individual connection parameters
   */
  connect_add: {
    title: 'Add MongoDB Connection',
    description: 'Add a new MongoDB connection to manage',
    modes: {
      simple: {
        description: 'Quick setup using MongoDB connection URI',
        fields: [
          {
            id: 'name',
            label: 'Connection Name',
            type: 'text',
            required: true,
            placeholder: 'my-connection',
            help_text: 'Unique name for this connection'
          },
          {
            id: 'uri',
            label: 'MongoDB URI',
            type: 'text',
            required: true,
            placeholder: 'mongodb://username:password@host:port/database',
            help_text: 'Full MongoDB connection string',
            validation: {
              pattern: '^mongodb(\\+srv)?:\\/\\/.+',
              message: 'Must be a valid MongoDB URI starting with mongodb:// or mongodb+srv://'
            }
          },
          {
            id: 'description',
            label: 'Description',
            type: 'text',
            required: false,
            placeholder: 'Production database',
            help_text: 'Optional description for this connection'
          }
        ]
      },
      advanced: {
        description: 'Configure connection parameters individually',
        fields: [
          {
            id: 'name',
            label: 'Connection Name',
            type: 'text',
            required: true,
            placeholder: 'my-connection',
            help_text: 'Unique name for this connection'
          },
          {
            id: 'host',
            label: 'Host',
            type: 'text',
            required: true,
            placeholder: 'localhost',
            help_text: 'MongoDB server hostname or IP address'
          },
          {
            id: 'port',
            label: 'Port',
            type: 'number',
            required: true,
            default: 27017,
            min: 1,
            max: 65535,
            help_text: 'MongoDB server port (default: 27017)'
          },
          {
            id: 'username',
            label: 'Username',
            type: 'text',
            required: false,
            placeholder: 'admin',
            help_text: 'Leave empty for no authentication'
          },
          {
            id: 'password',
            label: 'Password',
            type: 'password',
            required: false,
            help_text: 'Required if username is provided'
          },
          {
            id: 'auth_source',
            label: 'Authentication Database',
            type: 'text',
            required: false,
            default: 'admin',
            placeholder: 'admin',
            help_text: 'Database where user credentials are stored'
          },
          {
            id: 'database',
            label: 'Database',
            type: 'text',
            required: false,
            placeholder: 'myapp',
            help_text: 'Default database to connect to'
          },
          {
            id: 'description',
            label: 'Description',
            type: 'text',
            required: false,
            placeholder: 'Production database',
            help_text: 'Optional description for this connection'
          }
        ]
      }
    },
    actions: [
      {
        label: 'Add Connection',
        style: 'primary',
        action: 'submit'
      },
      {
        label: 'Cancel',
        style: 'secondary',
        action: 'cancel'
      }
    ]
  },

  /**
   * Connection Remove Form
   * 
   * Displays list of connections with checkboxes for selection.
   * Supports multi-selection for batch deletion.
   */
  connect_remove: {
    title: 'Remove MongoDB Connection(s)',
    description: 'Select connection(s) to remove. This action cannot be undone.',
    fields: [
      {
        id: 'connections',
        label: 'Select connections to remove',
        type: 'checkbox',
        required: true,
        help_text: 'Select one or more connections to delete',
        // options will be populated dynamically from backend
        options: []
      }
    ],
    actions: [
      {
        label: 'Remove Selected',
        style: 'danger',
        action: 'submit'
      },
      {
        label: 'Cancel',
        style: 'secondary',
        action: 'cancel'
      }
    ]
  },

  /**
   * Connection List Form
   * 
   * Read-only display of all MongoDB connections.
   * Shows connection details in formatted panels.
   */
  connect_list: {
    title: 'MongoDB Connections',
    description: 'Configured MongoDB connections',
    fields: [
      {
        id: 'connections_list',
        label: '',
        type: 'list',
        required: false,
        // items will be populated dynamically from backend
        items: []
      }
    ],
    actions: [
      {
        label: 'Close',
        style: 'secondary',
        action: 'cancel'
      }
    ]
  }
}

/**
 * Get form configuration by key
 * 
 * @param formKey - The form identifier (e.g., 'connect_add', 'connect_remove')
 * @returns Form configuration or undefined if not found
 */
export function getFormConfig(formKey: string): FormConfiguration | undefined {
  return TERMINAL_FORMS[formKey]
}

/**
 * Get fields for a specific form mode
 * 
 * @param formKey - The form identifier
 * @param mode - The mode key (e.g., 'simple', 'advanced')
 * @returns Array of form fields or undefined if not found
 */
export function getFormFields(formKey: string, mode?: string): FormField[] | undefined {
  const config = TERMINAL_FORMS[formKey]
  if (!config) return undefined
  
  if (mode && config.modes) {
    return config.modes[mode]?.fields
  }
  
  return config.fields
}

/**
 * Check if a form supports multiple modes
 * 
 * @param formKey - The form identifier
 * @returns True if form has multiple modes
 */
export function isMultiModeForm(formKey: string): boolean {
  const config = TERMINAL_FORMS[formKey]
  return !!(config?.modes && Object.keys(config.modes).length > 1)
}

/**
 * Get available modes for a form
 * 
 * @param formKey - The form identifier
 * @returns Array of mode keys
 */
export function getFormModes(formKey: string): string[] {
  const config = TERMINAL_FORMS[formKey]
  return config?.modes ? Object.keys(config.modes) : []
}
