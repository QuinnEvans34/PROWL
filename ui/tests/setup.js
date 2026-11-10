import { afterEach, beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })
// Unit/component tests must never fetch demo scans or call an inference service.
beforeEach(() => {
  // Some contract tests run in Node, where browser storage does not exist.
  try { if (typeof window !== 'undefined') window.localStorage?.clear() } catch { /* Storage may be disabled. */ }
  vi.stubGlobal('fetch', () => { throw new Error('Network forbidden in synthetic UI tests') })
})
