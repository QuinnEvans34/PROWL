import { describe, expect, it } from 'vitest'
import { sourceSliceAt, verifiedInspectionSource, viewportImageDetails } from '../src/lib/viewerImageDetails.js'

const affine = [[0, -3, 0, 7], [2, 0, 0, -9], [0, 0, 4, 11], [0, 0, 0, 1]]
const native = { kind: 'source', calibratedHu: true }
const prepared = { kind: 'prepared', legacyMillimeters: true }

function viewer({ units = 2, canvasWidth = 480, cssWidth = 240 } = {}) {
  return {
    volumes: [{ hdr: { affine, xyzt_units: units, dims: [3, 8, 9, 10] }, dimsRAS: [3, 9, 8, 10],
      cal_min: -100, cal_max: 300 }],
    canvas: { width: canvasWidth, clientWidth: cssWidth },
    screenSlices: [{ axCorSag: 0, leftTopWidthHeight: [canvasWidth, 0, -canvasWidth, 200],
      fovMM: [-120, 120], sliceFrac: 0.45 }],
  }
}

describe('viewport CT details', () => {
  it('uses the displayed tile, field of view and backing scale as the viewport zooms', () => {
    const nv = viewer()
    expect(viewportImageDetails(nv, 'axial', native)).toMatchObject({
      spacing: [2, 3, 4],
      scale: { millimeters: 50, widthPx: 100 },
      windowHu: { width: 400, center: 100 },
    })
    nv.screenSlices[0].fovMM[0] = -60
    expect(viewportImageDetails(nv, 'axial', native).scale).toEqual({ millimeters: 20, widthPx: 80 })
    nv.canvas.clientWidth = 120
    expect(viewportImageDetails(nv, 'axial', native).scale).toEqual({ millimeters: 50, widthPx: 100 })
  })

  it('shows prepared spacing for the legacy exporter without labelling normalized contrast as HU', () => {
    const old = viewer({ units: 0 })
    expect(viewportImageDetails(old, 'axial', prepared)).toMatchObject({ spacing: [2, 3, 4], windowHu: null })
    expect(viewportImageDetails(old, 'axial', native).scale).toBeNull()
    expect(viewportImageDetails(viewer(), 'axial', { kind: 'source' }).windowHu).toBeNull()
    expect(viewportImageDetails(viewer({ units: 1 }), 'axial', prepared).spacing).toBeNull()
  })
})

describe('source CT location and identity', () => {
  it('maps a physical location through RAS, snaps only depth and discloses a different plane', () => {
    const nv = viewer()
    nv.mm2frac = (point, volume, world) => {
      expect([volume, world]).toEqual([0, true])
      return [point[0] / 18, point[1] / 24, point[2] / 40]
    }
    expect(sourceSliceAt(nv, 'axial', [9, 12, 18])).toEqual({
      fractions: [0.5, 0.5, 0.45], index: 4, relation: 'exact',
    })
    expect(sourceSliceAt(nv, 'axial', [9, 12, 19])).toEqual({
      fractions: [0.5, 0.5, 0.45], index: 4, relation: 'nearest',
    })
    expect(sourceSliceAt(nv, 'sagittal', [9, 12, 18])).toEqual({
      fractions: [0.5, 0.5, 0.45], index: 4, relation: 'exact',
    })
    expect(sourceSliceAt(nv, 'axial', [9, 12, 41])).toBeNull()
  })

  it('requires the exact active prediction and its matching source CT evidence', () => {
    const ct = 'a'.repeat(64)
    const pred = 'b'.repeat(64)
    const result = {
      manifest: { case_id: 'study1', source_series_label: 'Abdomen CT', ct_intensity_units: 'HU',
        files: { ct: { content_sha256: ct }, pred: { content_sha256: pred } } },
      urls: { ct: 'blob:ct', pred: 'blob:pred' },
      measurement: { predictionSha256: pred, ctSha256: ct },
    }
    const selection = { studyId: 'study1', predictionSha256: pred }
    expect(verifiedInspectionSource(result, selection)).toEqual({ kind: 'source', calibratedHu: true, series: 'Abdomen CT' })
    expect(verifiedInspectionSource(result, { studyId: 'study1' })).toBeNull()
    expect(verifiedInspectionSource(result, { ...selection, studyId: 'study2' })).toBeNull()
    expect(verifiedInspectionSource(result, { ...selection, predictionSha256: 'c'.repeat(64) })).toBeNull()
    expect(verifiedInspectionSource({ ...result, measurement: { ...result.measurement, ctSha256: undefined } }, selection)).toBeNull()
  })
})
