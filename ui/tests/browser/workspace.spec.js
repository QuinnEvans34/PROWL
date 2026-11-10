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
  await expect(page.getByRole('status', { name: 'Synthetic viewer stub' })).toHaveCount(3)
  await expect(page.getByRole('status', { name: 'Synthetic viewer stub' }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: /^Prediction/ })).toBeDisabled()
  const list = page.getByRole('complementary', { name: 'Study list', includeHidden: true })
  if (await page.getByRole('button', { name: 'Collapse study list' }).isVisible()) {
    await page.getByRole('button', { name: 'Collapse study list' }).click()
  }
  // The hidden and inert list leaves both the layout and keyboard tab order.
  await expect(list).toBeHidden()
  await page.getByRole('button', { name: 'Open study list' }).click()
  await expect(list).toBeVisible()
  await page.getByRole('button', { name: '3D', exact: true }).click()
  await expect(page.getByRole('button', { name: '3D', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await page.getByRole('button', { name: 'Switch synthetic case' }).click()
  await expect(page.getByRole('button', { name: '2D', exact: true })).toHaveAttribute('aria-pressed', 'true')
  // Named keyboard target: proves this control's keyboard path, not a full tab-order audit.
  await page.getByRole('button', { name: 'View settings', exact: true }).focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('button', { name: 'View settings', exact: true })).toHaveAttribute('aria-expanded', 'true')
  await page.getByRole('button', { name: 'Reset viewer' }).click()
  await page.getByRole('button', { name: 'View settings', exact: true }).click()
  await page.getByRole('button', { name: 'Collapse study list' }).click()
  await page.getByRole('button', { name: '3D', exact: true }).click()
  await page.getByRole('button', { name: 'Close assistant panel' }).click()
  await page.setViewportSize({ width: 800, height: 600 })
  await page.getByRole('button', { name: 'Viewer controls', exact: true }).click()
  await page.getByRole('button', { name: 'Close viewer controls', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Viewer controls', exact: true })).toHaveCount(0)
  for (const [width, height] of [[1440, 900], [1280, 720], [1024, 768]]) {
    await page.setViewportSize({ width, height })
    await page.screenshot({ path: testInfo.outputPath(`synthetic-${width}.png`), fullPage: true })
  }
  expect(errors).toEqual([])
})

test('toolbench plane, resize and focus controls preserve mounted synthetic viewers', async ({ page }) => {
  await page.goto('/')
  const workspace = page.getByRole('main', { name: /Workbench/ })
  const viewers = page.getByRole('status', { name: 'Synthetic viewer stub' })
  await expect(viewers).toHaveCount(3)
  await page.getByRole('button', { name: 'Maximize coronal plane' }).click()
  await expect(viewers).toHaveCount(1)
  await expect(page.getByRole('button', { name: 'Coronal', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await page.getByRole('button', { name: 'Focus workspace', exact: true }).click()
  await expect(workspace).toHaveClass(/pw-toolbench--focus/)
  await expect(page.getByRole('complementary', { name: 'PROWL Assistant', includeHidden: true })).toBeHidden()
  await page.keyboard.press('Escape')
  await expect(workspace).not.toHaveClass(/pw-toolbench--focus/)
  await expect(viewers).toHaveCount(1)
  await page.getByRole('group', { name: 'Workspace layout' }).getByRole('button', { name: 'Restore layout', exact: true }).click()
  await expect(viewers).toHaveCount(3)
  const divider = page.getByRole('separator', { name: 'Primary pane size' })
  await divider.focus()
  await page.keyboard.press('Home')
  await expect(divider).toHaveAttribute('aria-valuenow', '40')
  await page.keyboard.press('End')
  await expect(divider).toHaveAttribute('aria-valuenow', '80')
  await page.reload()
  await expect(divider).toHaveAttribute('aria-valuenow', '80')
})

test('narrow screens keep drawers closed until requested', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/')
  const panel = page.getByRole('complementary', { name: 'PROWL Assistant', includeHidden: true })
  await expect(panel).toBeHidden()
  await page.getByRole('button', { name: 'Expert panel', exact: true }).click()
  await expect(panel).toBeVisible()
  await page.getByRole('button', { name: 'Close assistant panel' }).click()
  await expect(panel).toBeHidden()
  await page.getByRole('button', { name: 'Sagittal', exact: true }).click()
  await expect(page.getByRole('status', { name: 'Synthetic viewer stub' })).toHaveCount(1)
  const plane = page.getByRole('region', { name: 'Sagittal CT plane' })
  await expect(plane).toBeVisible()
})

test('full screen enters the native display mode and restores the selected plane', async ({ page }) => {
  await page.goto('/')
  const workspace = page.getByRole('main', { name: /Workbench/ })
  await page.getByRole('button', { name: 'Coronal', exact: true }).click()
  await page.getByRole('button', { name: 'Full screen', exact: true }).click()
  await expect(workspace).toHaveClass(/pw-toolbench--fullscreen/)
  expect(await page.evaluate(() => document.fullscreenElement?.classList.contains('pw-toolbench'))).toBe(true)
  const bounds = await workspace.boundingBox()
  const viewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight }))
  expect(bounds.x).toBe(0)
  expect(bounds.y).toBe(0)
  expect(bounds.width).toBe(viewport.width)
  expect(bounds.height).toBe(viewport.height)
  await page.getByRole('button', { name: 'Exit full screen', exact: true }).click()
  await expect(workspace).not.toHaveClass(/pw-toolbench--fullscreen/)
  expect(await page.evaluate(() => document.fullscreenElement)).toBeNull()
  await expect(page.getByRole('button', { name: 'Coronal', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('status', { name: 'Synthetic viewer stub' })).toHaveCount(1)
})
