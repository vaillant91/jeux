import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  // The Pages site is published at https://vaillant91.github.io/jeux/.
  base: process.env.GITHUB_ACTIONS ? '/jeux/' : '/',
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Cosmo Dash — le défi des étoiles',
        short_name: 'Cosmo Dash',
        description: 'Un mini jeu spatial jouable hors ligne.',
        theme_color: '#0b1024',
        background_color: '#0b1024',
        display: 'standalone',
        orientation: 'any',
        start_url: process.env.GITHUB_ACTIONS ? '/jeux/' : '/',
        icons: [
          { src: 'pwa-192.svg', sizes: '192x192', type: 'image/svg+xml', purpose: 'any' },
          { src: 'pwa-512.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'any' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,ico,png,webmanifest}'],
        navigateFallback: 'index.html',
      },
    }),
  ],
})
