// @vitest-environment node
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { it, expect, vi, afterEach } from 'vitest'
import retained from '../../configs/training-progress/current.json'
import { trainingProgressPlugin } from '../trainingProgressPlugin.js'
let dir
afterEach(() => { vi.unstubAllEnvs(); if (dir) rmSync(dir, { recursive: true, force: true }); dir = null })
function middleware(options) { let h; trainingProgressPlugin(options).configureServer({ middlewares: { use: (_, handler) => { h = handler } } }); return h }
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
  d.observed_at = new Date(Date.parse(retained.observed_at) + 60000).toISOString(); writeFileSync(file, JSON.stringify(d))
  const h = middleware(); expect(JSON.parse(call(h).body).snapshot.run.step).toBe(d.run.step)
  for (const invalid of ['{partial', ' '.repeat(128 * 1024 + 1), JSON.stringify(retained)]) {
    writeFileSync(file, invalid); const result = JSON.parse(call(h).body)
    expect(result.snapshot).toEqual(d); expect(result.note).toContain('last verified')
    expect(result.read_state).toBe('local_snapshot')
  }
})
it('can read a valid configured export when the retained file is unavailable at startup', () => {
  dir = mkdtempSync(join(tmpdir(), 'prowl-progress-'))
  const file = join(dir, 'export.json')
  vi.stubEnv('PROWL_TRAINING_PROGRESS_FILE', file)
  const h = middleware({ retainedPath: join(dir, 'missing.json') })
  expect(call(h).status).toBe(503)
  writeFileSync(file, JSON.stringify(retained))
  const recovered = call(h)
  expect(recovered.status).toBe(200)
  expect(JSON.parse(recovered.body)).toMatchObject({ snapshot: retained, read_state: 'local_snapshot' })
})
it('rejects source paths in requests, query overrides and writes; HEAD has no body', () => {
  const h = middleware()
  for (const [url, method] of [['/../../etc/passwd', 'GET'], ['/?file=/etc/passwd', 'GET'], ['/', 'POST']]) expect(call(h, url, method).status).toBe(404)
  expect(call(h, '/', 'HEAD').body).toBe('')
})

it('admits a refreshed retained export without a server restart and refuses later score rewrites', () => {
  vi.stubEnv('PROWL_TRAINING_PROGRESS_FILE', '')
  dir = mkdtempSync(join(tmpdir(), 'prowl-retained-progress-')); const file = join(dir, 'current.json')
  writeFileSync(file, JSON.stringify(retained)); const h = middleware({ retainedPath: file })
  expect(JSON.parse(call(h).body).snapshot).toEqual(retained)
  const next = structuredClone(retained); next.observed_at = new Date(Date.parse(retained.observed_at) + 60000).toISOString()
  next.run.step++; next.run.elapsed_seconds++
  writeFileSync(file, JSON.stringify(next))
  expect(JSON.parse(call(h).body).snapshot).toEqual(next)
  const corrupt = structuredClone(next); corrupt.validations[0].lesion_dice = 0.99
  writeFileSync(file, JSON.stringify(corrupt))
  expect(JSON.parse(call(h).body).snapshot).toEqual(next)
  expect(JSON.parse(call(h).body).note).toContain('last verified')
})
