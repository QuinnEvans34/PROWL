import { batchViewerUpdate, setMeshPropertyIfChanged } from '../lib/viewerUpdates.js'
import { useEffect, useRef, useState } from 'react'
import { DRAG_MODE, Niivue } from '@niivue/niivue'
import { LoaderCircle, TriangleAlert } from 'lucide-react'

import { verifyNativeVolumes } from '../lib/nativeGeometry.js'
import ViewerMeasurementOverlay from './ViewerMeasurementOverlay.jsx'
import ImagingViewportDetails from './ImagingViewportDetails.jsx'
import ViewerContourOverlay from './ViewerContourOverlay.jsx'
import { viewerSceneKey } from '../lib/viewerSceneKey.js'
import { ANTERIOR_CAMERA } from '../lib/viewerOrientation.js'
import { clientToBackingPx, pan2d, pan3dPivot, panPlaneAt, zoom2d, zoom3dFraming, zoomBox2d, zoomBox3dFraming, zoomToBounds2d } from '../lib/viewerZoom.js'
import { hasContourTile } from '../lib/viewerContour.js'
import { worldToNdc } from '../lib/viewerCaliperProjection.js'
export { viewerSceneKey } from '../lib/viewerSceneKey.js'

const BASE = '/cases'

const SOURCE_COLORS = {
  pred: {
    pancreas: [38, 197, 166],
    lesion: [249, 99, 99],
  },
  gt: {
    pancreas: [56, 189, 248],
    lesion: [251, 191, 36],
  },
}

const REFERENCE_STROKES = { pancreas: '#38bdf8', lesion: '#fbbf24' }

const DIFFERENCE_COLORS = {
  agreement: [196, 181, 253],
  predOnly: [244, 63, 94],
  gtOnly: [251, 191, 36],
}

const CT_WINDOWS = {
  soft: { cal_min: 0.08, cal_max: 0.72 },
  contrast: { cal_min: 0.16, cal_max: 0.6 },
  wide: { cal_min: 0, cal_max: 1 },
}

const PLANE_AXIS = {
  sagittal: 0,
  coronal: 1,
  axial: 2,
}

const PLANE_META = {
  axial: ['Axial', 'Top-down view'],
  coronal: ['Coronal', 'Front view'],
  sagittal: ['Sagittal', 'Side view'],
}

const LABEL_BOUNDS_CACHE = new WeakMap()

function clamp255(value) {
  return Math.max(0, Math.min(255, Math.round(value)))
}

function effectiveCtOpacity(ctOpacity, clip) {
  if (!clip?.enabled) return ctOpacity
  const progress = Math.max(0, Math.min(100, Number(clip?.progress) || 0))
  return progress >= 99.5 ? 0 : ctOpacity
}

function anatomyAlpha(anatomy, {
  anatomyFocus,
  focusTreatment,
  selectedObject,
  source,
}) {
  if (selectedObject) {
    const isSelected = selectedObject.source === source && selectedObject.anatomy === anatomy
    if (isSelected) return 255
    if (focusTreatment === 'isolate') return 0
  }

  if (anatomyFocus === 'all') return anatomy === 'pancreas' ? 188 : 255
  if (anatomyFocus === anatomy) return 255
  if (focusTreatment === 'isolate') return 0
  return anatomy === 'pancreas' ? 36 : 82
}

function labelColormap(source, presentation) {
  const colors = SOURCE_COLORS[source]
  const sourceScale = (
    presentation.sourceFocus === 'pred' || presentation.sourceFocus === 'gt'
  ) && presentation.sourceFocus !== source ? 0.18 : 1
  const pancreasAlpha = presentation.showPancreas
    ? anatomyAlpha('pancreas', { ...presentation, source }) * sourceScale
    : 0
  const lesionAlpha = presentation.showLesion
    ? anatomyAlpha('lesion', { ...presentation, source }) * sourceScale
    : 0

  return {
    R: [0, colors.pancreas[0], colors.lesion[0]],
    G: [0, colors.pancreas[1], colors.lesion[1]],
    B: [0, colors.pancreas[2], colors.lesion[2]],
    A: [0, clamp255(pancreasAlpha), clamp255(lesionAlpha)],
    I: [0, 1, 2],
    labels: ['Background', 'Pancreas', 'Lesion'],
  }
}

function differenceColormap({ selectedObject, anatomy, focusTreatment }) {
  const selectedRegion = selectedObject?.source === 'difference'
    && selectedObject.anatomy === anatomy
    ? selectedObject.region
    : null
  const alpha = (region) => {
    if (selectedRegion === region) return 255
    if (selectedRegion && focusTreatment === 'isolate') return 0
    return region === 'agreement' ? 205 : 255
  }
  return {
    R: [0, DIFFERENCE_COLORS.agreement[0], DIFFERENCE_COLORS.predOnly[0], DIFFERENCE_COLORS.gtOnly[0]],
    G: [0, DIFFERENCE_COLORS.agreement[1], DIFFERENCE_COLORS.predOnly[1], DIFFERENCE_COLORS.gtOnly[1]],
    B: [0, DIFFERENCE_COLORS.agreement[2], DIFFERENCE_COLORS.predOnly[2], DIFFERENCE_COLORS.gtOnly[2]],
    A: [0, alpha('agreement'), alpha('predOnly'), alpha('gtOnly')],
    I: [0, 1, 2, 3],
    labels: ['Background', 'Agreement', 'Prediction only', 'Reference only'],
  }
}

function voxelToWorld(volume, voxel) {
  const affine = volume?.hdr?.affine
  if (!Array.isArray(affine) || !Array.isArray(affine[0])) return null

  const [x, y, z] = voxel
  const world = [
    affine[0][0] * x + affine[0][1] * y + affine[0][2] * z + affine[0][3],
    affine[1][0] * x + affine[1][1] * y + affine[1][2] * z + affine[1][3],
    affine[2][0] * x + affine[2][1] * y + affine[2][2] * z + affine[2][3],
  ]
  return world.every(Number.isFinite) ? world : null
}

function labelCentroidMM(volume, requestedLabel = 1) {
  const image = volume?.img
  const dims = volume?.hdr?.dims
  if (!image || !dims || dims.length < 4) return null

  const nx = Number(dims[1])
  const ny = Number(dims[2])
  const nz = Number(dims[3])
  const voxelCount = nx * ny * nz
  if (!Number.isFinite(voxelCount) || voxelCount <= 0 || image.length < voxelCount) return null

  let count = 0
  let sumX = 0
  let sumY = 0
  let sumZ = 0
  let foregroundCount = 0
  let foregroundX = 0
  let foregroundY = 0
  let foregroundZ = 0

  for (let index = 0; index < voxelCount; index += 1) {
    const value = Math.round(Number(image[index]))
    if (value <= 0) continue

    const x = index % nx
    const yz = Math.floor(index / nx)
    const y = yz % ny
    const z = Math.floor(yz / ny)
    foregroundCount += 1
    foregroundX += x
    foregroundY += y
    foregroundZ += z

    if (value === requestedLabel) {
      count += 1
      sumX += x
      sumY += y
      sumZ += z
    }
  }

  if (count > 0) {
    return voxelToWorld(volume, [sumX / count, sumY / count, sumZ / count])
  }
  if (requestedLabel === 1 && foregroundCount > 0) {
    return voxelToWorld(volume, [
      foregroundX / foregroundCount,
      foregroundY / foregroundCount,
      foregroundZ / foregroundCount,
    ])
  }
  return null
}

function volumeCenterMM(volume) {
  const dims = volume?.hdr?.dims
  if (!dims || dims.length < 4) return null
  return voxelToWorld(volume, [
    (Number(dims[1]) - 1) / 2,
    (Number(dims[2]) - 1) / 2,
    (Number(dims[3]) - 1) / 2,
  ])
}

function labelBounds(volume, requestedLabel) {
  if (!volume) return null
  const cached = LABEL_BOUNDS_CACHE.get(volume)
  if (cached?.has(requestedLabel)) return cached.get(requestedLabel)

  const image = volume?.img
  const dims = volume?.hdr?.dims
  if (!image || !dims || dims.length < 4) return null

  const nx = Number(dims[1])
  const ny = Number(dims[2])
  const nz = Number(dims[3])
  const voxelCount = nx * ny * nz
  if (!Number.isFinite(voxelCount) || voxelCount <= 0 || image.length < voxelCount) return null

  const min = [nx, ny, nz]
  const max = [-1, -1, -1]
  for (let index = 0; index < voxelCount; index += 1) {
    if (Math.round(Number(image[index])) !== requestedLabel) continue
    const x = index % nx
    const yz = Math.floor(index / nx)
    const y = yz % ny
    const z = Math.floor(yz / ny)
    min[0] = Math.min(min[0], x)
    min[1] = Math.min(min[1], y)
    min[2] = Math.min(min[2], z)
    max[0] = Math.max(max[0], x)
    max[1] = Math.max(max[1], y)
    max[2] = Math.max(max[2], z)
  }
  const bounds = max[0] < 0 ? null : { min, max }
  const nextCache = cached || new Map()
  nextCache.set(requestedLabel, bounds)
  LABEL_BOUNDS_CACHE.set(volume, nextCache)
  return bounds
}

export function navigationSnapshot(nv, maskVolume) {
  // Crosshair fractions describe NiiVue's displayed RAS grid, which can have a
  // different axis order from the file header (notably in native CT packages).
  const dims = nv?.volumes?.[0]?.dimsRAS || nv?.volumes?.[0]?.hdr?.dims
  const crosshair = nv?.scene?.crosshairPos
  if (!dims || dims.length < 4 || !crosshair) return null

  const totals = {
    sagittal: Math.max(1, Number(dims[1])),
    coronal: Math.max(1, Number(dims[2])),
    axial: Math.max(1, Number(dims[3])),
  }
  // NiiVue texture fractions span voxel edges; the center of voxel i is
  // (i + 0.5) / dimension, including the first and last slice.
  const indices = Object.fromEntries(Object.entries(PLANE_AXIS).map(([plane, axis]) => [plane,
    Math.max(0, Math.min(totals[plane] - 1, Math.round(Number(crosshair[axis]) * totals[plane] - 0.5))),
  ]))
  const ranges = {}
  for (const [anatomy, labelValue] of [['pancreas', 1], ['lesion', 2]]) {
    const bounds = labelBounds(maskVolume, labelValue)
    ranges[anatomy] = null
    if (!bounds) continue
    // Label bounds are file voxels. Transform their corners into the displayed
    // grid before using them as anatomical slice ranges.
    const displayBounds = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] }
    for (const x of [bounds.min[0], bounds.max[0]]) {
      for (const y of [bounds.min[1], bounds.max[1]]) {
        for (const z of [bounds.min[2], bounds.max[2]]) {
          const world = voxelToWorld(maskVolume, [x, y, z])
          const fraction = world && typeof nv.mm2frac === 'function' ? nv.mm2frac(world, 0, true) : null
          if (!fraction || !Array.from(fraction).slice(0, 3).every(Number.isFinite)) continue
          for (const [plane, axis] of Object.entries(PLANE_AXIS)) {
            const index = Math.max(0, Math.min(totals[plane] - 1, Math.round(fraction[axis] * totals[plane] - 0.5)))
            displayBounds.min[axis] = Math.min(displayBounds.min[axis], index)
            displayBounds.max[axis] = Math.max(displayBounds.max[axis], index)
          }
        }
      }
    }
    if (displayBounds.min.every(Number.isFinite)) {
      ranges[anatomy] = Object.fromEntries(Object.entries(PLANE_AXIS).map(([plane, axis]) => [plane, [displayBounds.min[axis], displayBounds.max[axis]]]))
    }
  }
  return { indices, totals, ranges, fractions: Array.from(crosshair).slice(0, 3) }
}

function captureViewState(nv) {
  if (!nv?.scene?.crosshairPos) return null
  return {
    crosshair: Array.from(nv.scene.crosshairPos),
    pan2Dxyzmm: Array.from(nv.scene.pan2Dxyzmm || [0, 0, 0, 1]),
    azimuth: Number(nv.scene.renderAzimuth),
    elevation: Number(nv.scene.renderElevation),
    scale: Number(nv.scene.volScaleMultiplier),
    pivot3D: Array.isArray(nv.pivot3D) ? [...nv.pivot3D] : null,
    ctRange: [nv.volumes?.[0]?.cal_min, nv.volumes?.[0]?.cal_max],
  }
}

function inspectedPlane(nv, plane, snapshot, calipers, bounds) {
  const axis = PLANE_AXIS[plane]
  const total = snapshot.totals[plane]
  if (!Number.isInteger(axis) || !total || !calipers) return
  const fractionsAt = xyz => Array.from(nv.mm2frac(xyz, 0, true) || [])
  const indexAt = fraction => Math.max(0, Math.min(total - 1, Math.round(fraction * total - 0.5)))
  const measured = fractionsAt(calipers.anchorWorldMm)[axis]
  if (measured >= 0 && measured <= 1) snapshot.measuredIndex = indexAt(measured)
  if (bounds?.length) {
    const values = bounds.map(point => fractionsAt(point)[axis])
    if (values.every(Number.isFinite)) {
      const first = Math.max(0, Math.ceil(Math.min(...values) * total - 0.5001))
      const last = Math.min(total - 1, Math.floor(Math.max(...values) * total - 0.4999))
      if (first <= last) snapshot.inspectionRange = [first, last]
    }
  }
  const [x, y] = [0, 1, 2].filter(index => index !== axis)
  const worldAt = frac => Array.from(nv.frac2mm(frac, 0, true) || []).slice(0, 3)
  snapshot.worldMm = worldAt(snapshot.fractions)
  snapshot.planeWorldCorners = [[0, 0], [1, 0], [1, 1], [0, 1]].map(([i, j]) => {
    const fraction = [...snapshot.fractions]
    fraction[x] = i
    fraction[y] = j
    return worldAt(fraction)
  })
}

function restoreViewState(nv, view, mode) {
  if (!view) return false
  if (Array.isArray(view.crosshair) && view.crosshair.length >= 3) {
    nv.scene.crosshairPos = new Float32Array(view.crosshair.slice(0, 3))
  }
  if (Array.isArray(view.pan2Dxyzmm) && view.pan2Dxyzmm.length >= 4) {
    nv.scene.pan2Dxyzmm = new Float32Array(view.pan2Dxyzmm.slice(0, 4))
  }
  if (mode === '3d') {
    if (Number.isFinite(view.azimuth) && Number.isFinite(view.elevation)) {
      nv.scene.renderAzimuth = view.azimuth
      nv.scene.renderElevation = view.elevation
    }
    if (Number.isFinite(view.scale)) nv.scene.volScaleMultiplier = view.scale
    if (Array.isArray(view.pivot3D) && view.pivot3D.length >= 3) {
      nv.pivot3D = view.pivot3D.slice(0, 3)
    }
  }
  return true
}

function zoom3d(nv, factor) {
  const scale = Number(nv.scene.volScaleMultiplier)
  if (!Number.isFinite(factor) || factor <= 0 || !Number.isFinite(scale) || scale <= 0) return
  const nextScale = Math.max(0.45, Math.min(4, scale * factor))
  if (nextScale !== scale) nv.setScale(nextScale)
}

function renderView(nv) {
  const viewport = nv.screenSlices?.find(tile => tile.axCorSag === nv.sliceTypeRender)?.leftTopWidthHeight
  if (!viewport) return null
  const [left, top, width, height] = viewport
  if (!(width > 0 && height > 0)) return null
  const [matrix] = nv.calculateMvpMatrix(null, viewport, nv.scene.renderAzimuth, nv.scene.renderElevation)
  const inverse = matrix && invert4(matrix)
  if (!inverse) return null
  return {
    viewport, matrix,
    viewPoint: ([x, y]) => unproject(inverse, 2 * (x - left) / width - 1, 1 - 2 * (y - top) / height, 0),
  }
}

function apply3dFraming(nv, orbitCentreRef, framing) {
  if (!framing) return
  orbitCentreRef.current = framing.pivot
  nv.setScale(framing.scale)
}

function lesionFraming3d(nv, bounds) {
  const view = renderView(nv)
  if (!view || bounds?.length !== 8) return null
  const projected = bounds.map(point => worldToNdc(view.matrix, point))
  if (projected.some(point => !point)) return null
  const factor = Math.min(...[0, 1].map(axis => {
    const coordinates = projected.map(point => point[axis])
    return 1.3 / (Math.max(...coordinates) - Math.min(...coordinates))
  }))
  const centre = [0, 1, 2].map(axis => bounds.reduce((sum, point) => sum + point[axis], 0) / bounds.length)
  return zoom3dFraming(nv.scene.volScaleMultiplier, centre, factor)
}

function focusOnWorldPoint(nv, worldMM, mode) {
  if (!worldMM) return false
  const fraction = nv.mm2frac(worldMM, 0, true)
  if (!fraction || !Array.from(fraction).every(Number.isFinite)) return false

  nv.scene.crosshairPos = new Float32Array(Array.from(fraction, (value) => (
    Math.min(1, Math.max(0, value))
  )))
  if (mode === '3d') nv.pivot3D = [...worldMM]
  return true
}

function clearMeshes(nv) {
  ;(nv.meshes || []).slice().forEach((mesh) => {
    try {
      nv.removeMesh(mesh)
    } catch {
      // A mesh can already be gone while NiiVue is switching cases.
    }
  })
}

function semanticFromLocation(location, visibleSources, differenceMode) {
  const values = Array.isArray(location?.values) ? location.values : []
  if (differenceMode) {
    for (const labelValue of [2, 3, 1]) {
      const match = values.find((value) => (
        typeof value?.name === 'string'
        && value.name.startsWith('diff-')
        && Math.round(Number(value.value)) === labelValue
      ))
      if (match) {
        return {
          source: 'difference',
          anatomy: match.name.replace('diff-', '').split('.')[0],
          region: {
            1: 'agreement',
            2: 'predOnly',
            3: 'gtOnly',
          }[labelValue],
        }
      }
    }
  }
  const priority = [...visibleSources].reverse()

  for (const labelValue of [2, 1]) {
    for (const source of priority) {
      const match = values.find((value) => (
        (
          value?.name === source
          || value?.name === `${source}.nii.gz`
          || value?.name?.startsWith(`${source}.`)
        )
        && Math.round(Number(value.value)) === labelValue
      ))
      if (match) {
        return {
          source,
          anatomy: labelValue === 2 ? 'lesion' : 'pancreas',
        }
      }
    }
  }
  return null
}

// Reference surfaces drawn over a visible prediction use NiiVue's Outline shader:
// a glassy rim instead of a second solid surface that z-fights with the first.
const SLICE_TYPE_KEYS = { 0: 'axial', 1: 'coronal', 2: 'sagittal' }

// "All 3" uses a hero layout: axial large, coronal and sagittal stacked beside it
// (or below it in a tall viewer). A single row of three left most of a normal
// workstation viewer empty. Very wide viewers keep the original row.
function setPlaneLayout(nv, activePlane) {
  const view = captureViewState(nv)
  const sliceType = {
    axial: nv.sliceTypeAxial,
    coronal: nv.sliceTypeCoronal,
    sagittal: nv.sliceTypeSagittal,
    multiplanar: nv.sliceTypeMultiplanar,
  }[activePlane] ?? nv.sliceTypeMultiplanar
  const width = nv.canvas?.clientWidth || 0
  const height = nv.canvas?.clientHeight || 0
  const aspect = height > 0 ? width / height : 0
  if (activePlane !== 'multiplanar' || !aspect || aspect > 2.4 || typeof nv.setCustomLayout !== 'function') {
    if (typeof nv.clearCustomLayout === 'function') nv.clearCustomLayout()
    nv.setSliceType(sliceType)
    restoreViewState(nv, view, '2d')
    return
  }
  nv.setSliceType(sliceType)
  nv.setCustomLayout(aspect >= 1.25
    ? [
        { sliceType: nv.sliceTypeAxial, position: [0, 0, 0.6, 1] },
        { sliceType: nv.sliceTypeCoronal, position: [0.6, 0, 0.4, 0.5] },
        { sliceType: nv.sliceTypeSagittal, position: [0.6, 0.5, 0.4, 0.5] },
      ]
    : [
        { sliceType: nv.sliceTypeAxial, position: [0, 0, 1, 0.6] },
        { sliceType: nv.sliceTypeCoronal, position: [0, 0.6, 0.5, 0.4] },
        { sliceType: nv.sliceTypeSagittal, position: [0.5, 0.6, 0.5, 0.4] },
      ])
  restoreViewState(nv, view, '2d')
}

// Where NiiVue actually drew each 2D tile, in CSS pixels, so the plane labels
// sit on their own image whatever the layout.
function planeTilesFrom(nv) {
  const ratio = nv.uiData?.dpr || window.devicePixelRatio || 1
  return (nv.screenSlices || [])
    .filter((slice) => SLICE_TYPE_KEYS[slice.axCorSag] && Array.isArray(slice.leftTopWidthHeight))
    .map((slice) => {
      const [left, top, width] = slice.leftTopWidthHeight
      return { plane: SLICE_TYPE_KEYS[slice.axCorSag], left: left / ratio, top: top / ratio, width: width / ratio }
    })
}

function invert4(m) {
  const [a00, a01, a02, a03, a10, a11, a12, a13, a20, a21, a22, a23, a30, a31, a32, a33] = Array.from(m)
  const b00 = a00 * a11 - a01 * a10; const b01 = a00 * a12 - a02 * a10; const b02 = a00 * a13 - a03 * a10
  const b03 = a01 * a12 - a02 * a11; const b04 = a01 * a13 - a03 * a11; const b05 = a02 * a13 - a03 * a12
  const b06 = a20 * a31 - a21 * a30; const b07 = a20 * a32 - a22 * a30; const b08 = a20 * a33 - a23 * a30
  const b09 = a21 * a32 - a22 * a31; const b10 = a21 * a33 - a23 * a31; const b11 = a22 * a33 - a23 * a32
  let det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06
  if (!det) return null
  det = 1 / det
  return [
    (a11 * b11 - a12 * b10 + a13 * b09) * det, (a02 * b10 - a01 * b11 - a03 * b09) * det,
    (a31 * b05 - a32 * b04 + a33 * b03) * det, (a22 * b04 - a21 * b05 - a23 * b03) * det,
    (a12 * b08 - a10 * b11 - a13 * b07) * det, (a00 * b11 - a02 * b08 + a03 * b07) * det,
    (a32 * b02 - a30 * b05 - a33 * b01) * det, (a20 * b05 - a22 * b02 + a23 * b01) * det,
    (a10 * b10 - a11 * b08 + a13 * b06) * det, (a01 * b08 - a00 * b10 - a03 * b06) * det,
    (a30 * b04 - a31 * b02 + a33 * b00) * det, (a21 * b02 - a20 * b04 - a23 * b00) * det,
    (a11 * b07 - a10 * b09 - a12 * b06) * det, (a00 * b09 - a01 * b07 + a02 * b06) * det,
    (a31 * b01 - a30 * b03 - a32 * b00) * det, (a20 * b03 - a21 * b01 + a22 * b00) * det,
  ]
}

function unproject(inverse, x, y, z) {
  const out = [0, 0, 0, 0]
  for (let i = 0; i < 4; i += 1) out[i] = inverse[i] * x + inverse[4 + i] * y + inverse[8 + i] * z + inverse[12 + i]
  return out[3] ? [out[0] / out[3], out[1] / out[3], out[2] / out[3]] : null
}

// 3D click picking against the surfaces themselves. NiiVue's depth pick lands on the
// CT or the cut plane, which fails in "Masks only" (no CT left to hit). Instead cast the
// click ray through the render matrices and find surface vertices within a few mm of it.
// A lesion hit wins over the surrounding pancreas, since the lesion is drawn through it.
function pickSurfaceAtClick(nv, event, entries, toleranceMm = 3) {
  const tile = (nv.screenSlices || []).find((slice) => slice.axCorSag === 4)
  if (!tile || typeof nv.calculateMvpMatrix !== 'function') return null
  const rect = nv.canvas.getBoundingClientRect()
  const ratio = nv.uiData?.dpr || window.devicePixelRatio || 1
  const [left, top, width, height] = tile.leftTopWidthHeight
  const px = (event.clientX - rect.left) * ratio
  const py = (event.clientY - rect.top) * ratio
  const [mvp] = nv.calculateMvpMatrix(null, tile.leftTopWidthHeight, nv.scene.renderAzimuth, nv.scene.renderElevation)
  const inverse = mvp ? invert4(mvp) : null
  if (!inverse) return null
  const ndcX = (2 * (px - left)) / width - 1
  const ndcY = 1 - (2 * (py - top)) / height
  const near = unproject(inverse, ndcX, ndcY, -1)
  const far = unproject(inverse, ndcX, ndcY, 1)
  if (!near || !far) return null
  const dir = [far[0] - near[0], far[1] - near[1], far[2] - near[2]]
  const length = Math.hypot(...dir)
  if (!length) return null
  const u = dir.map((value) => value / length)
  let best = null
  entries.forEach((entry) => {
    const points = entry.mesh.pts
    if (!entry.mesh.visible || entry.mesh.opacity <= 0.02 || !points?.length) return
    for (let i = 0; i < points.length; i += 3) {
      const vx = points[i] - near[0]; const vy = points[i + 1] - near[1]; const vz = points[i + 2] - near[2]
      const along = vx * u[0] + vy * u[1] + vz * u[2]
      if (along < 0 || along > length) continue
      const perp = Math.hypot(vx - along * u[0], vy - along * u[1], vz - along * u[2])
      if (perp > toleranceMm) continue
      const lesion = entry.anatomy === 'lesion'
      if (!best || (lesion && !best.lesion) || (lesion === best.lesion && along < best.along)) {
        best = { entry, along, lesion, point: [points[i], points[i + 1], points[i + 2]] }
      }
    }
  })
  return best ? { ...best.entry, point: best.point, ray: { near, direction: u, along: best.along, length } } : null
}

// Surface meshes can move slightly with smoothing. Keep the existing mesh hit
// priority, but give component selection a native lesion voxel, not a guessed
// closest component. Try the actual click ray locally around the surface hit;
// a verified hit vertex also works when grazing the edge of the outline.
function lesionVoxelAtSurface(volume, picked) {
  const affine = volume?.hdr?.affine
  const dims = volume?.hdr?.dims
  const image = volume?.img
  if (!affine || !dims || !image) return null
  const inverse = invert4(Array.from({ length: 16 }, (_, n) => affine[n % 4]?.[Math.floor(n / 4)]))
  if (!inverse) return null
  const voxelCenter = (world) => {
    const voxel = unproject(inverse, ...world)?.map(v => Math.floor(v + 0.5))
    if (!voxel?.every((v, axis) => Number.isInteger(v) && v >= 0 && v < dims[axis + 1])) return null
    const [x, y, z] = voxel
    return image[x + dims[1] * (y + dims[2] * z)] === 2 ? voxelToWorld(volume, voxel) : null
  }
  const { near, direction, along, length } = picked.ray
  const rate = Math.max(...[0, 1, 2].map(axis => Math.abs(direction[0] * inverse[axis]
    + direction[1] * inverse[axis + 4] + direction[2] * inverse[axis + 8])))
  const steps = Math.max(12, Math.min(128, Math.ceil(12 * rate)))
  for (let n = 0; n <= steps; n += 1) {
    for (const sign of n ? [-1, 1] : [1]) {
      const depth = along + sign * n * 3 / steps
      if (depth < 0 || depth > length) continue
      const point = voxelCenter(near.map((v, i) => v + direction[i] * depth))
      if (point) return point
    }
  }
  return voxelCenter(picked.point)
}

// NiiVue ray-casts every loaded volume in 3D even at zero opacity. In "Masks only"
// nothing of the CT is visible, so skip that pass for this viewer instance: it was
// the bulk of each 3D frame (about 7 ms down to 0.5 ms in a measured orbit).
const skipImage3D = () => {}
function setVolumeRendering(nv, enabled) {
  if (enabled) delete nv.drawImage3D
  else nv.drawImage3D = skipImage3D
}

// The peel runs along the anatomical anterior/posterior axis. Each shortcut
// reveals the near side of the pancreas with a small margin past its surface.
function peelRevealPercentages(nv, meshes) {
  const unavailable = { frontToBack: null, backToFront: null }
  const pancreas = meshes.find((entry) => entry.anatomy === 'pancreas'
    && entry.source !== 'difference' && entry.mesh.extentsMin && entry.mesh.extentsMax)
  if (!pancreas || typeof nv.sceneExtentsMinMax !== 'function') return unavailable
  const [lo, hi, range] = nv.sceneExtentsMinMax()
  const span = Number(range?.[1])
  if (!Number.isFinite(span) || span <= 0) return unavailable
  const percent = (distance) => Number.isFinite(distance)
    ? Math.max(1, Math.min(99, Math.round((distance / span + 0.03) * 100)))
    : null
  return {
    frontToBack: percent(hi?.[1] - pancreas.mesh.extentsMax[1]),
    backToFront: percent(pancreas.mesh.extentsMin[1] - lo?.[1]),
  }
}

function applyPeel(nv, clip) {
  nv.setClipPlane([clip?.enabled ? clip.depth : 2, clip?.azimuth ?? 0, clip?.elevation ?? 0])
}

// NiiVue recomputes its 3D pivot from the scene bounds on every frame, so rotation is
// always about the scan centre. Wrapping setPivot3D on this instance lets a chosen
// point (double-clicked surface) become the orbit centre until Fit or Reset.
function installOrbitCentre(nv, centreRef) {
  const base = Object.getPrototypeOf(nv).setPivot3D
  if (typeof base !== 'function') return
  nv.setPivot3D = function setPivot3DWithCentre() {
    base.call(this)
    if (centreRef.current) this.pivot3D = [...centreRef.current]
  }
}

function meshShaderFor(entry, { isSelected, renderedSources, sourceFocus, anatomyLighting }) {
  if (isSelected) return anatomyLighting ? 'Diffuse' : 'Toon'
  if (entry.source === 'gt' && renderedSources.includes('pred') && sourceFocus !== 'gt') return 'Outline'
  return 'Hemispheric'
}

// The full abdomen is framed as a whole (NiiVue orbits the scene centre, not the
// pancreas), so it gets a gentle fixed zoom; the cropped scenes fit the surfaces.
const FULL_SCAN_SCALE = 1.0

// Leave space around cropped surfaces and cap automatic magnification.
// Users can still zoom in explicitly; Fit shows the full scene.
function surfaceFitScale(nv) {
  const visible = (nv.meshes || []).filter((mesh) => mesh.visible && mesh.extentsMin && mesh.extentsMax)
  if (!visible.length || typeof nv.sceneExtentsMinMax !== 'function') return null
  const scene = nv.sceneExtentsMinMax()
  const sceneRange = Math.max(...[0, 1, 2].map((axis) => Number(scene?.[2]?.[axis]) || 0))
  const lo = [0, 1, 2].map((axis) => Math.min(...visible.map((mesh) => mesh.extentsMin[axis])))
  const hi = [0, 1, 2].map((axis) => Math.max(...visible.map((mesh) => mesh.extentsMax[axis])))
  const meshRange = Math.max(...[0, 1, 2].map((axis) => hi[axis] - lo[axis]))
  if (!Number.isFinite(sceneRange) || !Number.isFinite(meshRange) || meshRange <= 0) return null
  return Math.max(1, Math.min(1.8, (0.85 * sceneRange) / meshRange))
}

function meshOpacity({
  anatomy,
  source,
  visible,
  anatomyFocus,
  focusTreatment,
  hasSelection,
  isSelected,
  overlayOpacity,
  sourceFocus,
}) {
  if (!visible) return 0
  if (isSelected) return 1
  if (hasSelection && focusTreatment === 'isolate') return 0
  const sourceScale = (sourceFocus === 'pred' || sourceFocus === 'gt') && sourceFocus !== source
    ? 0.16
    : 1
  if (anatomyFocus !== 'all' && anatomyFocus !== anatomy) {
    if (focusTreatment === 'isolate') return 0
    return (anatomy === 'pancreas' ? 0.12 : 0.3) * sourceScale
  }
  const base = anatomy === 'pancreas' ? 0.68 : 1
  return Math.max(0, Math.min(1, base * (0.65 + overlayOpacity * 0.5) * sourceScale))
}

export default function NiivueViewer({
  caseData,
  assetUrls = null,
  nativeGeometry = null,
  nativeCtOnly = false,
  ctRange = null,
  sources = ['pred'],
  visibleSources = null,
  mode = '2d',
  showFull = false,
  overlayOpacity = 0.3,
  ctOpacity = 0.18,
  ctWindow = 'soft',
  showPancreas = true,
  showLesion = true,
  anatomyFocus = 'all',
  sourceFocus = 'both',
  differenceMode = false,
  enableDifferenceAssets = false,
  focusTreatment = 'context',
  selectedObject = null,
  selectedLesionWorldMm = null,
  measurementCalipers = null,
  measurementAnatomy = 'lesion',
  overlayMode = 'fill',
  imageDetails = null,
  sliceLocatorCorners = null,
  capturePlaneLocation = false,
  inspectionBounds = null,
  onViewHandle = null,
  anatomyLighting = false,
  onSelectObject = null,
  activePlane = 'multiplanar',
  interactionMode = 'navigate',
  framingLocked = false,
  wheelZoom = false,
  navigationCommand = null,
  onNavigationChange = null,
  onZoomChange = null,
  syncCrosshair = null,
  syncWindow = null,
  onWindowChange = null,
  showPlaneLabels = true,
  onPeelReveal = null,
  clip = null,
  resetToken = 0,
  compact = false,
  guided = false,
  label = 'Medical image viewer',
}) {
  const canvasRef = useRef(null)
  const nvRef = useRef(null)
  const registryRef = useRef({
    volumeIndexes: new Map(),
    volumes: new Map(),
    differenceVolumeIndexes: new Map(),
    differenceVolumes: new Map(),
    meshes: new Map(),
  })
  const locationRef = useRef(null)
  const pointerStartRef = useRef(null)
  const loadedSceneKeyRef = useRef('')
  const expectedSceneKeyRef = useRef('')
  const currentSceneRef = useRef(null)
  const sceneLoadChainRef = useRef(Promise.resolve())
  const savedViewsRef = useRef(new Map())
  const latestCrosshairWorldRef = useRef(new Map())
  const handledResetTokenRef = useRef(resetToken)
  const handledNavigationCommandRef = useRef(null)
  const previousClipEnabledRef = useRef(Boolean(clip?.enabled))
  const clipFrameRef = useRef(null)
  const navigationFrameRef = useRef(null)
  const pendingNavigationRef = useRef(null)
  const lastNavigationSignatureRef = useRef('')
  const interactiveRef = useRef({
    mode,
    framingLocked,
    wheelZoom,
    interactionMode,
    onZoomChange,
    onSelectObject,
    onNavigationChange,
    onWindowChange,
    visibleSources: visibleSources || sources,
    differenceMode,
    inspectionPlane: capturePlaneLocation ? activePlane : null,
    measurementCalipers,
    inspectionBounds,
  })
  const lastFocusedObjectRef = useRef('')
  const [state, setState] = useState({ status: 'loading', message: 'Preparing viewer' })
  const [sceneVersion, setSceneVersion] = useState(0)
  const [planeTiles, setPlaneTiles] = useState([])
  const [zoomBox, setZoomBox] = useState(null)
  const orbitCentreRef = useRef(null)

  const renderedSources = visibleSources || sources
  const sceneKey = viewerSceneKey({ caseData, assetUrls, sources, mode, showFull, enableDifferenceAssets })
  expectedSceneKeyRef.current = sceneKey

  function publishZoom(nv) {
    const { onZoomChange: notifyZoom, mode: currentMode } = interactiveRef.current
    if (!notifyZoom || !loadedSceneKeyRef.current || loadedSceneKeyRef.current !== expectedSceneKeyRef.current) return
    const scale = currentMode === '3d' ? nv.scene.volScaleMultiplier : nv.scene.pan2Dxyzmm?.[3]
    if (Number.isFinite(scale) && scale > 0) notifyZoom(scale)
  }

  function publishNavigation(nv, { immediate = false, origin = 'interaction' } = {}) {
    const maskVolume = registryRef.current.volumes.get('pred')
      || registryRef.current.volumes.get('gt')
      || registryRef.current.volumes.values().next().value
    const snapshot = navigationSnapshot(nv, maskVolume)
    if (!snapshot) return
    snapshot.sceneKey = loadedSceneKeyRef.current
    snapshot.origin = origin
    const { inspectionPlane, measurementCalipers: calipers, inspectionBounds: bounds } = interactiveRef.current
    if (inspectionPlane) inspectedPlane(nv, inspectionPlane, snapshot, calipers, bounds)
    const signature = [
      snapshot.indices.sagittal,
      snapshot.indices.coronal,
      snapshot.indices.axial,
      snapshot.totals.sagittal,
      snapshot.totals.coronal,
      snapshot.totals.axial,
      ...snapshot.fractions.map((value) => Number(value).toFixed(6)),
      snapshot.measuredIndex,
      snapshot.inspectionRange?.join(','),
    ].join(':')
    if (signature === lastNavigationSignatureRef.current) return

    const commit = () => {
      navigationFrameRef.current = null
      const pending = pendingNavigationRef.current
      pendingNavigationRef.current = null
      if (!pending || pending.signature === lastNavigationSignatureRef.current) return
      lastNavigationSignatureRef.current = pending.signature
      interactiveRef.current.onNavigationChange?.(pending.snapshot)
    }

    pendingNavigationRef.current = { signature, snapshot }
    if (immediate) {
      if (navigationFrameRef.current !== null) {
        window.cancelAnimationFrame(navigationFrameRef.current)
      }
      commit()
      return
    }
    if (navigationFrameRef.current === null) {
      navigationFrameRef.current = window.requestAnimationFrame(commit)
    }
  }

  useEffect(() => {
    interactiveRef.current = {
      mode,
      framingLocked,
      wheelZoom,
      interactionMode,
      onZoomChange,
      onSelectObject,
      onNavigationChange,
      onWindowChange,
      visibleSources: renderedSources,
      differenceMode,
      inspectionPlane: capturePlaneLocation ? activePlane : null,
      measurementCalipers,
      inspectionBounds,
    }
  }, [mode, framingLocked, wheelZoom, interactionMode, onZoomChange, onSelectObject, onNavigationChange, onWindowChange, renderedSources.join('|'), differenceMode, capturePlaneLocation, activePlane, measurementCalipers, inspectionBounds])

  useEffect(() => { setZoomBox(null) }, [interactionMode, framingLocked, sceneKey])

  useEffect(() => {
    if (!canvasRef.current) return undefined

    const canvas = canvasRef.current
    const nv = new Niivue({
      backColor: [0.024, 0.026, 0.029, 1],
      show3Dcrosshair: false,
      isColorbar: false,
      multiplanarShowRender: 0,
      // ROW (3): keep axial/coronal/sagittal in one row so the plane labels below
      // always sit over the matching view. AUTO switched to a 2x2 grid in tall viewers.
      multiplanarLayout: 3,
      clipPlaneColor: [0, 0, 0, 0],
      isClipPlanesCutaway: true,
      isClipAllVolumes: false,
      meshXRay: 0.22,
    })

    nv.attachToCanvas(canvas)
    installOrbitCentre(nv, orbitCentreRef)
    nv.overlayOutlineWidth = 1.15
    nv.onLocationChange = (location) => {
      locationRef.current = location
      if (interactiveRef.current.mode === '2d') publishNavigation(nv)
    }
    nv.onIntensityChange = (volume) => {
      if (interactiveRef.current.mode !== '2d' || !loadedSceneKeyRef.current) return
      const ct = nv.volumes?.[0]
      if (volume && volume !== ct) return
      if (!Number.isFinite(ct?.cal_min) || !Number.isFinite(ct?.cal_max)) return
      interactiveRef.current.onWindowChange?.({
        sceneKey: loadedSceneKeyRef.current,
        range: [Number(ct.cal_min), Number(ct.cal_max)],
      })
    }
    nvRef.current = nv

    // While the 3D view is being dragged or zoomed with the CT visible, render at
    // half the device pixel ratio (a quarter of the pixels) and restore full
    // resolution when the gesture ends. Only on high-DPI screens; meshes-only
    // scenes are cheap and keep full resolution.
    let lowResActive = false
    let wheelTimer = null
    let restoreTimer = null
    let pointerHeld = false
    let pinchDistance = null
    let pinching = false
    let boxGesture = null
    let panGesture = null
    function setLowResolution(active) {
      const native = window.devicePixelRatio || 1
      if (active === lowResActive) return
      if (active && (interactiveRef.current.mode !== '3d' || native <= 1 || Object.prototype.hasOwnProperty.call(nv, 'drawImage3D'))) return
      lowResActive = active
      nv.opts.forceDevicePixelRatio = active ? Math.max(1, native / 2) : 0
      nv.resizeListener()
    }
    function pulseLowResolution() {
      setLowResolution(true)
      window.clearTimeout(wheelTimer)
      wheelTimer = window.setTimeout(() => { if (!pointerHeld) setLowResolution(false) }, 220)
    }
    function canZoom() {
      const { mode, framingLocked } = interactiveRef.current
      return !(mode === '2d' && framingLocked) && nv.volumes?.[0]
        && loadedSceneKeyRef.current && loadedSceneKeyRef.current === expectedSceneKeyRef.current
    }
    function zoomBy(factor, clientX, clientY) {
      const point = clientToBackingPx(canvas, clientX, clientY)
      if (interactiveRef.current.mode === '3d') {
        const view = point && renderView(nv)
        if (view) {
          const framing = zoom3dFraming(nv.scene.volScaleMultiplier, nv.pivot3D, factor, view.viewport, view.viewPoint, point)
          pulseLowResolution()
          apply3dFraming(nv, orbitCentreRef, framing)
        } else {
          pulseLowResolution()
          zoom3d(nv, factor)
        }
      } else zoom2d(nv, factor, point)
      publishZoom(nv)
    }
    function handleWheel(event) {
      const { mode, wheelZoom } = interactiveRef.current
      if (!wheelZoom) {
        if (mode === '3d') pulseLowResolution()
        return
      }
      // NiiVue's listener can advance the 2D slice or the active 3D clip plane.
      // Capture the gesture before either behavior runs.
      event.preventDefault()
      event.stopImmediatePropagation()
      const { deltaMode, deltaX, deltaY } = event
      if (boxGesture || panGesture || !canZoom() || !deltaY || Math.abs(deltaX) > Math.abs(deltaY)) return
      const unit = deltaMode === 1 ? 16 : deltaMode === 2 ? canvas.clientHeight : 1
      const delta = Math.max(-120, Math.min(120, deltaY * unit))
      zoomBy(Math.exp(-delta * 0.003), event.clientX, event.clientY)
    }
    function handlePinch(event) {
      if (!interactiveRef.current.wheelZoom || (event.touches.length < 2 && !pinching)) return
      event.preventDefault()
      event.stopImmediatePropagation()
      if (panGesture) {
        panGesture = null
        pointerStartRef.current = null
      }
      pinching = true
      const first = event.touches[0]
      const second = event.touches[1]
      if (!second) {
        pinchDistance = null
        return
      }
      const distance = Math.hypot(second.clientX - first.clientX, second.clientY - first.clientY)
      if (!boxGesture && canZoom() && pinchDistance > 0 && distance > 0) {
        zoomBy(distance / pinchDistance, (first.clientX + second.clientX) / 2, (first.clientY + second.clientY) / 2)
      }
      pinchDistance = distance
    }
    function endPinch(event) {
      pinchDistance = null
      if (event.touches.length === 0) pinching = false
    }
    function handleTouchStart(event) {
      if (panToolActive() && event.touches.length === 1 && !pinching) {
        event.preventDefault()
        event.stopImmediatePropagation()
        return
      }
      handlePinch(event)
    }
    function handleTouchMove(event) {
      if (panToolActive() && event.touches.length === 1 && !pinching) {
        event.preventDefault()
        event.stopImmediatePropagation()
        return
      }
      if (interactiveRef.current.mode !== '3d' || event.touches.length !== 1 || pinching) {
        handlePinch(event)
        return
      }
      // NiiVue's single-touch move starts a clip-plane drag even in rotate mode.
      event.preventDefault()
      event.stopImmediatePropagation()
      if (usesCustomDrag() || !canZoom()) return
      const rect = canvas.getBoundingClientRect()
      const touch = event.touches[0]
      nv.mouseMove(touch.clientX - rect.left, touch.clientY - rect.top)
    }
    function suppressClipShortcut(event) {
      if (interactiveRef.current.mode !== '3d'
        || ![nv.opts.clipPlaneHotKey, nv.opts.cycleClipPlaneHotKey].includes(event.code)) return
      event.preventDefault()
      event.stopImmediatePropagation()
    }
    function suppressSliceShortcut(event) {
      const { mode, wheelZoom } = interactiveRef.current
      if (mode !== '2d' || !wheelZoom) return
      const crosshairKey = ['KeyH', 'KeyJ', 'KeyK', 'KeyL'].includes(event.code)
        || (event.ctrlKey && ['KeyU', 'KeyD'].includes(event.code))
      if (!crosshairKey && !['ArrowLeft', 'ArrowRight'].includes(event.code)) return
      event.preventDefault()
      event.stopImmediatePropagation()
    }
    function endGesture() {
      // After NiiVue has processed its own mouseup at the gesture's resolution.
      pointerHeld = false
      window.clearTimeout(restoreTimer)
      restoreTimer = window.setTimeout(() => setLowResolution(false), 0)
    }

    function cancelBox() {
      if (!boxGesture) return
      boxGesture = null
      setZoomBox(null)
    }
    function boxToolActive() {
      return interactiveRef.current.interactionMode === 'box-zoom'
    }
    function panToolActive() {
      const { mode, interactionMode, framingLocked } = interactiveRef.current
      return interactionMode === 'pan' && (mode === '3d' || !framingLocked)
    }
    function usesCustomDrag() {
      return boxToolActive() || panToolActive()
    }
    function startsCustomDrag(event) {
      return event.button === 0 && (boxToolActive()
        || (panToolActive() && (interactiveRef.current.mode === '3d' || !event.ctrlKey)))
    }
    function preventNativeDrag(event) {
      if (!startsCustomDrag(event)) return
      event.preventDefault()
      event.stopImmediatePropagation()
    }
    function cancelCustomDrag(event) {
      if (boxGesture && (event.pointerId === undefined || boxGesture.pointerId === event.pointerId)) cancelBox()
      if (panGesture && (event.pointerId === undefined || panGesture.pointerId === event.pointerId)) {
        panGesture = null
        pointerStartRef.current = null
      }
    }
    function boxMove(event) {
      if (!boxGesture || boxGesture.pointerId !== event.pointerId) return
      if (!boxToolActive() || !canZoom() || boxGesture.sceneKey !== loadedSceneKeyRef.current) {
        cancelBox()
        return
      }
      const rect = canvas.getBoundingClientRect()
      const x = Math.max(0, Math.min(rect.width, event.clientX - rect.left))
      const y = Math.max(0, Math.min(rect.height, event.clientY - rect.top))
      const startX = boxGesture.clientX - rect.left
      const startY = boxGesture.clientY - rect.top
      setZoomBox({ left: Math.min(startX, x), top: Math.min(startY, y), width: Math.abs(x - startX), height: Math.abs(y - startY) })
    }
    function panMove(event) {
      if (!panGesture || panGesture.pointerId !== event.pointerId) return
      if (!panToolActive() || !canZoom() || panGesture.sceneKey !== loadedSceneKeyRef.current) {
        cancelCustomDrag(event)
        return
      }
      if (!panGesture.moved && Math.hypot(event.clientX - panGesture.clientX, event.clientY - panGesture.clientY) <= 5) return
      // Use the current viewport for both locations, including any DPI or size
      // change during capture. This translation leaves the peel in scan space.
      const previous = clientToBackingPx(canvas, panGesture.clientX, panGesture.clientY)
      const next = clientToBackingPx(canvas, event.clientX, event.clientY)
      if (interactiveRef.current.mode === '3d') {
        const view = renderView(nv)
        const pivot = view && pan3dPivot(nv.pivot3D, view.viewPoint, previous, next)
        if (!pivot) return
        orbitCentreRef.current = pivot
        nv.pivot3D = pivot
        nv.drawScene()
      } else if (!pan2d(nv, panGesture.plane, previous, next)) return
      panGesture = { ...panGesture, clientX: event.clientX, clientY: event.clientY, moved: true }
    }
    function handlePointerMove(event) {
      if (panGesture) panMove(event)
      else boxMove(event)
    }
    function cancelBoxOnEscape(event) {
      if (event.key !== 'Escape' || !boxGesture) return
      event.preventDefault()
      event.stopImmediatePropagation()
      cancelBox()
    }

    function handlePointerDown(event) {
      const is3d = interactiveRef.current.mode === '3d'
      if (is3d && event.button !== 0) return
      if (startsCustomDrag(event)) {
        event.preventDefault()
        if (!canZoom() || boxGesture || panGesture || pinching || event.isPrimary === false) return
        const gesture = { pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY, sceneKey: loadedSceneKeyRef.current }
        canvas.focus({ preventScroll: true })
        canvas.setPointerCapture?.(event.pointerId)
        if (boxToolActive()) {
          boxGesture = gesture
          return
        }
        const plane = is3d ? null : panPlaneAt(nv, clientToBackingPx(canvas, event.clientX, event.clientY))
        if (!is3d && plane === null) return
        panGesture = { ...gesture, plane }
      }
      pointerHeld = true
      window.clearTimeout(restoreTimer)
      // A plain click in 2D Pan leaves the slice and its crosshair where they were.
      pointerStartRef.current = !is3d && panGesture ? null
        : { x: event.clientX, y: event.clientY, sceneKey: loadedSceneKeyRef.current }
      setLowResolution(true)
    }

    function handlePointerUp(event) {
      if (panGesture) {
        if (panGesture.pointerId !== event.pointerId || event.button !== 0) return
        panMove(event)
        if (panGesture?.moved) pointerStartRef.current = null
        panGesture = null
      }
      if (boxToolActive() && event.button === 0) {
        const box = boxGesture
        if (!box || box.pointerId !== event.pointerId) return
        cancelBox()
        if (!canZoom() || box.sceneKey !== loadedSceneKeyRef.current
          || Math.min(Math.abs(box.clientX - event.clientX), Math.abs(box.clientY - event.clientY)) < 6) return
        const start = clientToBackingPx(canvas, box.clientX, box.clientY)
        const end = clientToBackingPx(canvas, event.clientX, event.clientY)
        if (!start || !end) return
        if (interactiveRef.current.mode === '3d') {
          const view = renderView(nv)
          if (view) apply3dFraming(nv, orbitCentreRef, zoomBox3dFraming(
            nv.scene.volScaleMultiplier, nv.pivot3D, view.viewport, view.viewPoint, start, end,
          ))
        } else zoomBox2d(nv, start, end)
        publishZoom(nv)
        return
      }
      const start = pointerStartRef.current
      pointerStartRef.current = null
      if (!start) return
      if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 5) return

      const interaction = interactiveRef.current
      if (typeof interaction.onSelectObject !== 'function') return
      const current = () => Boolean(start.sceneKey) && nvRef.current === nv
        && start.sceneKey === loadedSceneKeyRef.current && start.sceneKey === expectedSceneKeyRef.current
      if (!current()) return

      if (interaction.mode === '2d') {
        window.setTimeout(() => {
          if (!current()) return
          interaction.onSelectObject(
            semanticFromLocation(
              locationRef.current,
              interaction.visibleSources,
              interaction.differenceMode,
            ),
          )
        }, 0)
        return
      }

      const previousCrosshair = nv.scene?.crosshairPos
      nv.resetBriCon(event)
      // NiiVue replaces the crosshair on a successful depth pick and leaves the
      // previous position alone on a miss. A miss must not reselect that anatomy.
      const depthCrosshair = nv.scene?.crosshairPos !== previousCrosshair ? nv.scene?.crosshairPos : null
      const picked = pickSurfaceAtClick(nv, event, Array.from(registryRef.current.meshes.values()))
      if (picked) {
        const semantic = { source: picked.source, anatomy: picked.anatomy }
        if (picked.region) semantic.region = picked.region
        if (picked.source === 'pred' && picked.anatomy === 'lesion') {
          const worldMm = lesionVoxelAtSurface(registryRef.current.volumes.get('pred'), picked)
          if (worldMm) semantic.worldMm = worldMm
        }
        window.setTimeout(() => { if (current()) interaction.onSelectObject(semantic) }, 0)
        return
      }
      window.setTimeout(() => {
        if (!current()) return
        if (!depthCrosshair) {
          interaction.onSelectObject(null)
          return
        }
        const world = Array.from(nv.frac2mm(depthCrosshair, 0, true)).slice(0, 3)
        if (!world.every(Number.isFinite)) return

        let nearest = null
        registryRef.current.meshes.forEach((entry) => {
          if (!entry.mesh.visible || entry.mesh.opacity <= 0.02) return
          const result = nv.indexNearestXYZmm(entry.mesh.id, world[0], world[1], world[2])
          const distance = Number(result?.[1])
          if (!Number.isFinite(distance)) return
          if (!nearest || distance < nearest.distance) nearest = { ...entry, distance }
        })
        interaction.onSelectObject(
          nearest && nearest.distance <= 12
            ? { source: nearest.source, anatomy: nearest.anatomy }
            : null,
        )
      }, 0)
    }

    // Double-click a surface in 3D: orbit around that point and zoom in a step.
    function handleDoubleClick(event) {
      if (interactiveRef.current.mode !== '3d' || usesCustomDrag()) return
      const picked = pickSurfaceAtClick(nv, event, Array.from(registryRef.current.meshes.values()))
      if (!picked?.point) return
      orbitCentreRef.current = picked.point
      zoom3d(nv, 1.15)
      nv.drawScene()
      publishZoom(nv)
    }

    const captureGesture = { capture: true, passive: false }
    canvas.addEventListener('pointerdown', handlePointerDown)
    canvas.addEventListener('pointerup', handlePointerUp)
    canvas.addEventListener('pointermove', handlePointerMove)
    canvas.addEventListener('pointercancel', cancelCustomDrag)
    canvas.addEventListener('lostpointercapture', cancelCustomDrag)
    canvas.addEventListener('mousedown', preventNativeDrag, true)
    canvas.addEventListener('mouseup', preventNativeDrag, true)
    canvas.addEventListener('keydown', cancelBoxOnEscape, true)
    canvas.addEventListener('dblclick', handleDoubleClick)
    canvas.addEventListener('wheel', handleWheel, captureGesture)
    canvas.addEventListener('touchstart', handleTouchStart, captureGesture)
    canvas.addEventListener('touchmove', handleTouchMove, captureGesture)
    canvas.addEventListener('touchend', endPinch, true)
    canvas.addEventListener('touchcancel', endPinch, true)
    canvas.addEventListener('keydown', suppressSliceShortcut, true)
    canvas.addEventListener('keyup', suppressClipShortcut, true)
    window.addEventListener('pointerup', endGesture)
    window.addEventListener('pointercancel', endGesture)
    window.addEventListener('blur', endGesture)
    window.addEventListener('blur', cancelCustomDrag)

    return () => {
      if (clipFrameRef.current !== null) {
        window.cancelAnimationFrame(clipFrameRef.current)
        clipFrameRef.current = null
      }
      if (navigationFrameRef.current !== null) {
        window.cancelAnimationFrame(navigationFrameRef.current)
        navigationFrameRef.current = null
      }
      pendingNavigationRef.current = null
      canvas.removeEventListener('pointerdown', handlePointerDown)
      canvas.removeEventListener('pointerup', handlePointerUp)
      canvas.removeEventListener('pointermove', handlePointerMove)
      canvas.removeEventListener('pointercancel', cancelCustomDrag)
      canvas.removeEventListener('lostpointercapture', cancelCustomDrag)
      canvas.removeEventListener('mousedown', preventNativeDrag, true)
      canvas.removeEventListener('mouseup', preventNativeDrag, true)
      canvas.removeEventListener('keydown', cancelBoxOnEscape, true)
      canvas.removeEventListener('dblclick', handleDoubleClick)
      canvas.removeEventListener('wheel', handleWheel, true)
      canvas.removeEventListener('touchstart', handleTouchStart, true)
      canvas.removeEventListener('touchmove', handleTouchMove, true)
      canvas.removeEventListener('touchend', endPinch, true)
      canvas.removeEventListener('touchcancel', endPinch, true)
      canvas.removeEventListener('keydown', suppressSliceShortcut, true)
      canvas.removeEventListener('keyup', suppressClipShortcut, true)
      window.removeEventListener('pointerup', endGesture)
      window.removeEventListener('pointercancel', endGesture)
      window.removeEventListener('blur', endGesture)
      window.removeEventListener('blur', cancelCustomDrag)
      window.clearTimeout(restoreTimer)
      window.clearTimeout(wheelTimer)
      nv.cleanup()
      nvRef.current = null
    }
  }, [compact])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || !caseData) return undefined

    let cancelled = false

    async function loadScene() {
      try {
        const previousScene = currentSceneRef.current
        const previousView = captureViewState(nv)
        if (previousScene && previousView && loadedSceneKeyRef.current) {
          savedViewsRef.current.set(
            previousScene.viewKey,
            { ...previousView, ctUrl: previousScene.ctUrl, orbitCentre: orbitCentreRef.current },
          )
          const worldMm = Array.from(nv.frac2mm(previousView.crosshair, 0, true) || []).slice(0, 3)
          if (worldMm.length === 3 && worldMm.every(Number.isFinite)) {
            latestCrosshairWorldRef.current.set(previousScene.caseId, worldMm)
          }
        }

        loadedSceneKeyRef.current = ''
        lastNavigationSignatureRef.current = ''
        pendingNavigationRef.current = null
        setState({ status: 'loading', message: 'Loading prepared scan' })
        lastFocusedObjectRef.current = ''
        registryRef.current = {
          volumeIndexes: new Map(),
          volumes: new Map(),
          differenceVolumeIndexes: new Map(),
          differenceVolumes: new Map(),
          meshes: new Map(),
        }

        const ctPath = showFull && caseData.files.ct_full
          ? caseData.files.ct_full
          : caseData.files.ct
        const ctUrl = assetUrls?.ct || `${BASE}/${ctPath}`
        const currentCaseId = caseData.case_id || caseData.files.ct
        // A crop and the full study need independent framing. Reloads for an
        // arriving mask or mesh on the same CT should preserve the camera.
        const viewKey = JSON.stringify([currentCaseId, mode, mode === '3d' ? ctUrl : null])
        const availableSources = sources.filter((source) => caseData.files[source])
        const renderedCtOpacity = effectiveCtOpacity(ctOpacity, clip)

        clearMeshes(nv)
        orbitCentreRef.current = null
        const volumes = [{
          url: ctUrl,
          name: 'ct.nii.gz',
          colormap: 'gray',
          opacity: mode === '2d'
            ? 1
            : renderedCtOpacity,
          ...(ctRange ? { cal_min: ctRange[0], cal_max: ctRange[1] } : CT_WINDOWS[ctWindow]),
          trustCalMinMax: true,
          ignoreZeroVoxels: true,
        }]

        availableSources.forEach((source) => {
          volumes.push({
            url: assetUrls?.[source] || `${BASE}/${caseData.files[source]}`,
            name: `${source}.nii.gz`,
            colormap: 'warm',
            opacity: mode === '2d' ? overlayOpacity : 0,
            cal_min: 0,
            cal_max: 2,
          })
        })
        const canLoadDifference = enableDifferenceAssets
          && availableSources.includes('gt')
          && caseData.files.difference
        if (canLoadDifference) {
          for (const anatomy of ['pancreas', 'lesion']) {
            const differencePath = caseData.files.difference[anatomy]
            if (!differencePath) continue
            volumes.push({
              url: `${BASE}/${differencePath}`,
              name: `diff-${anatomy}.nii.gz`,
              colormap: 'warm',
              opacity: 0,
              cal_min: 0,
              cal_max: 3,
            })
          }
        }

        await nv.loadVolumes(volumes)
        if (cancelled) return
        if (nativeGeometry) verifyNativeVolumes(nv.volumes, nativeGeometry, { ctOnly: nativeCtOnly })

        availableSources.forEach((source, index) => {
          const volumeIndex = index + 1
          registryRef.current.volumeIndexes.set(source, volumeIndex)
          registryRef.current.volumes.set(source, nv.volumes[volumeIndex])
        })
        let differenceIndex = availableSources.length + 1
        if (canLoadDifference) {
          for (const anatomy of ['pancreas', 'lesion']) {
            if (!caseData.files.difference[anatomy]) continue
            registryRef.current.differenceVolumeIndexes.set(anatomy, differenceIndex)
            registryRef.current.differenceVolumes.set(anatomy, nv.volumes[differenceIndex])
            differenceIndex += 1
          }
        }

        if (mode === '2d') {
          nv.opts.isOrientCube = false
          setPlaneLayout(nv, activePlane)
          // A thin, quiet crosshair with an open centre keeps the target visible.
          nv.setCrosshairColor([0.66, 0.74, 0.84, 0.42])
          nv.opts.crosshairWidth = 1
          nv.opts.crosshairGap = 14
          // Orientation letters: larger and brighter so they read at a glance.
          nv.opts.fontMinPx = 15
          nv.opts.fontColor = [0.8, 0.84, 0.9, 1]
          nv.setAtlasOutline(0)
        } else {
          const meshFiles = caseData.files.mesh || {}
          const layers = []
          const layerSemantics = []

          availableSources.forEach((source) => {
            for (const anatomy of ['pancreas', 'lesion']) {
              const key = `${anatomy}_${source}`
              const meshPath = meshFiles[key]
              const verifiedMesh = assetUrls?.mesh?.[key]
              if (!meshPath && !verifiedMesh) continue
              const colors = SOURCE_COLORS[source][anatomy]
              layers.push({
                url: verifiedMesh || `${BASE}/${meshPath}`,
                name: `${source}-${anatomy}.${verifiedMesh ? 'stl' : 'obj'}`,
                rgba255: [...colors, anatomy === 'pancreas' ? 190 : 255],
                opacity: anatomy === 'pancreas' ? 0.68 : 1,
              })
              layerSemantics.push({ source, anatomy })
            }
          })
          if (canLoadDifference) {
            for (const anatomy of ['pancreas', 'lesion']) {
              for (const [region, meshSuffix] of [
                ['agreement', 'agreement'],
                ['predOnly', 'pred_only'],
                ['gtOnly', 'gt_only'],
              ]) {
                const meshPath = meshFiles[`${anatomy}_${meshSuffix}`]
                if (!meshPath) continue
                const colors = DIFFERENCE_COLORS[region]
                layers.push({
                  url: `${BASE}/${meshPath}`,
                  name: `difference-${anatomy}-${region}.obj`,
                  rgba255: [...colors, 255],
                  opacity: 1,
                })
                layerSemantics.push({ source: 'difference', anatomy, region })
              }
            }
          }

          if (layers.length) await nv.loadMeshes(layers)
          if (cancelled) return

          batchViewerUpdate(nv, () => layerSemantics.forEach((semantic, index) => {
            const mesh = nv.meshes[index]
            if (!mesh) return
            const semanticKey = semantic.region
              ? `${semantic.source}:${semantic.anatomy}:${semantic.region}`
              : `${semantic.source}:${semantic.anatomy}`
            registryRef.current.meshes.set(
              semanticKey,
              { ...semantic, mesh },
            )
            nv.setMeshShader(mesh.id, 'Hemispheric')
          }))

          nv.setSliceType(nv.sliceTypeRender)
          // Small labelled orientation cube in the corner so L/R, A/P and S/I stay readable while orbiting.
          nv.opts.isOrientCube = !compact
          nv.setRenderAzimuthElevation(...(clip?.enabled ? ANTERIOR_CAMERA : [120, 15]))
          nv.setClipPlaneColor([0, 0, 0, 0])
          applyPeel(nv, clip)
          onPeelReveal?.(peelRevealPercentages(nv, Array.from(registryRef.current.meshes.values())))
        }

        const savedView = savedViewsRef.current.get(viewKey)
        const sameGrid = savedView?.ctUrl === ctUrl
        if (mode === '3d') orbitCentreRef.current = savedView?.orbitCentre ?? null
        // Keep the established 2D framing on an image source change, while
        // treating its fractional slice position as specific to the old grid.
        const restore = sameGrid || !savedView ? savedView : { ...savedView, crosshair: null }
        if (!restoreViewState(nv, restore, mode) || !sameGrid) {
          const primaryVolume = registryRef.current.volumes.get(availableSources[0])
          const target = primaryVolume
            ? labelCentroidMM(primaryVolume, 1)
            : volumeCenterMM(nv.volumes[0])
          focusOnWorldPoint(nv, target, mode)
          if (mode === '3d' && anatomyLighting && !showFull && primaryVolume && target) orbitCentreRef.current = target
        }
        // NiiVue fractions belong to the CT grid. Bridge scene changes through
        // world millimeters and leave a crop's own position if the point lies outside it.
        const worldMm = latestCrosshairWorldRef.current.get(currentCaseId)
        const fraction = worldMm && Array.from(nv.mm2frac(worldMm, 0, true) || []).slice(0, 3)
        if (fraction?.length === 3 && fraction.every(value => Number.isFinite(value) && value >= 0 && value <= 1)) {
          nv.scene.crosshairPos = new Float32Array(fraction)
        }
        // First visit to 3D for this case (no saved camera): frame the surfaces.
        if (mode === '3d' && !savedView) {
          const fit = compact ? 1.1 : showFull ? FULL_SCAN_SCALE : surfaceFitScale(nv)
          nv.setScale(fit || FULL_SCAN_SCALE)
        }

        nv.updateGLVolume()
        nv.drawScene()
        currentSceneRef.current = { caseId: currentCaseId, ctUrl, viewKey }
        loadedSceneKeyRef.current = sceneKey
        publishZoom(nv)
        publishNavigation(nv, { immediate: true, origin: 'initial' })
        setSceneVersion((version) => version + 1)
        if (!cancelled) setState({ status: 'ready', message: 'Prepared result loaded' })
      } catch (error) {
        if (!cancelled) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : 'The prepared scan could not be displayed.',
          })
        }
      }
    }

    // NiiVue mutates one volume registry while loading. Serialize transitions so
    // a slow previous study cannot append volumes into a newer study's scene.
    sceneLoadChainRef.current = sceneLoadChainRef.current
      .catch(() => {})
      .then(() => { if (!cancelled) return loadScene() })
    return () => {
      cancelled = true
    }
  }, [caseData, sources.join('|'), mode, showFull, enableDifferenceAssets, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || mode !== '2d'
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
    ) return
    setPlaneLayout(nv, activePlane)
    nv.drawScene()
    setPlaneTiles(planeTilesFrom(nv))
    publishNavigation(nv)
  }, [activePlane, mode, sceneVersion, state.status, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return

    const presentation = {
      anatomyFocus,
      focusTreatment,
      selectedObject,
      showPancreas,
      showLesion,
      sourceFocus,
    }

    try {
      batchViewerUpdate(nv, () => {
        if (mode === '2d') {
          setVolumeRendering(nv, true)
          registryRef.current.volumeIndexes.forEach((volumeIndex, source) => {
            const volume = nv.volumes[volumeIndex]
            if (!volume) return
            volume.setColormapLabel(labelColormap(source, presentation))
            // Keep a reference fill when the displayed CT grid or plane cannot
            // support the dashed reference contour over the prediction.
            const outlineOnly = source === 'gt' && renderedSources.includes('pred')
              && hasContourTile(nv, volume, activePlane)
            nv.setOpacity(volumeIndex, overlayMode === 'fill' && !differenceMode && renderedSources.includes(source) && !outlineOnly ? overlayOpacity : 0)
          })
          registryRef.current.differenceVolumeIndexes.forEach((volumeIndex, anatomy) => {
            const volume = nv.volumes[volumeIndex]
            if (!volume) return
            volume.setColormapLabel(differenceColormap({ selectedObject, anatomy, focusTreatment }))
            const anatomyVisible = anatomyFocus === 'all' || anatomyFocus === anatomy
            const layerVisible = anatomy === 'pancreas' ? showPancreas : showLesion
            const excludedBySelection = focusTreatment === 'isolate' && selectedObject?.source === 'difference'
              && selectedObject.anatomy !== anatomy
            nv.setOpacity(
              volumeIndex,
              differenceMode && anatomyVisible && layerVisible && !excludedBySelection ? overlayOpacity : 0,
            )
          })
          nv.setOpacity(0, 1)
          nv.updateGLVolume()
          nv.drawScene()
          return
        }

        const renderedCtOpacity = effectiveCtOpacity(ctOpacity, clip)
        nv.setOpacity(0, renderedCtOpacity)
        setVolumeRendering(nv, renderedCtOpacity > 0.001)
        registryRef.current.meshes.forEach((entry) => {
          const structureVisible = entry.anatomy === 'pancreas' ? showPancreas : showLesion
          const sourceVisible = entry.source === 'difference'
            ? differenceMode && (anatomyFocus === 'all' || anatomyFocus === entry.anatomy)
            : !differenceMode && renderedSources.includes(entry.source)
          const isSelected = selectedObject?.source === entry.source
            && selectedObject.anatomy === entry.anatomy
            && (entry.source !== 'difference' || selectedObject.region === entry.region)
          const opacity = meshOpacity({
            anatomy: entry.anatomy,
            source: entry.source,
            visible: structureVisible && sourceVisible,
            anatomyFocus,
            focusTreatment,
            hasSelection: Boolean(selectedObject),
            isSelected,
            overlayOpacity,
            sourceFocus,
          })
          // Difference pieces tile one surface; drawing the pancreas pieces opaque
          // avoids stacked translucent shells. Lesion pieces show through via X-ray.
          const finalOpacity = entry.source === 'difference' && entry.anatomy === 'pancreas' && opacity > 0
            ? 1
            : opacity
          const color = entry.source === 'difference'
            ? DIFFERENCE_COLORS[entry.region]
            : SOURCE_COLORS[entry.source][entry.anatomy]
          entry.mesh.visible = finalOpacity > 0.01
          setMeshPropertyIfChanged(nv, entry.mesh, 'rgba255', new Uint8Array([
            color[0],
            color[1],
            color[2],
            clamp255(finalOpacity * 255),
          ]))
          setMeshPropertyIfChanged(nv, entry.mesh, 'opacity', finalOpacity)
          const shader = meshShaderFor(entry, { isSelected, renderedSources, sourceFocus, anatomyLighting })
          if (entry.appliedShader !== shader) {
            nv.setMeshShader(entry.mesh.id, shader)
            entry.appliedShader = shader
          }
        })
        nv.opts.meshXRay = differenceMode ? 0.32 : 0.22

        nv.updateGLVolume()
        nv.drawScene()
      })
    } catch (error) {
      setState({
        status: 'error',
        message: error instanceof Error ? error.message : 'The viewer presentation could not be updated.',
      })
    }
  }, [
    sceneVersion,
    state.status,
    mode,
    activePlane,
    overlayMode,
    anatomyLighting,
    overlayOpacity,
    ctOpacity,
    showPancreas,
    showLesion,
    anatomyFocus,
    sourceFocus,
    focusTreatment,
    selectedObject?.source,
    selectedObject?.anatomy,
    selectedObject?.region,
    renderedSources.join('|'),
    differenceMode,
    clip?.enabled,
    Number(clip?.progress || 0) >= 99.5,
    sceneKey,
  ])

  // Layer/selection changes must not discard a window adjusted on the image.
  // Only an explicit preset/range change or a newly loaded scene resets it.
  useEffect(() => {
    const nv = nvRef.current
    if (!nv || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey || !nv.volumes?.[0]) return
    const range = ctRange ? { cal_min: ctRange[0], cal_max: ctRange[1] } : CT_WINDOWS[ctWindow] || CT_WINDOWS.soft
    nv.volumes[0].cal_min = range.cal_min
    nv.volumes[0].cal_max = range.cal_max
    nv.updateGLVolume()
  }, [ctWindow, ctRange?.[0], ctRange?.[1], sceneVersion, state.status, sceneKey])

  // Linked panes exchange only the anatomical crosshair. Pan/zoom intentionally
  // remain local, and applying a remote position is tagged to prevent echoes.
  useEffect(() => {
    const nv = nvRef.current
    if (!nv || mode !== '2d' || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey
      || syncCrosshair?.sceneKey !== sceneKey || !Array.isArray(syncCrosshair?.fractions)
      || syncCrosshair.fractions.length !== 3 || !syncCrosshair.fractions.every(Number.isFinite)) return
    const next = syncCrosshair.fractions.map(value => Math.max(0, Math.min(1, value)))
    if (next.every((value, index) => Math.abs(value - nv.scene.crosshairPos[index]) < 0.000001)) return
    nv.scene.crosshairPos = new Float32Array(next)
    nv.drawScene()
    publishNavigation(nv, { immediate: true, origin: 'sync' })
  }, [syncCrosshair?.id, sceneVersion, state.status, sceneKey, mode])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || mode !== '2d' || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey
      || syncWindow?.sceneKey !== sceneKey || !Array.isArray(syncWindow?.range)) return
    const [min, max] = syncWindow.range
    const ct = nv.volumes?.[0]
    if (!ct || !Number.isFinite(min) || !Number.isFinite(max) || max <= min
      || (ct.cal_min === min && ct.cal_max === max)) return
    ct.cal_min = min
    ct.cal_max = max
    nv.updateGLVolume()
  }, [syncWindow?.id, sceneVersion, state.status, sceneKey, mode])

  // Resize the WebGL drawing buffer as well as the layout. Redrawing into the
  // old buffer leaves anatomy at its old size when a pane/fullscreen grows.
  // Keep the camera in anatomical units so NiiVue's fit scales with the new
  // canvas while the user's additional zoom, pan and slice remain unchanged.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || mode !== '2d' || typeof ResizeObserver === 'undefined') return undefined
    let frame = null
    const observer = new ResizeObserver(() => {
      if (frame !== null) window.cancelAnimationFrame(frame)
      frame = window.requestAnimationFrame(() => {
        frame = null
        const nv = nvRef.current
        if (!nv || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey
          || !nv.volumes?.[0] || canvas.clientWidth <= 0 || canvas.clientHeight <= 0) return
        const view = captureViewState(nv)
        nv.resizeListener()
        restoreViewState(nv, view, '2d')
        setPlaneLayout(nv, activePlane)
        nv.drawScene()
        setPlaneTiles(planeTilesFrom(nv))
      })
    })
    observer.observe(canvas)
    return () => {
      observer.disconnect()
      if (frame !== null) window.cancelAnimationFrame(frame)
    }
  }, [activePlane, mode, state.status, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    if (!nv || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey) return

    let primary = DRAG_MODE.crosshair
    if (mode === '2d') {
      if (interactionMode === 'pan' && !framingLocked) primary = DRAG_MODE.pan
      if (interactionMode === 'window') primary = DRAG_MODE.windowing
      nv.setMouseEventConfig({
        leftButton: {
          primary,
          withShift: framingLocked ? DRAG_MODE.none : DRAG_MODE.pan,
          withCtrl: DRAG_MODE.crosshair,
        },
        rightButton: DRAG_MODE.windowing,
        centerButton: framingLocked ? DRAG_MODE.none : DRAG_MODE.pan,
      })
      nv.setTouchEventConfig({
        singleTouch: primary,
        doubleTouch: framingLocked ? DRAG_MODE.none : DRAG_MODE.pan,
      })
      return
    }

    nv.setMouseEventConfig({
      leftButton: {
        primary: DRAG_MODE.crosshair,
        withShift: DRAG_MODE.none,
        withCtrl: DRAG_MODE.crosshair,
      },
      rightButton: DRAG_MODE.none,
      centerButton: DRAG_MODE.none,
    })
    nv.setTouchEventConfig({
      singleTouch: DRAG_MODE.crosshair,
      doubleTouch: DRAG_MODE.none,
    })
  }, [interactionMode, framingLocked, mode, sceneVersion, state.status, sceneKey])

  useEffect(() => {
    const nv = nvRef.current
    const canvas = canvasRef.current
    if (mode !== '2d' || !framingLocked || !nv || !canvas) return
    // NiiVue's wheel and pinch behavior considers its fallback drag mode,
    // independently of the configured mouse buttons.
    const previous = nv.opts.dragMode
    nv.setDragMode(DRAG_MODE.none)
    const preventModeCycle = event => {
      if (event.code === 'KeyM') {
        event.preventDefault()
        event.stopImmediatePropagation()
      }
    }
    canvas.addEventListener('keydown', preventModeCycle, true)
    return () => {
      canvas.removeEventListener('keydown', preventModeCycle, true)
      if (nvRef.current === nv && previous !== undefined) nv.setDragMode(previous)
    }
  }, [framingLocked, compact, mode])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !navigationCommand
      || handledNavigationCommandRef.current === navigationCommand.id
      || !nv
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return

    const command = navigationCommand
    if (command.type === 'restore-camera' && command.view.viewKey !== currentSceneRef.current?.viewKey) return
    handledNavigationCommandRef.current = command.id
    if (mode === '2d' && framingLocked && ['fit', 'zoom', 'zoom-lesion'].includes(command.type)) return
    if (command.type === 'slice') {
      const axis = PLANE_AXIS[command.plane]
      const total = Number((nv.volumes[0]?.dimsRAS || nv.volumes[0]?.hdr?.dims)?.[axis + 1])
      if (Number.isInteger(axis) && Number.isFinite(total) && total > 1 && Number.isFinite(Number(command.index))) {
        const index = Math.max(0, Math.min(total - 1, Number(command.index)))
        const next = Array.from(nv.scene.crosshairPos)
        next[axis] = (index + 0.5) / total
        nv.scene.crosshairPos = new Float32Array(next)
      }
    } else if (command.type === 'measurement-point') {
      if (mode === '2d' && Array.isArray(command.worldMm) && command.worldMm.length === 3
        && command.worldMm.every(Number.isFinite)) {
        const fraction = nv.mm2frac(command.worldMm, 0, true)
        if (fraction?.length === 3 && Array.from(fraction).every(v => Number.isFinite(v) && v >= 0 && v <= 1)) {
          nv.scene.crosshairPos = new Float32Array(fraction)
        }
        if (!framingLocked && command.fitBounds?.length) zoomToBounds2d(nv, command.fitBounds, 0.48)
      }
    } else if (command.type === 'restore-camera') {
      orbitCentreRef.current = command.view.orbitCentre ?? null
      restoreViewState(nv, command.view, mode)
    } else if (command.type === 'restore-finding-view') {
      const { worldMm, camera, pan2Dxyzmm, ctRange: window } = command.view
      if (mode === '3d' && camera) {
        orbitCentreRef.current = camera.pivot ?? null
        nv.setRenderAzimuthElevation(camera.azimuth, camera.elevation)
        nv.setScale(camera.scale)
      } else if (mode === '2d') {
        const fraction = nv.mm2frac(worldMm, 0, true)
        if (fraction?.length !== 3 || !Array.from(fraction).every(v => Number.isFinite(v) && v >= 0 && v <= 1)) return
        nv.scene.crosshairPos = new Float32Array(fraction)
        if (pan2Dxyzmm) nv.setPan2Dxyzmm(pan2Dxyzmm)
        if (window) {
          nv.volumes[0].cal_min = window[0]
          nv.volumes[0].cal_max = window[1]
        }
        nv.updateGLVolume()
      }
    } else if (command.type === 'focus') {
      const volume = registryRef.current.volumes.get(command.source)
        || registryRef.current.volumes.get('pred')
        || registryRef.current.volumes.get('gt')
      const labelValue = command.anatomy === 'lesion' ? 2 : 1
      const focused = focusOnWorldPoint(nv, labelCentroidMM(volume, labelValue), mode)
      if (mode === '3d') {
        if (focused) orbitCentreRef.current = nv.pivot3D
        if (Number.isFinite(command.azimuth) && Number.isFinite(command.elevation)) {
          nv.setRenderAzimuthElevation(command.azimuth, command.elevation)
        }
        if (Number.isFinite(command.scale)) nv.setScale(command.scale)
      }
    } else if (command.type === 'camera') {
      nv.setRenderAzimuthElevation(command.azimuth, command.elevation)
    } else if (command.type === 'rotate') {
      nv.setRenderAzimuthElevation(
        Number(nv.scene.renderAzimuth) + Number(command.deltaAzimuth || 0),
        Math.max(-90, Math.min(90, Number(nv.scene.renderElevation) + Number(command.deltaElevation || 0))),
      )
    } else if (command.type === 'zoom') {
      if (mode === '2d') zoom2d(nv, Number(command.factor))
      else zoom3d(nv, Number(command.factor))
    } else if (command.type === 'zoom-lesion') {
      if (mode === '3d') {
        apply3dFraming(nv, orbitCentreRef, lesionFraming3d(nv, command.boundsWorldMm))
      } else {
        zoomToBounds2d(nv, command.boundsWorldMm)
        // This explicit action takes the reviewer through the selected lesion
        // when the current CT slice no longer intersects it.
        focusOnWorldPoint(nv, command.worldMm, mode)
      }
    } else if (command.type === 'fit') {
      orbitCentreRef.current = null
      if (mode === '3d') {
        focusOnWorldPoint(nv, volumeCenterMM(nv.volumes[0]), mode)
        nv.setScale(1)
      } else nv.setPan2Dxyzmm([0, 0, 0, 1])
    }

    nv.drawScene()
    publishZoom(nv)
    publishNavigation(nv)
  }, [navigationCommand?.id, sceneVersion, state.status, sceneKey, mode, framingLocked])

  useEffect(() => {
    if (!selectedObject) {
      lastFocusedObjectRef.current = ''
      return
    }
    const nv = nvRef.current
    if (
      !nv
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || (mode === '2d' && measurementCalipers)
    ) return
    const worldMm = selectedObject.worldMm
    const focusKey = `${selectedObject.source}:${selectedObject.anatomy}:${selectedObject.region || ''}:${worldMm?.join(',') || ''}`
    if (lastFocusedObjectRef.current === focusKey) return

    const volume = selectedObject.source === 'difference'
      ? registryRef.current.differenceVolumes.get(selectedObject.anatomy)
      : registryRef.current.volumes.get(selectedObject.source)
    const labelValue = selectedObject.source === 'difference'
      ? { agreement: 1, predOnly: 2, gtOnly: 3 }[selectedObject.region]
      : selectedObject.anatomy === 'lesion' ? 2 : 1
    if (focusOnWorldPoint(nv, worldMm || labelCentroidMM(volume, labelValue), mode)) {
      lastFocusedObjectRef.current = focusKey
      nv.drawScene()
      publishNavigation(nv)
    }
  }, [
    sceneVersion,
    state.status,
    mode,
    selectedObject?.source,
    selectedObject?.anatomy,
    selectedObject?.region,
    selectedObject?.worldMm,
    measurementCalipers,
    sceneKey,
  ])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || mode !== '3d'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return
    const justActivated = Boolean(clip?.enabled) && !previousClipEnabledRef.current
    previousClipEnabledRef.current = Boolean(clip?.enabled)
    if (clipFrameRef.current !== null) {
      window.cancelAnimationFrame(clipFrameRef.current)
    }
    clipFrameRef.current = window.requestAnimationFrame(() => {
      clipFrameRef.current = null
      if (loadedSceneKeyRef.current !== sceneKey || expectedSceneKeyRef.current !== sceneKey) return
      applyPeel(nv, clip)
      if (justActivated) {
        nv.setRenderAzimuthElevation(...ANTERIOR_CAMERA)
      }
    })
  }, [clip?.enabled, clip?.depth, clip?.azimuth, clip?.elevation, mode, sceneKey, sceneVersion])

  useEffect(() => {
    const nv = nvRef.current
    if (
      !nv
      || handledResetTokenRef.current === resetToken
      || state.status !== 'ready'
      || loadedSceneKeyRef.current !== sceneKey
      || !nv.volumes?.[0]
    ) return
    handledResetTokenRef.current = resetToken
    if (mode === '2d' && framingLocked) return
    orbitCentreRef.current = null
    lastFocusedObjectRef.current = ''
    if (mode === '3d') {
      nv.setRenderAzimuthElevation(...(clip?.enabled ? ANTERIOR_CAMERA : [120, 15]))
      nv.setScale(compact ? 1 : showFull ? FULL_SCAN_SCALE : (surfaceFitScale(nv) || 1))
    } else {
      setPlaneLayout(nv, activePlane)
      nv.setPan2Dxyzmm([0, 0, 0, 1])
    }
    const primaryVolume = registryRef.current.volumes.get(sources[0])
    const target = primaryVolume
      ? labelCentroidMM(primaryVolume, 1)
      : volumeCenterMM(nv.volumes[0])
    focusOnWorldPoint(nv, target, mode)
    nv.drawScene()
    publishZoom(nv)
    publishNavigation(nv)
  }, [resetToken, sceneVersion, state.status, mode, sceneKey, clip?.enabled, framingLocked])

  useEffect(() => {
    const nv = nvRef.current
    if (!onViewHandle || !nv || state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey) return
    const isCurrent = () => nvRef.current === nv && loadedSceneKeyRef.current === sceneKey && expectedSceneKeyRef.current === sceneKey
    onViewHandle({
      capture: () => isCurrent() ? {
        ...captureViewState(nv), sceneKey, viewKey: currentSceneRef.current?.viewKey, orbitCentre: orbitCentreRef.current,
        worldMm: mode === '2d' ? Array.from(nv.frac2mm(nv.scene.crosshairPos, 0, true)).slice(0, 3) : null,
      } : null,
      thumbnail: () => {
        if (!isCurrent() || mode !== '2d' || !nv.canvas?.width || !nv.canvas?.height) return null
        try {
          const image = document.createElement('canvas')
          image.width = 112
          image.height = Math.max(1, Math.min(112, Math.round(112 * nv.canvas.height / nv.canvas.width)))
          const context = image.getContext('2d')
          if (!context) return null
          nv.drawScene()
          context.drawImage(nv.canvas, 0, 0, image.width, image.height)
          return image.toDataURL('image/jpeg', 0.8)
        } catch {
          return null
        }
      },
      restore: (view) => {
        if (!view || !isCurrent()) return false
        const sameView = mode === '3d' ? view.viewKey === currentSceneRef.current?.viewKey : view.sceneKey === sceneKey
        if (!sameView) return false
        orbitCentreRef.current = view.orbitCentre ?? null
        restoreViewState(nv, view, mode)
        if (view.ctRange?.every(Number.isFinite)) {
          ;[nv.volumes[0].cal_min, nv.volumes[0].cal_max] = view.ctRange
          nv.updateGLVolume()
        }
        nv.drawScene()
        publishZoom(nv)
        publishNavigation(nv)
        return true
      },
    })
    return () => onViewHandle(null)
  }, [onViewHandle, mode, sceneKey, sceneVersion, state.status])

  const isPancreasMeasurement = mode === '2d' && measurementAnatomy === 'pancreas'
  const measurementLayerVisible = isPancreasMeasurement ? showPancreas : showLesion
  const ready = state.status === 'ready' && loadedSceneKeyRef.current === sceneKey
  const panning = interactionMode === 'pan' && (mode === '3d' || !framingLocked)

  return (
    <div className={`niivue-frame niivue-frame--${mode}${compact ? ' niivue-frame--compact' : ''}${guided ? ' niivue-frame--guided' : ''}${panning ? ' niivue-frame--pan' : ''}`}>
      <canvas ref={canvasRef} aria-label={label} style={{
        visibility: state.status !== 'ready' || loadedSceneKeyRef.current !== sceneKey ? 'hidden' : undefined,
        cursor: interactionMode === 'box-zoom' && !(mode === '2d' && framingLocked) ? 'crosshair' : undefined,
        touchAction: panning ? 'none' : undefined,
      }} />
      <ViewerMeasurementOverlay nvRef={nvRef} loadedSceneKeyRef={loadedSceneKeyRef} sceneKey={sceneKey}
        ready={ready && Boolean(sliceLocatorCorners || (overlayMode !== 'off' && measurementLayerVisible && !differenceMode && renderedSources.includes('pred')))}
        mode={mode} anatomy={measurementAnatomy} calipers={measurementCalipers} marker={selectedLesionWorldMm} sliceLocatorCorners={sliceLocatorCorners} />
      {mode === '2d' && (overlayMode === 'outline' || overlayMode === 'fill') && activePlane !== 'multiplanar' && <ViewerContourOverlay nvRef={nvRef} loadedSceneKeyRef={loadedSceneKeyRef} sceneKey={sceneKey}
        ready={ready && renderedSources.includes('pred') && !differenceMode} mask={registryRef.current.volumes.get('pred')}
        plane={activePlane} showLesion={showLesion} showPancreas={showPancreas}
        opacity={sourceFocus === 'gt' && renderedSources.includes('gt') ? 0.3 : 1} />}
      {mode === '2d' && overlayMode === 'fill' && activePlane !== 'multiplanar' && <ViewerContourOverlay nvRef={nvRef} loadedSceneKeyRef={loadedSceneKeyRef} sceneKey={sceneKey}
        ready={ready && renderedSources.includes('gt') && !differenceMode} mask={registryRef.current.volumes.get('gt')}
        plane={activePlane} showLesion={showLesion} showPancreas={showPancreas} colors={REFERENCE_STROKES}
        dashed={renderedSources.includes('pred')} label="Reference contours"
        opacity={sourceFocus === 'pred' && renderedSources.includes('pred') ? 0.3 : 1} />}
      {imageDetails && <ImagingViewportDetails nvRef={nvRef} loadedSceneKeyRef={loadedSceneKeyRef} sceneKey={sceneKey}
        ready={ready} plane={activePlane} source={imageDetails} />}
      {zoomBox && interactionMode === 'box-zoom' && !framingLocked && (
        <div aria-hidden="true" className="niivue-zoom-box" style={{ ...zoomBox, position: 'absolute',
          border: '1px solid #f5ca82', background: '#f5ca8224', pointerEvents: 'none' }} />
      )}
      {mode === '2d' && showPlaneLabels && (
        <div
          className={`viewer-plane-labels viewer-plane-labels--${activePlane}${planeTiles.length ? ' viewer-plane-labels--placed' : ''}`}
          aria-label="CT anatomical planes"
        >
          {(activePlane === 'multiplanar'
            ? ['axial', 'coronal', 'sagittal']
            : [activePlane]
          ).map((planeKey) => {
            const [plane, explanation] = PLANE_META[planeKey]
            const tile = planeTiles.find((item) => item.plane === planeKey)
            return (
            <span key={plane} style={tile ? { left: `${Math.round(tile.left + 10)}px`, top: `${Math.round(tile.top + 10)}px` } : undefined}>
              <strong>{plane}</strong>
              <small>{explanation}</small>
            </span>
            )
          })}
        </div>
      )}
      {state.status === 'loading' && (
        <div className="viewer-state" role="status">
          <LoaderCircle size={16} className="spin" aria-hidden="true" />
          <span>{state.message}</span>
        </div>
      )}
      {state.status === 'error' && (
        <div className="viewer-state viewer-state--error" role="alert">
          <TriangleAlert size={16} aria-hidden="true" />
          <span>{state.message}</span>
        </div>
      )}
      {state.status === 'ready' && (
        <span className="viewer-ready" aria-label="Prepared result loaded">Evidence ready</span>
      )}
    </div>
  )
}
