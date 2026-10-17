import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests/workflow-browser',
  outputDir: '../outputs/prowl/testing/workflow-browser',
  workers: 1, retries: 0,
  use: { browserName: 'chromium', baseURL: 'http://127.0.0.1:5179', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [{
    command: 'npm run test:fixture', url: 'http://127.0.0.1:5179', reuseExistingServer: false, timeout: 30000,
  }, {
    command: '../.venv-retrieval/bin/python ../tests/retrieval/helpers/workflow_fixture_server.py --output ../outputs/prowl/testing/workflow-fixtures',
    url: 'http://127.0.0.1:8015/research-workflow/health', reuseExistingServer: false, timeout: 30000,
  }],
})
