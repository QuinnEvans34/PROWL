const SLICE_AXES = {
  axial: { type: 0, depth: 2 },
  coronal: { type: 1, depth: 1 },
  sagittal: { type: 2, depth: 0 },
}

function millimeterSpacing(header, legacyMillimeters) {
  const units = header?.xyzt_units
  if (!Number.isInteger(units) || ((units & 7) !== 2 && !(legacyMillimeters && (units & 7) === 0))) return null
  const affine = header?.affine
  if (affine?.length !== 4 || !affine.slice(0, 3).every(row => row?.length === 4 && row.every(Number.isFinite))) return null
  const spacing = [0, 1, 2].map(axis => Math.hypot(affine[0][axis], affine[1][axis], affine[2][axis]))
  return spacing.every(value => value > 0) ? spacing : null
}

function physicalScaleBar(canvas, tile) {
  const [left, , width] = tile?.leftTopWidthHeight || []
  const mm = Math.abs(tile?.fovMM?.[0])
  if (!canvas?.width || !canvas.clientWidth || !Number.isFinite(left) || !Number.isFinite(width) || !mm || !Number.isFinite(mm)) return null
  const cssScale = canvas.clientWidth / canvas.width
  const pixelsPerMm = Math.abs(width) * cssScale / mm
  const visibleLeft = Math.max(0, Math.min(left, left + width) * cssScale)
  const visibleRight = Math.min(canvas.clientWidth, Math.max(left, left + width) * cssScale)
  const targetPx = Math.min(110, visibleRight - visibleLeft - 20)
  if (!(targetPx > 0) || !(pixelsPerMm > 0)) return null
  const targetMm = targetPx / pixelsPerMm
  if (!(targetMm > 0) || !Number.isFinite(targetMm)) return null
  const power = 10 ** Math.floor(Math.log10(targetMm))
  const millimeters = ([5, 2, 1].find(step => step * power <= targetMm) || 1) * power
  if (!millimeters) return null
  return { millimeters: Number(millimeters.toPrecision(4)), widthPx: millimeters * pixelsPerMm }
}

/** Use the displayed NiiVue tile's signed field of view and backing-pixel width. */
export function viewportImageDetails(nv, plane, source) {
  const ct = nv?.volumes?.[0]
  if (!ct || !source) return null
  const spacing = millimeterSpacing(ct.hdr, source.kind === 'prepared' && source.legacyMillimeters)
  const tile = nv.screenSlices?.find(slice => slice.axCorSag === SLICE_AXES[plane]?.type && Number.isFinite(slice.sliceFrac))
  const low = ct.cal_min
  const high = ct.cal_max
  const windowHu = source.kind === 'source' && source.calibratedHu && Number.isFinite(low) && Number.isFinite(high) && high > low
    ? { width: high - low, center: (high + low) / 2 }
    : null
  return { kind: source.kind, series: source.series, spacing, scale: spacing && physicalScaleBar(nv.canvas, tile), windowHu }
}

/**
 * Locate a point on the actual viewer grid. Snap the depth coordinate only,
 * keeping the other two crosshair axes aligned to the original world point.
 */
export function sourceSliceAt(nv, plane, worldMm) {
  const depth = SLICE_AXES[plane]?.depth
  const dims = nv?.volumes?.[0]?.dimsRAS || nv?.volumes?.[0]?.hdr?.dims
  const total = dims?.[depth + 1]
  if (depth === undefined || !Number.isSafeInteger(total) || total < 1
    || worldMm?.length !== 3 || !Array.from(worldMm).every(Number.isFinite)) return null
  const mapped = nv.mm2frac(worldMm, 0, true)
  if (!(mapped?.length >= 3)) return null
  const fractions = Array.from(mapped).slice(0, 3)
  if (!fractions.every(value => Number.isFinite(value) && value >= 0 && value <= 1)) return null
  const position = fractions[depth] * total - 0.5
  const index = Math.min(total - 1, Math.max(0, Math.round(position)))
  fractions[depth] = (index + 0.5) / total
  return { fractions, index, relation: Math.abs(position - index) <= 0.02 ? 'exact' : 'nearest' }
}

/** A matching study ID alone does not bind a source CT to a prepared result. */
export function verifiedInspectionSource(result, { studyId, predictionSha256 } = {}) {
  const { manifest, measurement, urls } = result || {}
  const sourceSha256 = manifest?.files?.ct?.content_sha256
  if (!predictionSha256 || !sourceSha256 || manifest.case_id !== studyId
    || manifest?.files?.pred?.content_sha256 !== predictionSha256
    || measurement?.predictionSha256 !== predictionSha256
    || measurement?.ctSha256 !== sourceSha256
    || !urls?.ct || !urls?.pred) return null
  return { kind: 'source', series: manifest.source_series_label, calibratedHu: manifest.ct_intensity_units === 'HU' }
}
