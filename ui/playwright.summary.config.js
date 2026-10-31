import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir:'./tests/summary-browser',outputDir:'../outputs/prowl/testing/summary-browser',
  workers:1,retries:0,timeout:30000,
  use:{browserName:'chromium',baseURL:'http://127.0.0.1:5179',
    launchOptions:{args:['--disable-gpu']},trace:'retain-on-failure',screenshot:'only-on-failure'},
  webServer:{command:'npm run test:fixture',url:'http://127.0.0.1:5179',reuseExistingServer:false,timeout:30000},
})
