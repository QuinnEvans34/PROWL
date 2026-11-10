import { defineConfig } from '@playwright/test'

// Presentation-only fixture: no Python service, patient data or model inference.
export default defineConfig({
  testDir: './tests',
  testMatch: [/browser\/workspace\.spec\.js$/, /summary-browser\/summary\.spec\.js$/],
  outputDir: '../outputs/prowl/testing/toolbench-browser',
  workers: 1,
  retries: 0,
  use: {
    browserName: 'chromium',
    baseURL: 'http://127.0.0.1:5179',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run test:fixture',
    url: 'http://127.0.0.1:5179',
    reuseExistingServer: false,
    timeout: 30000,
  },
})
