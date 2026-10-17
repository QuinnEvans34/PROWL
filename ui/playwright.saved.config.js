import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests/saved-browser',
  outputDir: '../outputs/prowl/testing/saved-viewer-browser',
  workers: 1, retries: 0,
  use: { browserName: 'chromium', baseURL: 'http://127.0.0.1:5180', screenshot: 'only-on-failure' },
})
