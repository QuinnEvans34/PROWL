import React, { useState } from 'react'
import { expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewSummary from '../src/components/ReviewSummary.jsx'
import { generateObservations, predictionIdentity } from '../src/lib/summaryDraft.js'

const saved = predictionIdentity({ hasPrediction: true, liveResult: null, modelLabel: 'Model v1' })
const facts = { hasPrediction: true, lesionFlagged: true, volumeMm3: 15629.6, diameterMm: 31, comparison: null }

function Harness({ initialStudy = 'S1', prediction = saved, initialFacts = facts }) {
  const [drafts, setDrafts] = useState({})
  const [study, setStudy] = useState(initialStudy)
  const [f, setFacts] = useState(initialFacts)
  return <>
    <button onClick={() => setStudy(study === 'S1' ? 'S2' : 'S1')}>switch study</button>
    <button onClick={() => setFacts({ ...f, comparison: { pancreas: 0.855, lesion: 0.919, bothLesionAbsent: false } })}>compare</button>
    <ReviewSummary studyId={study} studyLabel={study} seriesLabel="Abdomen CT" prediction={prediction} facts={f}
      drafts={drafts} onChange={(key, draft) => setDrafts((d) => { const n = { ...d }; if (draft) n[key] = draft; else delete n[key]; return n })} />
  </>
}

it('never invents observations before a prediction exists', () => {
  const text = generateObservations({ hasPrediction: false, studyLabel: 'S', seriesLabel: 'CT', prediction: predictionIdentity({ hasPrediction: false }) })
  expect(text).toMatch(/no model-derived observations/)
  expect(text).not.toMatch(/lesion|cm³|Dice/i)
})

it('labels derived values and refuses healthy conclusions from an empty prediction', () => {
  const flagged = generateObservations({ ...facts, studyLabel: 'S', seriesLabel: 'CT', prediction: saved })
  expect(flagged).toMatch(/15\.63 cm³/)
  expect(flagged).toMatch(/derived; not a measured width or length/)
  const empty = generateObservations({ ...facts, lesionFlagged: false, studyLabel: 'S', seriesLabel: 'CT', prediction: saved })
  expect(empty).toMatch(/does not establish that no lesion is present/)
  expect(empty).not.toMatch(/normal|healthy|benign/i)
})

it('keeps edits across study switches and requires a choice before regenerating over them', async () => {
  const user = userEvent.setup()
  render(<Harness />)
  await user.click(screen.getByRole('button', { name: /Start draft from findings/ }))
  const observations = screen.getByLabelText(/Draft observations/)
  await user.type(observations, ' Reviewer wording.')
  await user.type(screen.getByLabelText(/Your notes/), 'Check the duct.')
  expect(screen.getByText('Unsaved · session only')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'switch study' }))
  expect(screen.getByRole('button', { name: /Start draft from findings/ })).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'switch study' }))
  expect(screen.getByLabelText(/Draft observations/).value).toMatch(/Reviewer wording\.$/)
  expect(screen.getByLabelText(/Your notes/).value).toBe('Check the duct.')
  await user.click(screen.getByRole('button', { name: 'compare' }))
  expect(screen.getByText(/findings changed since this draft was generated/)).toBeTruthy()
  await user.click(screen.getByRole('button', { name: /Regenerate/ }))
  expect(screen.getByText(/would replace your edited observations/)).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Keep my edits' }))
  expect(screen.getByLabelText(/Draft observations/).value).toMatch(/Reviewer wording\.$/)
  expect(screen.getByLabelText(/Your notes/).value).toBe('Check the duct.')
})

it('offers no durable save without a persistence receipt contract', async () => {
  const user = userEvent.setup()
  render(<Harness />)
  await user.click(screen.getByRole('button', { name: /Start draft from findings/ }))
  expect(screen.getByRole('button', { name: 'Save review' }).disabled).toBe(true)
  expect(screen.queryByText(/^Saved$/)).toBeNull()
  expect(screen.getAllByText(/Durable saving isn’t connected yet/).length).toBeGreaterThan(0)
})

it('keeps a draft written for a different prediction separate and labeled', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<Harness />)
  await user.click(screen.getByRole('button', { name: /Start draft from findings/ }))
  await user.type(screen.getByLabelText(/Your notes/), 'Earlier note')
  const live = predictionIdentity({ hasPrediction: true, liveResult: { source: 'live', scoredAt: '10:00' }, modelLabel: 'Model v1' })
  rerender(<Harness prediction={live} />)
  expect(screen.getByText('Draft for an earlier prediction')).toBeTruthy()
  expect(screen.getByText(/“Saved prediction · Model v1” is kept/)).toBeTruthy()
  expect(screen.getByRole('button', { name: /Start draft from findings/ })).toBeTruthy()
})
