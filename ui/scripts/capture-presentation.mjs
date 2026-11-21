// Capture presentation screenshots from the running Workbench on this Mac's GPU.
//
//   cd ui && npm run dev            # in one terminal (http://127.0.0.1:5180)
//   cd ui && node scripts/capture-presentation.mjs [ID ...]
//
// A browser window opens and clicks through each shot; PNGs (and the turntable WebM)
// land in ../presentation-assets/raw/. Display-only: nothing in the app or data changes.
// IDs: D1 C2 D4 D5 B1 D10 F4 B2 F1 D7 D3 A1 A2 C1 D8 D9 E2 F2 F3 (default: all)
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const BASE = process.env.PROWL_URL || 'http://127.0.0.1:5180'
const OUT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../presentation-assets/raw')
const ALL = ['D1', 'C2', 'D4', 'D5', 'B1', 'D10', 'F4', 'B2', 'F1', 'D7', 'D3', 'A1', 'A2', 'C1', 'D8', 'D9', 'E2', 'F2', 'F3']
const WANT = new Set(process.argv.slice(2).length ? process.argv.slice(2) : ALL)
const want = (...ids) => ids.some(id => WANT.has(id))
const HIDE_OVERLAYS = `.pw-viewer-help, .pw-structure-legend, .pw-hover-tag, .pw-snap-wrap, .pw-split__label, .pw-viewport-detail, .pw-viewport-scale, .tb-pane__header, .tb-pane__navigator { visibility: hidden !important; }`
mkdirSync(OUT, { recursive: true })

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

async function launch() {
  // A visible window gets the real GPU on macOS; HEADLESS=1 is for testing without a display.
  const headless = process.env.HEADLESS === '1'
  const args = headless
    ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    : ['--ignore-gpu-blocklist', '--enable-gpu-rasterization']
  const options = { headless, args }
  try { return await chromium.launch(options) } catch (error) {
    console.log('Playwright Chromium not installed; trying Google Chrome.', error.message.split('\n')[0])
    return chromium.launch({ ...options, channel: 'chrome' })
  }
}

const browser = await launch()
const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, acceptDownloads: true })
await context.addInitScript(() => { window.__PROWL_CAPTURE = true })
const page = await context.newPage()
const errors = []
page.on('pageerror', error => errors.push(String(error)))

async function clickText(text, scope = 'body', { starts = false, optional = false, timeout = 60000 } = {}) {
  const end = Date.now() + timeout
  while (Date.now() < end) {
    const ok = await page.evaluate(([scopeSel, label, prefix]) => {
      const root = document.querySelector(scopeSel) || document.body
      const el = [...root.querySelectorAll('button, a, [role=tab], summary')]
        .find(item => { const t = item.textContent.trim(); return prefix ? t.startsWith(label) : t === label })
      if (!el || el.disabled) return false
      el.click()
      return true
    }, [scope, text, starts])
    if (ok) return true
    if (optional) return false
    await sleep(400)
  }
  throw new Error(`Button not found: ${text}`)
}

async function clickLabel(label) {
  const ok = await page.evaluate(name => {
    const el = document.querySelector(`[aria-label="${name}"]`)
    if (!el || el.disabled) return false
    el.click()
    return true
  }, label)
  if (!ok) console.log(`  (skipped: ${label} not available)`)
}

async function settle(extra = 1500) {
  let stable = 0
  const end = Date.now() + 180000
  while (stable < 3 && Date.now() < end) {
    await sleep(700)
    const loading = await page.evaluate(() => document.body.innerText.includes('Loading prepared scan'))
    stable = loading ? 0 : stable + 1
  }
  await sleep(extra)
}

async function rect(selector, inset = 0) {
  return page.evaluate(([sel, pad]) => {
    const r = document.querySelector(sel).getBoundingClientRect()
    return { x: r.x + pad, y: r.y + pad, width: r.width - 2 * pad, height: r.height - 2 * pad }
  }, [selector, inset])
}

async function shot(name, clip) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), clip })
  console.log('saved', name)
}

async function openStudy(study, mode = '2D') {
  await page.goto(`${BASE}/workbench?study=${study}`)
  await page.waitForSelector('[aria-label="Viewer mode"]', { timeout: 60000 })
  await clickText(mode, '[aria-label="Viewer mode"]')
  await settle(2500)
}

// The layer-bar "Go to" buttons were retired (Nov 20). Studies open near the lesion;
// for an exact lesion slice, use inspectLesion(), which opens the measured slice.
async function goLesion() {
  if (await clickText('Lesion', '.pw-layerbar__goto', { optional: true })) {
    await settle(1000)
    if (await clickText('Exit inspection', 'body', { optional: true })) await settle(800)
  }
}

async function inspectLesion() {
  await clickText('Inspect measurement', 'body')
  await settle(2500)
}

async function toggleLayer(label, on) {
  const pressed = await page.evaluate(name => {
    const b = [...document.querySelectorAll('.pw-layerbar button')].find(e => e.textContent.trim().startsWith(name))
    return b ? b.getAttribute('aria-pressed') : null
  }, label)
  if (pressed === null) return
  if ((pressed === 'true') !== on) {
    await clickText(label, '.pw-layerbar', { starts: true })
    await settle(1200)
  }
}

async function threeD(study, zoomClicks, hidePanel = false) {
  await openStudy(study, '3D')
  if (hidePanel) await clickLabel('Hide assistant panel')
  await clickText('Surfaces', '[aria-label="3D scene"]')
  await settle(3000)
  for (let i = 0; i < zoomClicks; i += 1) { await clickLabel('Zoom in'); await sleep(400) }
  await sleep(2500)
}

const failed = []
async function step(ids, fn) {
  if (!ids.some(id => WANT.has(id))) return
  try { await fn() } catch (error) {
    failed.push(ids.join('/'))
    console.log(`FAILED ${ids.join('/')}: ${String(error.message || error).split('\n')[0]}`)
  }
}

try {
  await step(['D1'], async () => {
    await page.goto(`${BASE}/`)
    await sleep(3000)
    await shot('D1_studies_page')
  })

  await step(['C2', 'D2', 'D4', 'D5', 'B1', 'D10', 'F4', 'B2', 'F1', 'D7'], async () => {
    await openStudy('PanTS_00009005', '2D')
    await goLesion()
    await toggleLayer('Anatomy', true)
    await settle(3000)
    if (want('C2')) await shot('C2_workbench_overview')
    if (want('D4')) {
      await page.evaluate(() => document.querySelector('.pw-insight-card')?.scrollIntoView({ block: 'start' }))
      await sleep(800)
      await shot('D4_findings_cards_full')
      await shot('D4_findings_cards_panel', await rect('#pw-assistant'))
      const cards = await page.evaluate(() => [...document.querySelectorAll('.pw-insight-card')].slice(0, 2)
        .map(el => { const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height } }))
      if (cards[0]) await shot('D4a_card_lesion_characteristics', cards[0])
      if (cards[1]) await shot('D4b_card_vessel_relationship', cards[1])
    }
    if (want('D5')) {
      await clickText('Compare with reference', '.pw-layerbar')
      await settle(3000)
      await shot('D5_compare_with_reference_9005')
      await clickText('End comparison', '.pw-layerbar')
      await settle(1500)
    }
    await clickText('Axial', '[aria-label="Visible planes"]')
    await settle(2000)
    await goLesion()
    await page.addStyleTag({ content: HIDE_OVERLAYS })
    await toggleLayer('Anatomy', false)
    const pane = () => rect('.pw-toolbench-scene__planes')
    if (want('B1')) {
      await toggleLayer('Prediction', false)
      await shot('B1a_ct_no_overlay_9005', await pane())
      await toggleLayer('Prediction', true)
      await shot('B1b_ct_model_outline_9005', await pane())
    }
    if (want('D10')) {
      await toggleLayer('Confidence', true)
      await sleep(4000)
      await shot('D10_confidence_2d_9005', await pane())
      await toggleLayer('Confidence', false)
    }
    if (want('B2')) {
      await clickText('Compare with reference', '.pw-layerbar')
      await settle(3000)
      await shot('B2_both_outlines_9005', await pane())
      await clickText('End comparison', '.pw-layerbar')
      await settle(1500)
    }
    if (want('F4', 'F1')) {
      for (let i = 0; i < 5; i += 1) { await clickLabel('Zoom in axial'); await sleep(500) }
      await settle(1500)
      if (want('F4')) {
        await toggleLayer('Confidence', true)
        await sleep(4000)
        await shot('F4_confidence_zoomed_9005', await pane())
        await toggleLayer('Confidence', false)
      }
      if (want('F1')) {
        await clickText('Compare with reference', '.pw-layerbar')
        await settle(3000)
        {
          await clickText('Difference', '[aria-label="Compare source"]')
          await settle(2500)
          await shot('F1_difference_zoomed_9005', await pane())
        }
      }
    }
    if (want('D7')) {
      await clickText('Review summary')
      await sleep(3000)
      await shot('D7_review_summary_9005')
    }
  })

  await step(['D3'], async () => {
    await threeD('PanTS_00009005', 1)
    await shot('D3_3d_vessel_bands_9005')
  })
  await step(['A1'], async () => {
    await threeD('PanTS_00009005', 2, true)
    await page.addStyleTag({ content: HIDE_OVERLAYS })
    await sleep(1000)
    await shot('A1_raw_3d_9005', await rect('.pw-toolbench-scene__3d', 3))
  })
  await step(['A2'], async () => {
    await threeD('PanTS_00009016', 2, true)
    await page.addStyleTag({ content: HIDE_OVERLAYS })
    await sleep(1000)
    await shot('A2_raw_3d_9016', await rect('.pw-toolbench-scene__3d', 3))
  })
  await step(['C1'], async () => {
    await threeD('PanTS_00009005', 2, true)
    await page.addStyleTag({ content: HIDE_OVERLAYS })
    const download = page.waitForEvent('download', { timeout: 60000 })
    await clickLabel('Record turntable')
    const file = await download
    await file.saveAs(path.join(OUT, 'C1_turntable_9005.webm'))
    console.log('saved C1_turntable_9005.webm')
  })
  await step(['D8'], async () => {
    await openStudy('PanTS_00009005', '2D')
    await clickText('Curved', '[aria-label="Viewer mode"]')
    await page.waitForSelector('.pw-curved__image img', { timeout: 60000 })
    await sleep(2500)
    const box = await rect('.pw-curved__image')
    await page.mouse.move(box.x + box.width * 0.62, box.y + box.height * 0.5)
    await sleep(600)
    await shot('D8_curved_view_9005')
  })
  await step(['D9'], async () => {
    await openStudy('PanTS_00009005', '2D')
    await clickText('Edit outline', 'body', { starts: true })
    await page.waitForSelector('.pw-editor__canvas', { timeout: 60000 })
    await page.waitForFunction(() => !document.querySelector('.pw-editor__status'), null, { timeout: 120000 })
    await sleep(2000)
    await shot('D9_outline_editor_9005')
  })
  await step(['E2'], async () => {
    await page.goto(`${BASE}/training`)
    await sleep(5000)
    await shot('E2_training_page')
  })
  await step(['F2'], async () => {
    await openStudy('PanTS_00009220', '2D')
    await clickText('Show saved prediction', 'body', { starts: true, optional: true })
    await settle(2000)
    await goLesion()
    await shot('F2_false_positive_9220_workbench')
    await inspectLesion()
    await page.addStyleTag({ content: HIDE_OVERLAYS })
    await shot('F2_false_positive_9220_axial', await rect('.pw-toolbench-scene__planes'))
  })
  await step(['F3'], async () => {
    await openStudy('PanTS_00009687', '2D')
    await clickText('Show saved prediction', 'body', { starts: true, optional: true })
    await settle(2000)
    await clickText('Compare with reference', '.pw-layerbar')
    await settle(3000)
    await goLesion()
    await shot('F3_failure_small_lesion_9687_workbench')
    await inspectLesion()
    await page.addStyleTag({ content: HIDE_OVERLAYS })
    await shot('F3_failure_small_lesion_9687_axial', await rect('.pw-toolbench-scene__planes'))
  })
} finally {
  if (failed.length) console.log(`Shots that failed (rerun with these IDs): ${failed.join(' ')}`)
  console.log(errors.length ? `page errors:\n${errors.join('\n')}` : 'page errors: none')
  console.log(`Saved to ${OUT}`)
  await browser.close()
}
