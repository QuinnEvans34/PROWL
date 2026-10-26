import { expect, it, vi } from 'vitest'
import { serializeLiteratureCapture, downloadLiteratureCapture } from '../src/lib/literatureCapture.js'

it('bounds serialized UTF-8 bytes, not character count', () => {
  expect(() => serializeLiteratureCapture({request_id:'r', question:'q'}, {text:'漢'.repeat(400000)})).toThrow(/too large/)
})
it('downloads JSON and releases the temporary URL', () => {
  vi.useFakeTimers()
  const create = vi.fn(() => 'blob:test'), revoke = vi.fn()
  vi.stubGlobal('URL', {createObjectURL:create, revokeObjectURL:revoke})
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {
    expect(this.download).toBe('prowl-literature-capture.json')
    expect(this.href).toBe('blob:test')
  })
  try {
    downloadLiteratureCapture('{}\n')
    expect(create.mock.calls[0][0].type).toBe('application/json')
    expect(document.querySelector('a[download]')).toBeNull()
    vi.runAllTimers()
    expect(revoke).toHaveBeenCalledWith('blob:test')
  } finally { click.mockRestore(); vi.unstubAllGlobals(); vi.useRealTimers() }
})
