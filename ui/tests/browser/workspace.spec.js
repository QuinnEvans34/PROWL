import { test, expect } from '@playwright/test'

test('synthetic controls, case reset, and viewport baseline', async ({ page }, testInfo) => {
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/*', route => {
    const url = new URL(route.request().url())
    // Historical CSS imports a Google font. Keep this fixture offline with fallback fonts;
    // this explicitly does not qualify production font loading or pixel-identical layout.
    if (url.origin === 'https://fonts.googleapis.com' && url.pathname === '/css2') {
      return route.fulfill({ status: 200, contentType: 'text/css', body: '/* offline fixture fonts */' })
    }
    if (url.origin !== 'http://127.0.0.1:5179' || url.pathname.startsWith('/cases/')) {
      errors.push(`Forbidden request: ${url.origin}${url.pathname}`)
      return route.abort()
    }
    return route.continue()
  })
  await page.goto('/')
  await expect(page.getByRole('status', { name: 'Synthetic viewer stub' })).toBeVisible()
  await expect(page.getByRole('button', { name: /^Prediction/ })).toBeDisabled()
  const list = page.getByRole('complementary', { name: 'Study list' })
  if (await page.getByRole('button', { name: 'Collapse study list' }).isVisible()) {
    await page.getByRole('button', { name: 'Collapse study list' }).click()
  }
  // Collapsed list is visibility:hidden and inert, so it leaves the tab order.
  await expect(list).toHaveCSS('visibility', 'hidden')
  await page.getByRole('button', { name: 'Open study list' }).click()
  await expect(list).toHaveCSS('visibility', 'visible')
  await page.getByRole('button', { name: '3D', exact: true }).click()
  await expect(page.getByRole('button', { name: '3D', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await page.getByRole('button', { name: 'Switch synthetic case' }).click()
  await expect(page.getByRole('button', { name: '2D', exact: true })).toHaveAttribute('aria-pressed', 'true')
  // Named keyboard target: proves this control's keyboard path, not a full tab-order audit.
  await page.getByRole('button', { name: 'View settings', exact: true }).focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('button', { name: 'View settings', exact: true })).toHaveAttribute('aria-expanded', 'true')
  await page.getByRole('button', { name: 'Reset viewer' }).click()
  for (const [width, height] of [[1440, 900], [1280, 720], [1024, 768]]) {
    await page.setViewportSize({ width, height })
    await page.screenshot({ path: testInfo.outputPath(`synthetic-${width}.png`), fullPage: true })
  }
  expect(errors).toEqual([])
})
