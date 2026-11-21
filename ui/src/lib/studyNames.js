import { useCallback, useEffect, useState } from 'react'

// Display names for studies. The dataset ID stays the identity everywhere (routes,
// files, provenance); a name is a local, per-browser label a reviewer can change.
const STORAGE_KEY = 'prowl.studyNames.v1'
const EVENT = 'prowl-study-names'

function readNames() {
  try {
    const value = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}')
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {}
  } catch {
    return {}
  }
}

export function defaultStudyName(caseId) {
  if (!caseId) return 'Study'
  const match = /^PanTS_0*(\d+)$/.exec(caseId)
  return match ? `Case ${match[1]}` : caseId
}

export function studyDisplayName(caseId, names = readNames()) {
  const custom = typeof names?.[caseId] === 'string' ? names[caseId].trim() : ''
  return custom || defaultStudyName(caseId)
}

// "CT abdomen · Arterial phase · M, 77" from the de-identified study description.
export function studyDescriptor(caseInfo) {
  const study = caseInfo?.study
  if (!study) return 'CT abdomen'
  const parts = ['CT abdomen']
  if (study.phase) parts.push(/phase|contrast/i.test(study.phase) ? study.phase : `${study.phase} phase`)
  const demographic = [study.sex, Number.isFinite(study.age) ? Math.round(study.age) : null].filter(Boolean).join(', ')
  if (demographic) parts.push(demographic)
  return parts.join(' · ')
}

export function useStudyNames() {
  const [names, setNames] = useState(readNames)
  useEffect(() => {
    const sync = () => setNames(readNames())
    window.addEventListener('storage', sync)
    window.addEventListener(EVENT, sync)
    return () => { window.removeEventListener('storage', sync); window.removeEventListener(EVENT, sync) }
  }, [])
  const rename = useCallback((caseId, value) => {
    const next = { ...readNames() }
    const name = String(value || '').trim().slice(0, 60)
    if (!name || name === defaultStudyName(caseId)) delete next[caseId]
    else next[caseId] = name
    try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { /* private mode: session only */ }
    setNames(next)
    window.dispatchEvent(new Event(EVENT))
  }, [])
  return [names, rename]
}
