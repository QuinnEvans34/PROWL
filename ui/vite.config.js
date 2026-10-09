import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Static-first viewer, with an optional local fixture writer during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, open: true,
    proxy: { '/evidence-fixture': 'http://127.0.0.1:8011' },
  },
  build: {
    // Sites registers static files from the conventional client directory.
    // Keeping the Worker entry beside it lets the same bundle run locally
    // with `vite preview` and in the hosted Cloudflare environment.
    outDir: 'dist/client',
  },
})
