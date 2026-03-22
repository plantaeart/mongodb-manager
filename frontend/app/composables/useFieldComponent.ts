/**
 * useFieldComponent composable
 * 
 * Resolves the correct Vue component reference for a given form field type.
 * Extracted to eliminate the identical switch duplication that existed in
 * TerminalForm.vue and TerminalFormStepper.vue.
 */

import TerminalTextField from '~/components/Terminal/Forms/Fields/TerminalTextField.vue'
import TerminalPasswordField from '~/components/Terminal/Forms/Fields/TerminalPasswordField.vue'
import TerminalNumberField from '~/components/Terminal/Forms/Fields/TerminalNumberField.vue'
import TerminalCheckboxField from '~/components/Terminal/Forms/Fields/TerminalCheckboxField.vue'
import TerminalCheckboxListField from '~/components/Terminal/Forms/Fields/TerminalCheckboxListField.vue'
import TerminalReadonlyField from '~/components/Terminal/Forms/Fields/TerminalReadonlyField.vue'
import TerminalListField from '~/components/Terminal/Forms/Fields/TerminalListField.vue'
import TerminalSelectField from '~/components/Terminal/Forms/Fields/TerminalSelectField.vue'
import type { FormField } from '~/types/terminal'

/**
 * Returns the Vue component reference appropriate for the given field type.
 */
export function getFieldComponent(field: FormField) {
  switch (field.type) {
    case 'password':
      return TerminalPasswordField
    case 'number':
      return TerminalNumberField
    case 'checkbox':
      return TerminalCheckboxField
    case 'checkbox-list':
      return TerminalCheckboxListField
    case 'readonly':
      return TerminalReadonlyField
    case 'list':
      return TerminalListField
    case 'select':
      return TerminalSelectField
    case 'textarea':
      // TODO: Create TerminalTextAreaField when needed
      return TerminalTextField
    default:
      return TerminalTextField
  }
}

/**
 * Composable wrapper — auto-imported by Nuxt.
 */
export const useFieldComponent = () => ({ getFieldComponent })
