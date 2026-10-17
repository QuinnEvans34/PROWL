import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { savedPredictionPlugin } from './savedPredictionPlugin.js'

// Static-first viewer, with an optional local fixture writer during development.
export default defineConfig({
  plugins: [savedPredictionPlugin(), react()],
  server: {
    host: '127.0.0.1', port: 5180, strictPort: true, open: true,
    proxy: { '/research-workflow': 'http://127.0.0.1:8015', '/research-answers': 'http://127.0.0.1:8014', '/research-evidence': 'http://127.0.0.1:8013', '/evidence-fixture': 'http://127.0.0.1:8011' },
  },
  build: {
    // Sites registers static files from the conventional client directory.
    // Keeping the Worker entry beside it lets the same bundle run locally
    // with `vite preview` and in the hosted Cloudflare environment.
    outDir: 'dist/client',
  },
})
