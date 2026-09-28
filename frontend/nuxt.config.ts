// Every /api/** request is forwarded to Flask, so the browser only ever talks
// to one origin and the auth cookie stays first-party.
const apiBase = (process.env.API_BASE || 'http://127.0.0.1:5000').replace(/\/$/, '')

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  css: ['~/assets/css/main.css'],

  app: {
    head: {
      title: 'ASCE · Service Cost Estimator',
      htmlAttrs: { lang: 'en' },
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Car repair cost estimates for Bangladesh.' },
        { name: 'theme-color', content: '#fdf8f6' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Bitter:wght@500;600;700&family=Hind+Siliguri:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap',
        },
      ],
    },
  },

  routeRules: {
    '/api/**': { proxy: `${apiBase}/api/**` },
  },
})
