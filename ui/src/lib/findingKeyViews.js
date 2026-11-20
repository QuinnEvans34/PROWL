export const KEY_VIEWS_STORAGE_KEY = 'prowl.workbench.key-views.v1'
export const KEY_VIEW_EXPORT_LIMIT = 16000
export const KEY_VIEW_NOTE_LIMIT = 1200
const MAX_RECORDS = 48
const VERSION = 1
const SHA256 = /^[a-f0-9]{64}$/
const STUDY_ID = /^[A-Za-z0-9_-]{1,96}$/
const RECORD_ID = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/
const PLANES = ['axial', 'coronal', 'sagittal']

const present = (value) => value !== undefined && value !== null
const between = (value, min, max) => Number.isFinite(value) && value >= min && value <= max
const vector = (value, length) => Array.isArray(value) && value.length === length
  && value.every((coordinate) => between(coordinate, -1e6, 1e6))
const integer = (value) => Number.isSafeInteger(value) && value >= 0

export function keyViewScope(scope) {
  if (typeof scope?.studyId !== 'string' || !STUDY_ID.test(scope.studyId)
    || typeof scope.ctSha256 !== 'string' || !SHA256.test(scope.ctSha256)
    || typeof scope.predictionSha256 !== 'string' || !SHA256.test(scope.predictionSha256)
    || (present(scope.manifestHash) && (typeof scope.manifestHash !== 'string' || !SHA256.test(scope.manifestHash)))) return null
  return {
    studyId: scope.studyId,
    ctSha256: scope.ctSha256,
    predictionSha256: scope.predictionSha256,
    ...(present(scope.manifestHash) ? { manifestHash: scope.manifestHash } : {}),
  }
}

export function matchesKeyViewScope(scope, record) {
  const valid = keyViewScope(scope)
  return Boolean(valid && valid.studyId === record?.scope?.studyId
    && valid.ctSha256 === record.scope.ctSha256
    && valid.predictionSha256 === record.scope.predictionSha256
    && valid.manifestHash === record.scope.manifestHash)
}

function findingIdentity(finding) {
  if (finding?.anatomy === 'pancreas' && finding.id === 'pancreas') {
    return { anatomy: 'pancreas', id: 'pancreas' }
  }
  if (finding?.anatomy !== 'lesion' || !integer(finding.id)) return null
  return { anatomy: 'lesion', id: finding.id,
    ...(integer(finding.ordinal) && finding.ordinal > 0 ? { ordinal: finding.ordinal } : {}) }
}

function framing2d(value) {
  return vector(value, 4) && between(value[3], 0.25, 12)
}

function framing3d(camera) {
  if (!between(camera?.azimuth, -1e6, 1e6) || !between(camera.elevation, -90, 90)
    || !between(camera.scale, 0.45, 4) || (present(camera.pivot) && !vector(camera.pivot, 3))) return null
  return {
    azimuth: camera.azimuth, elevation: camera.elevation, scale: camera.scale,
    ...(present(camera.pivot) ? { pivot: [...camera.pivot] } : {}),
  }
}

const VIEW_SETTINGS = {
  sliceIndex: integer,
  seriesKey: (value) => ['prepared', 'source', 'abdomen', 'full'].includes(value),
  sourceCtSha256: (value) => typeof value === 'string' && SHA256.test(value),
  ctWindow: (value) => ['soft', 'contrast', 'wide'].includes(value),
  ctRange: (value) => vector(value, 2) && value[0] < value[1],
  overlayMode: (value) => ['outline', 'fill', 'ct', 'ct-only', 'off'].includes(value),
  overlayOpacity: (value) => between(value, 0, 1),
  ctOpacity: (value) => between(value, 0, 1),
  clipEnabled: (value) => typeof value === 'boolean',
  clipProgress: (value) => between(value, 0, 100),
  clipDirection: (value) => ['frontToBack', 'backToFront'].includes(value),
  scene3d: (value) => ['full', 'region', 'surfaces'].includes(value),
  viewMode: (value) => ['2d', '3d', 'split', 'inspect'].includes(value),
  showFull: (value) => typeof value === 'boolean',
  show3dCalipers: (value) => typeof value === 'boolean',
  showSliceIn3d: (value) => typeof value === 'boolean',
  pan2Dxyzmm: framing2d,
}

function viewSettings(view) {
  if (!PLANES.includes(view?.plane) || !vector(view.worldMm, 3)) return null
  const next = { plane: view.plane, worldMm: [...view.worldMm] }
  for (const [key, validate] of Object.entries(VIEW_SETTINGS)) {
    const value = view[key]
    if (!present(value)) continue
    if (!validate(value)) return null
    next[key] = Array.isArray(value) ? [...value] : value
  }
  if (present(view.camera)) {
    next.camera = framing3d(view.camera)
    if (!next.camera) return null
  }
  return next
}

function checkedRecord(value) {
  if (typeof value?.id !== 'string' || !RECORD_ID.test(value.id)
    || typeof value.createdAt !== 'string' || value.createdAt.length !== 24
    || !Number.isFinite(Date.parse(value.createdAt))) return null
  const scope = keyViewScope(value.scope)
  const finding = findingIdentity(value.finding)
  const view = viewSettings(value.view)
  if (!scope || !finding || !view) return null
  return { id: value.id, createdAt: value.createdAt, scope, finding, view }
}

export function createFindingKeyView(scope, finding, view) {
  return checkedRecord({ id: crypto.randomUUID(), createdAt: new Date().toISOString(), scope, finding, view })
}

function browserStorage(storage) {
  return storage === undefined ? window.localStorage : storage
}

export function readFindingKeyViews(storage) {
  try {
    const raw = browserStorage(storage).getItem(KEY_VIEWS_STORAGE_KEY)
    const saved = raw && raw.length <= KEY_VIEW_EXPORT_LIMIT * MAX_RECORDS && JSON.parse(raw)
    if (saved?.version !== VERSION || !Array.isArray(saved.records)) return []
    return saved.records.slice(0, MAX_RECORDS).map(checkedRecord).filter(Boolean)
  } catch {
    return []
  }
}

export function saveFindingKeyView(record, storage) {
  const value = checkedRecord(record)
  if (!value) throw new Error('The current image settings could not be captured.')
  const records = [value, ...readFindingKeyViews(storage).filter((item) => item.id !== value.id)].slice(0, MAX_RECORDS)
  try {
    browserStorage(storage).setItem(KEY_VIEWS_STORAGE_KEY, JSON.stringify({ version: VERSION, records }))
  } catch {
    throw new Error('This browser could not save the key view.')
  }
  return records
}

export function exportFindingKeyView(record, note = '') {
  const view = checkedRecord(record)
  if (!view || typeof note !== 'string' || note.length > KEY_VIEW_NOTE_LIMIT) {
    throw new Error('The key view could not be exported.')
  }
  return JSON.stringify({ version: VERSION, keyView: view, reviewerNote: note }, null, 2)
}

export function importFindingKeyView(text) {
  if (typeof text !== 'string' || text.length > KEY_VIEW_EXPORT_LIMIT) throw new Error('The key view file is too large.')
  const invalidFile = 'This file is not a supported PROWL key view.'
  let data
  try { data = JSON.parse(text) } catch { throw new Error(invalidFile) }
  const keyView = checkedRecord(data?.keyView)
  if (data?.version !== VERSION || !keyView
    || typeof data.reviewerNote !== 'string' || data.reviewerNote.length > KEY_VIEW_NOTE_LIMIT) throw new Error(invalidFile)
  return { keyView, reviewerNote: data.reviewerNote }
}
