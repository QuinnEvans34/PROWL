import React from 'react'
import { expect, it, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel, { validateSearch } from '../src/components/LiteratureSearchPanel.jsx'
import config from '../../configs/evidence/development-search-v1.json'
function response(request, state = 'evidence_unassessed') {
  return { schema_version: 'prowl-development-search-response-v1', request_id: request.request_id,
    question: request.question, collection: config.collection, generation: 'not_called', answer: null,
    target: { manifest_sha256: config.manifest.sha256, inventory: { content_sha256: config.corpus_content_sha256 } },
    state, reason: state === 'not_searched' ? 'case_context_unavailable' : null,
    evidence: state === 'evidence_unassessed' ? [{ rank: 1, score: .8, record: {
      text: 'Artificial source excerpt for testing provenance display.',
      passage: { passage_id: `psg:${'a'.repeat(64)}`, section_id: 'body-1', start: 0, end: 55 },
      citation: { title: 'Artificial pancreas reference', year: '2020', pmcid: 'PMC123', pmid: '123', authors: ['Example'], attribution: 'Test', doi: 'test' },
      rights: { permissions: { display_snippet: true } },
    } }] : [],
  }
}
it('submits typed text and opens evidence with a source link', async () => {
  const user = userEvent.setup(), search = vi.fn(async r => response(r))
  render(<LiteratureSearchPanel search={search} />)
  expect(screen.getByRole('button', { name: 'Search literature' }).disabled).toBe(true)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatitis imaging')
  await user.click(screen.getByRole('button', { name: 'Search literature' }))
  expect(await screen.findByText('Retrieved passages')).toBeTruthy()
  expect(search.mock.calls[0][0].question).toBe('Pancreatitis imaging')
  expect(Object.keys(search.mock.calls[0][0]).sort()).toEqual(['question', 'request_id', 'schema_version'])
  expect(screen.getByText('Artificial source excerpt for testing provenance display.')).toBeTruthy()
  expect(screen.queryByRole('link', { name: /Read full source/ })).toBeNull()
  await user.click(screen.getByRole('button', { name: 'View source 1' }))
  expect(document.activeElement.textContent).toContain('Artificial pancreas reference')
  expect(screen.getByRole('link', { name: /Read full source/ }).href).toBe('https://pmc.ncbi.nlm.nih.gov/articles/PMC123/')
  expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
  await user.click(screen.getByRole('button', { name: 'Read passages' }))
  expect(screen.queryByRole('link', { name: /Read full source/ })).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Sources (1)' }))
  expect(screen.getByRole('region', { name: 'Sources' })).toBeTruthy()
  await user.type(screen.getByLabelText('Literature question'), ' findings')
  expect(screen.queryByRole('article')).toBeNull()
})
it('retries after service failure', async () => {
  const user = userEvent.setup(), search = vi.fn().mockRejectedValueOnce(new Error('offline')).mockImplementation(async r => response(r, 'no_results'))
  render(<LiteratureSearchPanel search={search} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreas size')
  await user.click(screen.getByRole('button', { name: 'Search literature' }))
  expect(await screen.findByRole('alert')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Retry search' }))
  expect(await screen.findByText('No passages found')).toBeTruthy()
})
it('discards old responses after question changes', async () => {
  const user = userEvent.setup(); let finish, oldRequest
  const search = vi.fn(r => { oldRequest = r; return new Promise(resolve => { finish = resolve }) })
  render(<LiteratureSearchPanel search={search} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatitis')
  await user.click(screen.getByRole('button', { name: 'Search literature' }))
  await user.type(screen.getByLabelText('Literature question'), ' CT')
  await act(async () => finish(response(oldRequest)))
  expect(screen.queryByRole('article')).toBeNull()
  expect(search.mock.calls[0][1].aborted).toBe(true)
})
it('cancels pending work', async () => {
  const user = userEvent.setup(), search = vi.fn(() => new Promise(() => {}))
  render(<LiteratureSearchPanel search={search} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatic cancer')
  await user.click(screen.getByRole('button', { name: 'Search literature' }))
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(search.mock.calls[0][1].aborted).toBe(true)
  expect(screen.getByRole('button', { name: 'Search literature' }).disabled).toBe(false)
})
it('explains case measurement limits without showing evidence', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => response(r, 'not_searched')} />)
  await user.type(screen.getByLabelText('Literature question'), 'What is the size of this pancreas?')
  await user.click(screen.getByRole('button', { name: 'Search literature' }))
  expect(await screen.findByText(/does not have access to your scan/)).toBeTruthy()
  expect(screen.queryByRole('link')).toBeNull()
})
it.each(['request', 'corpus', 'state', 'citation', 'duplicate', 'answer'])('rejects mismatched %s data', kind => {
  const r = { request_id: 'test', question: 'Pancreatitis' }, value = response(r)
  if (kind === 'request') value.request_id = 'wrong'
  if (kind === 'corpus') value.target.inventory.content_sha256 = 'wrong'
  if (kind === 'state') value.state = 'no_results'
  if (kind === 'citation') value.evidence[0].record.citation.pmcid = 'javascript:bad'
  if (kind === 'duplicate') value.evidence.push(value.evidence[0])
  if (kind === 'answer') value.answer = 'invented'
  expect(() => validateSearch(value, r)).toThrow()
})
