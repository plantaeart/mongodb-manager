/**
 * useTerminalHttp
 * 
 * Handles all HTTP interactions for the terminal:
 * - Fetching form schemas from the backend
 * - Submitting form data
 * 
 * Extracted from TerminalService to satisfy SRP.
 * Fixes the bug where `backendUrl` was used instead of `apiUrl`.
 */

import { CommandStatus } from '~/enums'
import { getPostApiPathForCommand, FORM_ENDPOINT_COMMANDS } from '~/config/terminalForms'
import type { FormRequestMessage } from '~/types/terminal'
import type { TerminalCommand } from '~/enums'

export interface FetchFormResult {
  ok: true
  formData: FormRequestMessage
  formId: string
}

export interface FetchFormError {
  ok: false
  error: string
}

export interface SubmitFormResult {
  success: boolean
  output?: string[]
  error?: string
}

export const useTerminalHttp = () => {
  const runtimeConfig = useRuntimeConfig()

  /**
   * The canonical backend URL (from nuxt.config.ts public.apiUrl)
   */
  function getBaseUrl(): string {
    return runtimeConfig.public.apiUrl as string
  }

  /**
   * Fetch a form schema for a given command path.
   *
   * @param formPath - API path (e.g. 'connect/add')
   * @param token - Bearer auth token
   * @param commandIdPrefix - Used to generate a unique form_id
   * @param command - Originating terminal command
   */
  async function fetchForm(
    formPath: string,
    token: string,
    commandIdPrefix: number,
    command: string
  ): Promise<FetchFormResult | FetchFormError> {
    try {
      const baseUrl = getBaseUrl()
      const response = await fetch(`${baseUrl}/api/forms/${formPath}`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!response.ok) {
        return { ok: false, error: `Failed to fetch form: ${response.statusText}` }
      }

      const raw = await response.json() as any
      const formId = `form-${commandIdPrefix}`

      const formData: FormRequestMessage = {
        type: 'form_request',
        form_id: formId,
        command,
        title: raw.title,
        description: raw.description,
        step: raw.step,
        total_steps: raw.total_steps,
        fields: raw.fields,
        actions: raw.actions
      }

      return { ok: true, formData, formId }
    } catch (error) {
      return {
        ok: false,
        error: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }

  /**
   * Submit form data to the backend.
   *
   * @param command - Originating terminal command
   * @param data - Processed form data
   * @param token - Bearer auth token
   */
  async function submitFormData(
    command: string,
    data: Record<string, any>,
    token: string
  ): Promise<SubmitFormResult> {
    try {
      const baseUrl = getBaseUrl()
      const postApiPath = getPostApiPathForCommand(command)
      const hasFormEndpoint = postApiPath && FORM_ENDPOINT_COMMANDS.has(command as TerminalCommand)

      const endpoint = hasFormEndpoint
        ? `${baseUrl}/api/forms/${postApiPath}`
        : `${baseUrl}/api/commands/execute`
      const requestBody = hasFormEndpoint
        ? data
        : { command, params: data }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      if (result.success) {
        return {
          success: true,
          output: result.output
            ? result.output.split('\n').filter((line: string) => line.trim())
            : [result.message || 'Command executed successfully']
        }
      } else {
        return {
          success: false,
          error: result.error ?? result.message ?? 'Command failed'
        }
      }
    } catch (error) {
      return {
        success: false,
        error: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }
  }

  return {
    fetchForm,
    submitFormData
  }
}
