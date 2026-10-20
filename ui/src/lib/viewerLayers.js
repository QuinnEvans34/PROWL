export const REVIEW_COLORS = {
  pred: {
    pancreas: '#26c5a6',
    lesion: '#f96363',
  },
  gt: {
    pancreas: '#38bdf8',
    lesion: '#fbbf24',
  },
  difference: {
    agreement: '#c4b5fd',
    predOnly: '#f43f5e',
    gtOnly: '#fbbf24',
  },
}

export const EVIDENCE_META = {
  ct: {
    label: 'Original CT',
    shortLabel: 'Original CT',
    description: 'Unannotated imaging context',
  },
  prediction: {
    label: 'Model prediction',
    shortLabel: 'Model prediction',
    description: 'Model-proposed contours',
  },
  truth: {
    label: 'Reference annotation',
    shortLabel: 'Reference',
    description: 'Independent JHU reference contours',
  },
  overlap: {
    label: 'Compare overlap',
    shortLabel: 'Compare overlap',
    description: 'Prediction and reference together',
  },
}

export function sourcesForEvidence(mode) {
  if (mode === 'prediction') return ['pred']
  if (mode === 'truth') return ['gt']
  if (mode === 'overlap') return ['pred', 'gt']
  return []
}

export function visibleSourcesForEvidence(mode, sourceFocus, layerVisibility) {
  const sources = sourcesForEvidence(mode)
  return sources.filter((source) => {
    if (!layerVisibility[source]) return false
    if (sourceFocus === 'difference') return false
    return true
  })
}

export function objectLabel(object) {
  if (!object) return 'All anatomy'
  if (object.source === 'difference') {
    const region = {
      agreement: 'Agreement',
      predOnly: 'Prediction only',
      gtOnly: 'Reference only',
    }[object.region] || 'Difference'
    return `${region} · ${object.anatomy}`
  }
  const source = object.source === 'gt' ? 'Reference' : 'Prediction'
  const anatomy = object.anatomy === 'lesion' ? 'lesion' : 'pancreas'
  return `${source} ${anatomy}`
}
