// https://nuxt.com/docs/api/configuration/nuxt-config
import { readFileSync } from 'fs'
import { resolve } from 'path'

// Read version from package.json
const packageJson = JSON.parse(
  readFileSync(resolve(__dirname, 'package.json'), 'utf-8')
)

export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true },
  
  ssr: false,
  
  modules: ['@nuxt/ui', '@pinia/nuxt'],
  
  typescript: {
    typeCheck: true,
    strict: true, 
  },

  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8000',
      appVersion: packageJson.version
    }
  },
  
  css: ['~/assets/css/gruvbox.css'],
  
  app: {
    head: {
      title: 'MongoDB Manager',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'MongoDB Manager - Terminal UI' }
      ],
      link: [
        {
          rel: 'icon',
          type: 'image/x-icon',
          href: '/logo/favicon.ico'
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap'
        }
      ]
    }
  }
})
