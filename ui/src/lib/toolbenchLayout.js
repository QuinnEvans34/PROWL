import { useCallback, useEffect, useState } from 'react'

export const TOOLBENCH_LAYOUT_KEY = 'prowl.toolbench.layout.v1'
export const TOOLBENCH_LAYOUT_VERSION = 1
export const TOOLBENCH_PLANES = Object.freeze(['axial', 'coronal', 'sagittal'])

// Presentation preferences only. Study identity, imaging state and review text
// belong to their existing session models and must never enter this record.
export const DEFAULT_TOOLBENCH_LAYOUT = Object.freeze({
  studyListOpen: false,
  panelOpen: true,
  panelWidth: 320,
  studyListWidth: 208,
  primaryShare: 64,
  secondaryShare: 50,
  hiddenPlanes: Object.freeze([]),
  maximizedPlane: null,
  measurementsVisible: true,
  linked: true,
})

function numberInRange(value, fallback, min, max) {
  return typeof value === 'number' && Number.isFinite(value)
    ? Math.min(max, Math.max(min, value))
    : fallback
}

function booleanOrDefault(value, fallback) {
  return typeof value === 'boolean' ? value : fallback
}

export function sanitizeToolbenchLayout(value) {
  const candidate = value && typeof value === 'object' && !Array.isArray(value) ? value : {}
  let hiddenPlanes = Array.isArray(candidate.hiddenPlanes)
    ? TOOLBENCH_PLANES.filter(plane => candidate.hiddenPlanes.includes(plane))
    : []
  // Always leave an imaging plane available, including after malformed storage.
  if (hiddenPlanes.length === TOOLBENCH_PLANES.length) hiddenPlanes = []
  const maximizedPlane = TOOLBENCH_PLANES.includes(candidate.maximizedPlane)
    && !hiddenPlanes.includes(candidate.maximizedPlane) ? candidate.maximizedPlane : null
  return {
    studyListOpen: booleanOrDefault(candidate.studyListOpen, DEFAULT_TOOLBENCH_LAYOUT.studyListOpen),
    panelOpen: booleanOrDefault(candidate.panelOpen, DEFAULT_TOOLBENCH_LAYOUT.panelOpen),
    panelWidth: numberInRange(candidate.panelWidth, DEFAULT_TOOLBENCH_LAYOUT.panelWidth, 260, 520),
    studyListWidth: numberInRange(candidate.studyListWidth, DEFAULT_TOOLBENCH_LAYOUT.studyListWidth, 160, 320),
    primaryShare: numberInRange(candidate.primaryShare, DEFAULT_TOOLBENCH_LAYOUT.primaryShare, 40, 80),
    secondaryShare: numberInRange(candidate.secondaryShare, DEFAULT_TOOLBENCH_LAYOUT.secondaryShare, 25, 75),
    hiddenPlanes,
    maximizedPlane,
    measurementsVisible: booleanOrDefault(candidate.measurementsVisible, DEFAULT_TOOLBENCH_LAYOUT.measurementsVisible),
    linked: booleanOrDefault(candidate.linked, DEFAULT_TOOLBENCH_LAYOUT.linked),
  }
}

function preferenceStorage(storage) {
  if (storage !== undefined) return storage
  return typeof window !== 'undefined' ? window.localStorage : null
}

export function readToolbenchLayout(storage) {
  try {
    const saved = JSON.parse(preferenceStorage(storage)?.getItem(TOOLBENCH_LAYOUT_KEY) || 'null')
    return saved?.version === TOOLBENCH_LAYOUT_VERSION
      ? sanitizeToolbenchLayout(saved.layout)
      : sanitizeToolbenchLayout(null)
  } catch {
    // Private browsing, a storage quota or invalid JSON must not block review.
    return sanitizeToolbenchLayout(null)
  }
}

export function saveToolbenchLayout(value, storage) {
  const layout = sanitizeToolbenchLayout(value)
  try {
    preferenceStorage(storage)?.setItem(TOOLBENCH_LAYOUT_KEY, JSON.stringify({
      version: TOOLBENCH_LAYOUT_VERSION,
      layout,
    }))
  } catch {
    // The current session still keeps the chosen layout when storage is denied.
  }
  return layout
}

export function useToolbenchLayout(storage) {
  // Initialize before the first render so returning reviewers see their layout
  // immediately, without an initial default layout that shifts after mounting.
  const [layout, setLayoutState] = useState(() => readToolbenchLayout(storage))
  const setLayout = useCallback(update => {
    setLayoutState(current => {
      const patch = typeof update === 'function' ? update(current) : update
      return sanitizeToolbenchLayout({ ...current, ...patch })
    })
  }, [])
  const resetLayout = useCallback(() => setLayoutState(sanitizeToolbenchLayout(null)), [])

  useEffect(() => { saveToolbenchLayout(layout, storage) }, [layout, storage])

  return [layout, setLayout, resetLayout]
}
