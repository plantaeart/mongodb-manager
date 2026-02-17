/**
 * Connection details response from API
 */
export interface ConnectionDetails {
  name: string
  uri: string
  description: string
  host: string
  port: number
  username: string
  password: string
  database: string
  auth_source: string
}

/**
 * Composable for fetching connection details
 * Used in Step 2 of connect update stepper to pre-populate form
 */
export const useConnectionDetails = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiUrl

  /**
   * Fetch connection details by name
   * @param name - Connection name
   * @returns Connection details with URI components
   */
  const fetchConnectionDetails = async (name: string): Promise<ConnectionDetails> => {
    const response = await $fetch<ConnectionDetails>(`${baseUrl}/api/forms/connection-details/${name}`, {
      credentials: 'include'
    })
    return response
  }

  return {
    fetchConnectionDetails
  }
}
