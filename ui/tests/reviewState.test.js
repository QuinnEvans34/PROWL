import { describe, expect, it } from 'vitest'
import { makeReviewState, reviewReducer } from '../src/lib/reviewState.js'
import { objectLabel, sourcesForEvidence, visibleSourcesForEvidence } from '../src/lib/viewerLayers.js'

describe('historical presentation reducer (not durable review persistence)', () => {
  it('starts unmarked cases in 3D Abdomen or uses Region for a crop-only study', () => {
    expect(makeReviewState()).toMatchObject({ viewMode: '3d', scene3d: 'full', interactionMode: 'rotate', evidenceMode: 'ct', selectedObject: null })
    expect(makeReviewState({ hasFullCt: false })).toMatchObject({ viewMode: '3d', scene3d: 'region' })
    expect(makeReviewState({ hasPrediction: true }).evidenceMode).toBe('prediction')
  })
  it('case change clears the previous case display state', () => {
    const old = { ...makeReviewState(), viewMode: '2d', scene3d: 'region', selectedObject: { anatomy: 'lesion' }, overlayOpacity: 0.1 }
    expect(reviewReducer(old, { type: 'CASE_CHANGED', hasPrediction: false })).toEqual(makeReviewState())
  })
  it('live prediction advances CT without wiping selected plane or opacity', () => {
    const old = { ...makeReviewState(), activePlane: 'axial', overlayOpacity: 0.1 }
    expect(reviewReducer(old, { type: 'PREDICTION_READY' })).toMatchObject({ evidenceMode: 'prediction', activePlane: 'axial', overlayOpacity: 0.1 })
    expect(old.evidenceMode).toBe('ct')
  })
  it('live prediction does not override a chosen comparison mode', () => {
    const old = { ...makeReviewState(), evidenceMode: 'overlap' }
    expect(reviewReducer(old, { type: 'PREDICTION_READY' })).toBe(old)
  })
  it.each([['3d', 'rotate'], ['2d', 'navigate']])('mode %s uses %s interaction', (value, interactionMode) => {
    expect(reviewReducer(makeReviewState(), { type: 'SET_VIEW_MODE', value })).toMatchObject({ viewMode: value, interactionMode, settingsOpen: false })
  })
  it('keeps Pan selected when switching review layouts', () => {
    const pan = { ...makeReviewState(), interactionMode: 'pan' }
    for (const value of ['2d', 'split', '3d']) {
      expect(reviewReducer(pan, { type: 'SET_VIEW_MODE', value })).toMatchObject({ viewMode: value, interactionMode: 'pan' })
    }
  })
  it('toggles a layer without mutating its input', () => {
    const old = makeReviewState()
    expect(reviewReducer(old, { type: 'TOGGLE_LAYER', layer: 'pred' }).layerVisibility.pred).toBe(false)
    expect(old.layerVisibility.pred).toBe(true)
  })
  it('makes the selected layer visible without changing the comparison filter', () => {
    const old = { ...makeReviewState(), evidenceMode: 'overlap', layerVisibility: { lesion: false, gt: false } }
    const object = { anatomy: 'lesion', source: 'gt' }
    expect(reviewReducer(old, { type: 'SELECT_OBJECT', value: object })).toMatchObject({
      selectedObject: object, anatomyFocus: 'all', sourceFocus: 'both', layerVisibility: { lesion: true, gt: true },
    })
  })
  it('exits inspection and leaves the current plane and source filter in place', () => {
    const old = {
      ...makeReviewState(), activePlane: 'coronal', sourceFocus: 'gt', focusTreatment: 'isolate',
      selectedObject: { anatomy: 'lesion', source: 'gt' },
    }
    expect(reviewReducer(old, { type: 'CLEAR_SELECTION' })).toEqual({
      ...old, selectedObject: null, focusTreatment: 'context',
    })
  })
  it('reset preserves evidence/view mode but resets focus and increments token', () => {
    const old = { ...makeReviewState(), viewMode: '3d', evidenceMode: 'overlap', anatomyFocus: 'lesion', resetToken: 2 }
    expect(reviewReducer(old, { type: 'RESET_VIEW' })).toMatchObject({ viewMode: '3d', evidenceMode: 'overlap', anatomyFocus: 'all', resetToken: 3, interactionMode: 'rotate' })
  })
  it('unknown actions leave state unchanged', () => {
    const old = makeReviewState()
    expect(reviewReducer(old, { type: 'UNKNOWN' })).toBe(old)
  })
})

describe('source presentation helpers', () => {
  it.each([['ct', []], ['prediction', ['pred']], ['truth', ['gt']], ['overlap', ['pred', 'gt']]])('%s exposes the expected source set', (mode, expected) => {
    expect(sourcesForEvidence(mode)).toEqual(expected)
  })
  it('layer visibility and difference mode suppress ordinary sources', () => {
    expect(visibleSourcesForEvidence('overlap', 'both', { pred: false, gt: true })).toEqual(['gt'])
    expect(visibleSourcesForEvidence('overlap', 'difference', { pred: true, gt: true })).toEqual([])
  })
  it('labels prediction, reference, and difference distinctly', () => {
    expect(objectLabel({ source: 'pred', anatomy: 'lesion' })).toBe('Prediction lesion')
    expect(objectLabel({ source: 'gt', anatomy: 'lesion' })).toBe('Reference lesion')
    expect(objectLabel({ source: 'difference', region: 'predOnly', anatomy: 'lesion' })).toBe('Prediction only · lesion')
  })
})
