// @vitest-environment node
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { it, expect, vi, afterEach } from 'vitest'
import retained from '../../configs/training-progress/lenovo-stunet-20261106.json'
import { trainingProgressPlugin } from '../trainingProgressPlugin.js'
let dir
afterEach(() => { vi.unstubAllEnvs(); if (dir) rmSync(dir, { recursive: true, force: true }); dir = null })
function middleware() { let h; trainingProgressPlugin().configureServer({ middlewares: { use: (_, handler) => { h = handler } } }); return h }
function call(h, url = '/', method = 'GET') {
  let body; const res = { statusCode: 200, setHeader: vi.fn(), end: v => { body = v } }
  h({ url, method }, res); return { status: res.statusCode, body, headers: res.setHeader }
}
it('returns a retained observation without claiming a live connection', () => {
  vi.stubEnv('PROWL_TRAINING_PROGRESS_FILE', '')
  const r = call(middleware()), d = JSON.parse(r.body)
  expect(d.snapshot.observed_at).toBe(retained.observed_at)
  expect(d.read_state).toBe('retained_snapshot'); expect(d.note).toContain('does not connect')
  expect(r.headers).toHaveBeenCalledWith('Cache-Control', 'no-store')
})
it('keeps valid data after a malformed, oversized or regressed local export', () => {
  dir = mkdtempSync(join(tmpdir(), 'prowl-progress-')); const file = join(dir, 'export.json')
  vi.stubEnv('PROWL_TRAINING_PROGRESS_FILE', file)
  const d = structuredClone(retained); d.run.step++; d.run.elapsed_seconds++
  d.observed_at = '2026-11-07T19:00:00Z'; writeFileSync(file, JSON.stringify(d))
  const h = middleware(); expect(JSON.parse(call(h).body).snapshot.run.step).toBe(d.run.step)
  for (const invalid of ['{partial', ' '.repeat(128 * 1024 + 1), JSON.stringify(retained)]) {
    writeFileSync(file, invalid); const result = JSON.parse(call(h).body)
    expect(result.snapshot).toEqual(d); expect(result.note).toContain('last verified')
  }
})
it('rejects source paths in requests, query overrides and writes; HEAD has no body', () => {
  const h = middleware()
  for (const [url, method] of [['/../../etc/passwd', 'GET'], ['/?file=/etc/passwd', 'GET'], ['/', 'POST']]) expect(call(h, url, method).status).toBe(404)
  expect(call(h, '/', 'HEAD').body).toBe('')
})
