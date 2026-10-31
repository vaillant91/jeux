import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';
const base = process.env.PAGES_BASE_PATH || '/';
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base))
    throw Error('PAGES_BASE_PATH doit être / ou /nom-du-depot/.');
export default defineConfig({
    base,
    plugins: [VitePWA({
            registerType: 'prompt', injectRegister: false, includeAssets: ['favicon.svg', 'pwa-192.png', 'pwa-512.png'],
            manifest: { id: base, name: 'Défi ton pote', short_name: 'Défi ton pote', description: 'Arcade, campagne et atelier de parcours à partager.', theme_color: '#142e35', background_color: '#101d23', display: 'standalone', start_url: base, scope: base, icons: [{ src: 'pwa-192.png', sizes: '192x192', type: 'image/png' }, { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' }] },
            workbox: { cacheId: 'defi-ton-pote-' + base.replaceAll('/', '-'), globPatterns: ['**/*.{js,css,html,svg,png,webmanifest}'], navigateFallback: 'index.html', maximumFileSizeToCacheInBytes: 4 * 1024 * 1024 }
        })],
    build: { rollupOptions: { output: { manualChunks: { phaser: ['phaser'] } } } }
});
