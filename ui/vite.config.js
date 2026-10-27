import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { localExpertPlugin } from './localExpertPlugin.js'
import { fileURLToPath } from 'node:url'
import { savedPredictionPlugin } from './savedPredictionPlugin.js'

// These public contracts are imported by the UI from outside its Vite root.
const evidenceContracts = [
  'guided-fixture-v1.json', 'guided-fixture-v2.json', 'evidence-wording-v1.json',
  'research-questions-v1.json', 'development-search-v1.json',
  'development-search-v3-records.json', 'source-facts-disease-v1.json',
  'development-volume-search-v1.json', 'source-facts-volume-v1.json',
  'volume-answer-v1.json', 'volume-answer-wording-v1.json',
  'development-measurement-search-v1.json', 'source-facts-measurement-v1.json',
  'measurement-answer-v1.json', 'measurement-answer-wording-v1.json',
  'natural-answer-v6.1.json', 'record-answer-v1.json', 'record-answer-wording-v1.json',
].map(name => fileURLToPath(new URL(`../configs/evidence/${name}`, import.meta.url)))

// Static-first viewer, with an optional local fixture writer during development.
export default defineConfig({
  plugins: [localExpertPlugin(), savedPredictionPlugin(), react()],
  server: {
    host: '127.0.0.1', port: 5180, strictPort: true, open: true,
    fs: { allow: [fileURLToPath(new URL('.', import.meta.url)), ...evidenceContracts] },
    proxy: { '/review-records': 'http://127.0.0.1:8018', '/scan-inference': 'http://127.0.0.1:8017', '/literature-search': 'http://127.0.0.1:8016', '/research-workflow': 'http://127.0.0.1:8015', '/research-answers': 'http://127.0.0.1:8014', '/research-evidence': 'http://127.0.0.1:8013', '/evidence-fixture': 'http://127.0.0.1:8011' },
  },
  build: {
    // Sites registers static files from the conventional client directory.
    // Keeping the Worker entry beside it lets the same bundle run locally
    // with `vite preview` and in the hosted Cloudflare environment.
    outDir: 'dist/client',
  },
})
