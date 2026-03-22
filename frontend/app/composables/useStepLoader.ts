/**
 * useStepLoader composable
 * 
 * Eliminates the repeated `$fetch(url, { headers: { Authorization: Bearer token } })`
 * boilerplate that was duplicated across all 5 stepper configuration files.
 */

import type { StepDefinition } from '~/types/stepper'

/**
 * Fetch a form schema from the backend and assign it to a step's formData.
 * 
 * @param url - Full URL to the form schema endpoint (e.g. `${context.baseUrl}/api/forms/...`)
 * @param token - Bearer auth token
 * @param step - The StepDefinition whose formData will be populated
 */
export async function loadStepSchema(
  url: string,
  token: string,
  step: StepDefinition
): Promise<void> {
  const formSchema = await $fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  step.formData = formSchema as any
}

/**
 * Composable wrapper — auto-imported by Nuxt.
 */
export const useStepLoader = () => ({ loadStepSchema })
