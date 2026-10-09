import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import GuidedEvidencePanel from '../src/components/GuidedEvidencePanel.jsx'
import { evidenceFixture, requestEvidence, validateEvidence } from '../src/lib/guidedEvidence.js'

function responseFor(request) {
  const q = evidenceFixture.questions.find(q => q.id === request.question_id)
  const passages = q.passage_ids.map(id => evidenceFixture.passages.find(p => p.id === id))
  return {
    schema_version: 'prowl-guided-fixture-response-v1', response_id: request.request_id,
    request, question: q.label, state: q.state, message: q.message,
    claims: passages.map((p, i) => ({ id: `claim-${i + 1}`, text: p.text, passage_id: p.id })),
    citations: passages, content_sha256: 'a'.repeat(64),
    provenance: { corpus: evidenceFixture.version, adapter: 'fixed-extractive-v1', model: null, index: null },
  }
}

it('shows exact supporting passage, provenance and a saved artifact link', async () => {
  const user = userEvent.setup()
  render(<GuidedEvidencePanel loadResponse={async request => responseFor(request)} />)
  await user.click(screen.getByText('Guided evidence questions'))
  await user.click(screen.getByRole('button', { name: 'Ask and save fixture response' }))
  expect(await screen.findByRole('heading', { name: 'Supported by the selected fixture' })).toBeTruthy()
  await user.click(screen.getByText('Supporting passage: Synthetic reviewer workflow'))
  expect(screen.getAllByText(evidenceFixture.passages[0].text)).toHaveLength(2)
  expect(screen.getByRole('link', { name: 'Download saved response JSON' }).getAttribute('href')).toMatch(/^\/evidence-fixture\/responses\//)
})

it.each(['measurement', 'diagnosis-boundary'])('renders %s without claims or invented citations', async id => {
  const user = userEvent.setup()
  render(<GuidedEvidencePanel loadResponse={async request => responseFor(request)} />)
  await user.click(screen.getByText('Guided evidence questions'))
  await user.selectOptions(screen.getByLabelText('Reviewer question'), id)
  await user.click(screen.getByRole('button', { name: 'Ask and save fixture response' }))
  expect(await screen.findByText(evidenceFixture.questions.find(q => q.id === id).message)).toBeTruthy()
  expect(screen.queryByText(/Supporting passage:/)).toBeNull()
})

it('keeps a failed save visibly unconfirmed and retries the identical request', async () => {
  const user = userEvent.setup()
  const load = vi.fn().mockRejectedValueOnce(new Error('offline')).mockImplementation(async req => responseFor(req))
  render(<GuidedEvidencePanel loadResponse={load} />)
  await user.click(screen.getByText('Guided evidence questions'))
  await user.click(screen.getByRole('button', { name: 'Ask and save fixture response' }))
  expect(await screen.findByRole('alert')).toBeTruthy()
  expect(screen.queryByRole('link')).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Retry same request' }))
  await screen.findByRole('article')
  expect(load.mock.calls[1][0]).toEqual(load.mock.calls[0][0])
})

it('aborts a pending request on case switch and never shows its late result', async () => {
  const user = userEvent.setup()
  let finish
  let signal
  const load = (req, incoming) => { signal = incoming; return new Promise(resolve => { finish = () => resolve(responseFor(req)) }) }
  const { rerender } = render(<GuidedEvidencePanel key="case-a" loadResponse={load} />)
  await user.click(screen.getByText('Guided evidence questions'))
  await user.click(screen.getByRole('button', { name: 'Ask and save fixture response' }))
  rerender(<GuidedEvidencePanel key="case-b" loadResponse={load} />)
  expect(signal.aborted).toBe(true)
  finish()
  await waitFor(() => expect(screen.queryByRole('article')).toBeNull())
})

it('rejects mismatched identities and unsupported claim/citation changes', () => {
  const request = { request_id: 'example', question_id: 'workflow' }
  for (const mutate of [r => { r.response_id = 'other' }, r => { r.claims[0].text = 'Diagnosis' }, r => { r.citations = [] }, r => { r.state = 'confident' }]) {
    const response = structuredClone(responseFor(request))
    mutate(response)
    expect(() => validateEvidence(response, request)).toThrow()
  }
})

it('sends no case data and treats non-JSON or service failures as unavailable', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: false })
  vi.stubGlobal('fetch', fetch)
  const request = { request_id: 'example', question_id: 'workflow' }
  await expect(requestEvidence(request)).rejects.toThrow()
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual(request)
  fetch.mockResolvedValue({ ok: true, json: async () => { throw new Error('HTML response') } })
  await expect(requestEvidence(request)).rejects.toThrow()
})
