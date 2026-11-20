import { useEffect, useState } from 'react'

// Precomputed review aids for native-resolution studies.
// Producer: scripts/build_workbench_insights.py (schema prowl.workbench.insights.v1).
// Spec: docs/capstone/interface/WORKBENCH-RADIOLOGIST-TOOLSET-SPEC-20261120.md

const BASE = '/cases'

// Reference anatomy (PanTS annotations, not model output). Values match anatomy.nii.gz.
export const ANATOMY_STRUCTURES = Object.freeze([
  { value: 1, name: 'superior_mesenteric_artery', label: 'SMA', kind: 'artery', color: [244, 114, 182] },
  { value: 2, name: 'celiac_artery', label: 'Celiac artery', kind: 'artery', color: [232, 121, 249] },
  { value: 3, name: 'veins', label: 'Portal / SMV / splenic veins', kind: 'vein', color: [96, 165, 250] },
  { value: 4, name: 'aorta', label: 'Aorta', kind: 'artery', color: [248, 113, 113] },
  { value: 5, name: 'postcava', label: 'IVC', kind: 'vein', color: [129, 140, 248] },
  { value: 6, name: 'common_bile_duct', label: 'Common bile duct', kind: 'duct', color: [52, 211, 153] },
  { value: 7, name: 'pancreatic_duct', label: 'Pancreatic duct', kind: 'duct', color: [163, 230, 53] },
])

// Distance from the predicted lesion (MeVis-style risk colouring).
export const DISTANCE_BANDS = Object.freeze([
  { key: 'contact', label: '< 2 mm', color: [239, 68, 68] },
  { key: 'near', label: '2–5 mm', color: [251, 146, 60] },
  { key: 'close', label: '5–10 mm', color: [253, 224, 71] },
  // Context band: muted and translucent so the near bands and the pancreas read first.
  { key: 'far', label: '> 10 mm', color: [100, 116, 139], opacity: 0.38 },
])

// Uncertainty ramp over 0..80 (normalised entropy x100). Everything below the
// display threshold (20) is fully transparent, and transparent entries keep the
// amber RGB so linear filtering never produces a dark fringe at band edges.
export const CONFIDENCE_COLORMAP = 'prowl-uncertainty'
export const CONFIDENCE_RANGE = [0, 80]
export const CONFIDENCE_COLORMAP_LUT = {
  R: [217, 217, 217, 239, 251, 255], G: [70, 70, 70, 120, 191, 247], B: [20, 20, 20, 30, 36, 194],
  A: [0, 0, 150, 190, 225, 255], I: [0, 62, 70, 130, 195, 255],
}

export const rgb = color => `rgb(${color.join(' ')})`

export function anatomyColormap(alpha = 255) {
  return {
    R: [0, ...ANATOMY_STRUCTURES.map(item => item.color[0])],
    G: [0, ...ANATOMY_STRUCTURES.map(item => item.color[1])],
    B: [0, ...ANATOMY_STRUCTURES.map(item => item.color[2])],
    A: [0, ...ANATOMY_STRUCTURES.map(() => alpha)],
    I: [0, ...ANATOMY_STRUCTURES.map(item => item.value)],
    labels: ['Background', ...ANATOMY_STRUCTURES.map(item => item.label)],
  }
}

// 3D layers for reference anatomy. With a predicted lesion, vessels are split into
// distance bands; ducts keep their identity colour.
export function anatomyMeshLayers(meshFiles = {}) {
  const banded = Object.keys(meshFiles).some(key => key.includes('__'))
  const layers = []
  for (const structure of ANATOMY_STRUCTURES) {
    const base = `anatomy_${structure.name}`
    if (banded && structure.kind !== 'duct') {
      for (const band of DISTANCE_BANDS) {
        const path = meshFiles[`${base}__${band.key}`]
        if (path) layers.push({ key: `${base}__${band.key}`, path, color: band.color, opacity: band.opacity ?? 1, structure: structure.name, band: band.key })
      }
    } else if (meshFiles[base]) {
      layers.push({ key: base, path: meshFiles[base], color: structure.color, opacity: structure.kind === 'duct' ? 1 : 0.7, structure: structure.name, band: null })
    }
  }
  return { banded, layers }
}

export function normalizeInsights(value) {
  if (!value || value.schema !== 'prowl.workbench.insights.v1') return null
  const anatomy = Array.isArray(value.anatomy) ? value.anatomy : []
  const order = new Map(ANATOMY_STRUCTURES.map((item, index) => [item.name, index]))
  return {
    ...value,
    anatomy: [...anatomy].sort((a, b) => (order.get(a.name) ?? 99) - (order.get(b.name) ?? 99)),
    lesion: value.lesion || { present: false },
  }
}

export function useStudyInsights(caseData) {
  const path = caseData?.files?.insights
  const [state, setState] = useState({ status: path ? 'loading' : 'absent', insights: null, path })
  useEffect(() => {
    if (!path) {
      setState({ status: 'absent', insights: null, path })
      return undefined
    }
    let cancelled = false
    setState({ status: 'loading', insights: null, path })
    fetch(`${BASE}/${path}`, { cache: 'no-store' })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then(json => {
        if (cancelled) return
        const insights = normalizeInsights(json)
        setState({ status: insights ? 'ready' : 'unavailable', insights, path })
      })
      .catch(() => { if (!cancelled) setState({ status: 'unavailable', insights: null, path }) })
    return () => { cancelled = true }
  }, [path])
  return state.path === path ? state : { status: path ? 'loading' : 'absent', insights: null, path }
}

const CATEGORY_TEXT = { none: 'no contact', abutment: 'abutment', encasement: 'encasement' }
const LOCATION_TEXT = { head: 'pancreatic head', body: 'pancreatic body', tail: 'pancreatic tail' }

export function contactCategoryLabel(category) {
  return CATEGORY_TEXT[category] || 'not assessed'
}

const mm = value => (Number.isFinite(value) ? `${value.toFixed(1)} mm` : 'n/a')
const cm = value => (Number.isFinite(value) ? `${(value / 10).toFixed(1)} cm` : 'n/a')

// SAR/APA-shaped draft built only from displayed values. Plain text for copying.
export function structuredSummaryText(insights, { studyLabel = '' } = {}) {
  if (!insights) return ''
  const { lesion, anatomy } = insights
  const lines = [`PROWL structured draft — ${studyLabel || insights.case_id}`, 'Draft for radiologist review. Model outline + reference anatomy; not a diagnosis.', '']
  lines.push('MORPHOLOGY')
  if (!lesion?.present) {
    lines.push('- No lesion outlined by the model.')
  } else {
    lines.push(`- Attenuation: ${lesion.attenuation || 'not assessed'}${Number.isFinite(lesion.attenuation_delta_hu) ? ` (${lesion.attenuation_delta_hu > 0 ? '+' : ''}${lesion.attenuation_delta_hu} HU vs pancreas)` : ''}`)
    lines.push(`- Size: ${cm(lesion.long_axis_mm)} × ${cm(lesion.short_axis_mm)} (axial long × short axis); outline volume ${lesion.volume_ml?.toFixed?.(1) ?? 'n/a'} mL`)
    lines.push(`- Location: ${LOCATION_TEXT[lesion.location] || 'not assessed'}`)
  }
  const ducts = anatomy.filter(item => item.kind === 'duct')
  for (const duct of ducts) {
    if (duct.annotated === false) lines.push(`- ${duct.label}: not annotated`)
    else if (Number.isFinite(duct.max_calibre_mm)) lines.push(`- ${duct.label}: ${mm(duct.max_calibre_mm)}${duct.dilated ? ' (dilated)' : ''}`)
  }
  lines.push('', 'VASCULAR RELATIONSHIP (model lesion vs reference vessels)')
  const vessels = anatomy.filter(item => item.kind !== 'duct' && item.annotated !== false)
  if (!lesion?.present) lines.push('- Not applicable without a predicted lesion.')
  else for (const vessel of vessels) {
    const angle = Number.isFinite(vessel.contact_angle_deg) && vessel.contact_angle_deg > 0 ? `, ${Math.round(vessel.contact_angle_deg)}°` : ''
    lines.push(`- ${vessel.label}: ${contactCategoryLabel(vessel.contact_category)}${angle}; closest ${mm(vessel.min_distance_mm)}`)
  }
  lines.push('', 'Generated by PROWL. Contact and distance relate the model outline to dataset reference anatomy and are review aids only.')
  return lines.join('\n')
}
