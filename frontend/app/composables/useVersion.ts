/**
 * Version management composable
 * Reads version from package.json via runtime config
 */

export const useVersion = () => {
  const config = useRuntimeConfig()
  const version = config.public.appVersion || '1.0.0'
  
  return {
    version: computed(() => version),
    versionString: computed(() => `v${version}`)
  }
}
