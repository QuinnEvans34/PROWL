import React from 'react'
import { expect, it, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel from '../src/components/LiteratureSearchPanel.jsx'
import config from '../../configs/evidence/development-search-v1.json'

// Synthetic, schema-valid search response (no real literature content).
function response(request) {
  return { schema_version: 'prowl-development-answer-response-v1', request_id: request.request_id,
    question: request.question, collection: config.collection, generation: 'unavailable', answer: null,
    target: { manifest_sha256: config.manifest.sha256, inventory: { content_sha256: config.corpus_content_sha256 } },
    state: 'evidence_unassessed', reason: null,
    evidence: [{ rank: 1, score: 0.8, record: {
      text: 'Artificial source excerpt for testing provenance display.',
      passage: { passage_id: `psg:${'a'.repeat(64)}`, section_id: 'body-1', start: 0, end: 55 },
      citation: { title: 'Artificial pancreas reference', year: '2020', pmcid: 'PMC123', pmid: '123', authors: ['Example'], attribution: 'Test', doi: 'test' },
      rights: { permissions: { display_snippet: true } },
    } }],
  }
}

it('states literature-only scope and never auto-submits a suggested question', async () => {
  const user = userEvent.setup()
  const search = vi.fn()
  render(<LiteratureSearchPanel variant="panel" search={search} contextKey="S1" contextLabel="Study 1" />)
  expect(screen.getByText(/Literature only · Scan context not connected/)).toBeTruthy()
  expect(screen.getByText(/do not remember earlier questions/)).toBeTruthy()
  const suggestion = screen.getAllByRole('button').find((b) => b.closest('[aria-label="Suggested general questions"]'))
  await user.click(suggestion)
  expect(screen.getByLabelText('Literature question').value).toBe(suggestion.textContent)
  expect(search).not.toHaveBeenCalled()
})

it('discards a late answer when the study changes mid-request and keeps the question', async () => {
  const user = userEvent.setup()
  let resolve
  const search = vi.fn((request) => new Promise((r) => { resolve = () => r(response(request)) }))
  const pending = vi.fn()
  const { rerender } = render(<LiteratureSearchPanel variant="panel" search={search} contextKey="S1" contextLabel="Study 1" onPendingChange={pending} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatitis imaging')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(pending).toHaveBeenLastCalledWith(true)
  rerender(<LiteratureSearchPanel variant="panel" search={search} contextKey="S2" contextLabel="Study 2" onPendingChange={pending} />)
  expect(search.mock.calls[0][1].aborted).toBe(true)
  expect(screen.getByText(/cancelled because you switched studies/)).toBeTruthy()
  await act(async () => { resolve() })
  expect(screen.queryByRole('article')).toBeNull()
  expect(screen.queryByText('Artificial source excerpt for testing provenance display.')).toBeNull()
  expect(screen.getByLabelText('Literature question').value).toBe('Pancreatitis imaging')
  expect(pending).toHaveBeenLastCalledWith(false)
})

it('labels a completed general answer when the reviewer moves to another study', async () => {
  const user = userEvent.setup()
  const search = vi.fn(async (request) => response(request))
  const { rerender } = render(<LiteratureSearchPanel variant="panel" search={search} contextKey="S1" contextLabel="Study 1" />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatitis imaging')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText('Retrieved passages')).toBeTruthy()
  expect(screen.queryByText(/asked while reviewing/)).toBeNull()
  rerender(<LiteratureSearchPanel variant="panel" search={search} contextKey="S2" contextLabel="Study 2" />)
  expect(screen.getByText(/asked while reviewing Study 1\. Not about the current study/)).toBeTruthy()
})
