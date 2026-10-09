import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  root: fileURLToPath(new URL('./fixtures', import.meta.url)),
  publicDir: false,
  plugins: [{
    name: 'synthetic-viewer-only', enforce: 'pre',
    resolveId(source) {
      if (source.endsWith('/NiivueViewer.jsx')) return fileURLToPath(new URL('./fixtures/MockViewer.jsx', import.meta.url))
    },
  }, react()],
  server: { host: '127.0.0.1', port: 5179, strictPort: true, open: false,
    proxy: { '/evidence-fixture': 'http://127.0.0.1:8012' },
  },
})
