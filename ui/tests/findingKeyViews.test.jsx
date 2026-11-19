import React from 'react'
import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import FindingKeyViews from '../src/components/FindingKeyViews.jsx'
import {
  createFindingKeyView, exportFindingKeyView, importFindingKeyView, KEY_VIEWS_STORAGE_KEY,
  matchesKeyViewScope, readFindingKeyViews, saveFindingKeyView,
} from '../src/lib/findingKeyViews.js'

const scope = { studyId: 'SYNTHETIC_A', ctSha256: 'a'.repeat(64), predictionSha256: 'b'.repeat(64) }
const finding = { anatomy: 'lesion', id: 42, ordinal: 2 }
const view = {
  plane: 'axial', worldMm: [15.25, -117, 38.5], sliceIndex: 53,
  seriesKey: 'source', sourceCtSha256: 'c'.repeat(64),
  ctWindow: 'soft', ctRange: [-112, 279], pan2Dxyzmm: [33, -42, 10, 2.75],
  overlayMode: 'outline', overlayOpacity: 0.62, ctOpacity: 0.51,
  clipEnabled: true, clipDirection: 'backToFront', clipProgress: 24.5,
  scene3d: 'region', viewMode: 'inspect', showFull: false, show3dCalipers: true, showSliceIn3d: true,
  camera: { azimuth: 38, elevation: -9, scale: 1.6, pivot: [5, -78, 36] },
}

beforeEach(() => window.localStorage.clear())

describe('finding key view persistence', () => {
  it('retains the exact measured image identity and supported viewer state', () => {
    const record = createFindingKeyView(scope, finding, view)
    saveFindingKeyView(record)
    expect(readFindingKeyViews()).toEqual([record])
    expect(record).toMatchObject({ scope, finding, view })
    expect(matchesKeyViewScope(scope, record)).toBe(true)
    expect(matchesKeyViewScope({ ...scope, predictionSha256: 'c'.repeat(64) }, record)).toBe(false)
    expect(matchesKeyViewScope({ ...scope, ctSha256: 'c'.repeat(64) }, record)).toBe(false)
    expect(matchesKeyViewScope({ ...scope, manifestHash: 'd'.repeat(64) }, record)).toBe(false)
  })

  it('rejects invalid camera and positional values and ignores extraneous content on save', () => {
    expect(createFindingKeyView(scope, finding, { ...view, worldMm: [NaN, 0, 0] })).toBeNull()
    expect(createFindingKeyView(scope, finding, { ...view, camera: { ...view.camera, scale: 0 } })).toBeNull()
    expect(createFindingKeyView(scope, finding, { ...view, seriesKey: '/private/ct.nii.gz' })).toBeNull()
    window.localStorage.setItem(KEY_VIEWS_STORAGE_KEY, 'damaged record')
    expect(readFindingKeyViews()).toEqual([])
    const record = createFindingKeyView(scope, { ...finding, label: 'free text' }, { ...view, note: 'private note' })
    saveFindingKeyView({ ...record, reviewerNote: 'private note' })
    expect(window.localStorage.getItem(KEY_VIEWS_STORAGE_KEY)).not.toMatch(/private note|free text/)
  })

  it('exports the optional note to its explicit file and refuses an unsupported file or storage failure', () => {
    const record = createFindingKeyView(scope, finding, view)
    const text = exportFindingKeyView(record, 'Review this slice.')
    expect(importFindingKeyView(text)).toEqual({ keyView: record, reviewerNote: 'Review this slice.' })
    expect(() => importFindingKeyView(text.replace('"version": 1', '"version": 3'))).toThrow('supported PROWL key view')
    const denied = { getItem: () => null, setItem: () => { throw new Error('Quota exceeded') } }
    expect(() => saveFindingKeyView(record, denied)).toThrow('could not save the key view')
  })
})

describe('finding key view controls', () => {
  it('saves and reopens a captured view after remount, then blocks a changed prediction', async () => {
    const user = userEvent.setup()
    const capture = vi.fn(() => view)
    const onReopen = vi.fn(() => null)
    const app = render(<FindingKeyViews scope={scope} finding={finding} capture={capture} onReopen={onReopen} />)
    await user.click(screen.getByRole('button', { name: 'Save key view' }))
    expect(screen.getByRole('status').textContent).toContain('saved on this browser')
    expect(capture).toHaveBeenCalledOnce()
    app.unmount()
    const revised = render(<FindingKeyViews scope={scope} onReopen={onReopen} />)
    await user.click(screen.getByRole('button', { name: 'Reopen Predicted lesion 2 key view' }))
    expect(onReopen).toHaveBeenLastCalledWith(expect.objectContaining({ scope, finding, view }))
    revised.rerender(<FindingKeyViews scope={{ ...scope, predictionSha256: 'c'.repeat(64) }} onReopen={onReopen} />)
    await user.click(screen.getByRole('button', { name: 'Reopen Predicted lesion 2 key view' }))
    expect(onReopen).toHaveBeenCalledOnce()
    expect(screen.getByRole('status').textContent).toContain('different study, CT series, or prediction')
  })

  it('places the note only in the download and shows an explicit restore failure', async () => {
    const user = userEvent.setup()
    const onReopen = vi.fn(() => 'The original source series is unavailable.')
    const download = vi.fn()
    render(<FindingKeyViews scope={scope} finding={finding} capture={() => view} onReopen={onReopen} download={download} />)
    await user.click(screen.getByRole('button', { name: 'Save key view' }))
    await user.click(screen.getByText('Key view file'))
    await user.type(screen.getByLabelText(/Reviewer note for export/), 'Review source alignment.')
    await user.click(screen.getByRole('button', { name: 'Download key view' }))
    expect(importFindingKeyView(download.mock.calls[0][0]).reviewerNote).toBe('Review source alignment.')
    expect(window.localStorage.getItem(KEY_VIEWS_STORAGE_KEY)).not.toContain('Review source alignment.')
    await user.click(screen.getByRole('button', { name: 'Reopen Predicted lesion 2 key view' }))
    expect(screen.getByRole('status').textContent).toBe('The original source series is unavailable.')
  })

  it('rejects a portable file when the current study changes during its read', async () => {
    const user = userEvent.setup()
    const onReopen = vi.fn(() => null)
    const keyView = createFindingKeyView(scope, finding, view)
    const file = new File([exportFindingKeyView(keyView)], 'key-view.json')
    let complete
    Object.defineProperty(file, 'text', { value: () => new Promise(resolve => { complete = resolve }) })
    const { rerender } = render(<FindingKeyViews scope={scope} onReopen={onReopen} />)
    await user.click(screen.getByText('Key view file'))
    fireEvent.change(screen.getByLabelText('Open a key view file for this prediction'), { target: { files: [file] } })
    rerender(<FindingKeyViews scope={{ ...scope, studyId: 'SYNTHETIC_B' }} onReopen={onReopen} />)
    await act(async () => complete(exportFindingKeyView(keyView)))
    expect(onReopen).not.toHaveBeenCalled()
    expect(screen.getByRole('status').textContent).toContain('different study, CT series, or prediction')
  })
})
