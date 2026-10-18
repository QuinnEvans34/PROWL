// Review summary drafts — FRONTEND model only (08 §7). Not a scientific schema, not a
// clinical report, and not a durable review record.
//
// A draft is keyed by study + series + prediction identity so a draft written against one
// prediction is never shown as current for another. Human text (observations edits and
// notes) is stored separately from the generated text it started from.

export function predictionIdentity({ hasPrediction, liveResult, modelLabel }) {
  if (!hasPrediction) return { key: 'none', label: 'No prediction displayed' }
  if (liveResult?.source === 'live') return { key: `live:${liveResult.scoredAt}`, label: `Live analysis · ${liveResult.scoredAt}` }
  return { key: `saved:${modelLabel}`, label: `Saved prediction · ${modelLabel}` }
}

export function draftKey(studyId, seriesKey, predictionKey) {
  return `${studyId}::${seriesKey}::${predictionKey}`
}

function fixed(value, digits) {
  return Number.isFinite(value) ? value.toFixed(digits) : null
}

// Deterministic assembly from validated facts only. No inference, normal ranges,
// impressions, reassurance, or literature claims are ever inserted.
export function generateObservations(facts) {
  const lines = []
  lines.push(`Study: ${facts.studyLabel} · ${facts.seriesLabel}`)
  lines.push(`Prediction: ${facts.prediction.label}`)
  lines.push('')
  if (!facts.hasPrediction) {
    lines.push('No model prediction has been displayed for this study, so no model-derived observations are included.')
  } else {
    lines.push('Model-derived observations (for reviewer verification):')
    lines.push('- Pancreas: model outline present. Pancreas volume is not published in this prediction package.')
    if (facts.lesionFlagged) {
      const volume = fixed(facts.volumeMm3 / 1000, 2)
      const diameter = facts.diameterMm ? `, equivalent spherical diameter ${facts.diameterMm} mm (derived; not a measured width or length)` : ''
      lines.push(`- Possible lesion proposed by the model. ${volume ? `Predicted mask volume ${volume} cm³${diameter}.` : 'Predicted mask volume unavailable.'}`)
    } else {
      lines.push('- No lesion was predicted by the model. This does not establish that no lesion is present.')
    }
    if (facts.comparison) {
      const pancreas = fixed(facts.comparison.pancreas, 3)
      const lesion = facts.comparison.bothLesionAbsent ? 'lesion absent in both' : fixed(facts.comparison.lesion, 3)
      lines.push(`- Agreement with reference annotation (Dice): pancreas ${pancreas ?? 'unavailable'}, lesion ${lesion ?? 'unavailable'}.`)
    }
  }
  lines.push('')
  lines.push('Limitations: Research use only. Model outlines are proposals that require human review. This draft is not a diagnosis or a signed report.')
  return lines.join('\n')
}

export function createDraft({ key, studyId, prediction, generated }) {
  return {
    key,
    studyId,
    predictionKey: prediction.key,
    predictionLabel: prediction.label,
    generated,
    observations: generated,
    notes: '',
    createdAt: new Date().toISOString(),
    persistence: 'session',
  }
}

export function isEdited(draft) {
  return Boolean(draft) && draft.observations !== draft.generated
}

export function hasHumanContent(draft) {
  return Boolean(draft) && (isEdited(draft) || draft.notes.trim().length > 0)
}

export function summaryText(draft) {
  return `${draft.observations.trim()}\n\nReviewer notes:\n${draft.notes.trim() || '(none)'}\n\nDraft only · session-only · not saved · not a signed report`
}
