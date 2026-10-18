import React from 'react'
import { expect, it, vi } from 'vitest'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel, { validateAnswer } from '../src/components/LiteratureSearchPanel.jsx'
import config from '../../configs/evidence/development-search-v1.json'
import answerConfig from '../../configs/evidence/natural-answer-v5.json'
function response(request, state = 'evidence_unassessed') {
  return { schema_version: 'prowl-development-answer-response-v1', request_id: request.request_id,
    question: request.question, collection: config.collection, generation: state === 'evidence_unassessed' ? 'unavailable' : 'not_called', answer: null,
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
  expect(screen.getByRole('button', { name: 'Ask question' }).disabled).toBe(true)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatitis imaging')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
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
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByRole('alert')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Try again' }))
  expect(await screen.findByText('No passages found')).toBeTruthy()
})
it('discards old responses after question changes', async () => {
  const user = userEvent.setup(); let finish, oldRequest
  const search = vi.fn(r => { oldRequest = r; return new Promise(resolve => { finish = resolve }) })
  render(<LiteratureSearchPanel search={search} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatitis')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  await user.type(screen.getByLabelText('Literature question'), ' CT')
  await act(async () => finish(response(oldRequest)))
  expect(screen.queryByRole('article')).toBeNull()
  expect(search.mock.calls[0][1].aborted).toBe(true)
})
it('cancels pending work', async () => {
  const user = userEvent.setup(), search = vi.fn(() => new Promise(() => {}))
  render(<LiteratureSearchPanel search={search} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatic cancer')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(search.mock.calls[0][1].aborted).toBe(true)
  expect(screen.getByRole('button', { name: 'Ask question' }).disabled).toBe(false)
})
it('explains case measurement limits without showing evidence', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => response(r, 'not_searched')} />)
  await user.type(screen.getByLabelText('Literature question'), 'What is the size of this pancreas?')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
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
  expect(() => validateAnswer(value, r)).toThrow()
})

function generated(request) {
  const result = response(request)
  result.generation = 'completed'
  result.answer = { status: 'summarized', claims: [{ text: 'A concise human-readable explanation.',
    citations: [{ rank: 1, quote: result.evidence[0].record.text }] }],
    model: answerConfig.model, model_sha256: answerConfig.model_sha256,
    policy: answerConfig.version, prompt_sha256: answerConfig.prompt_sha256,
    validation: 'exact_quotes_and_model_review', quality: 'development_unvalidated' }
  return result
}
it('shows the generated answer first and opens its source', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => generated(r)} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreas size')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText('A concise human-readable explanation.')).toBeTruthy()
  expect(screen.queryByText('Artificial source excerpt for testing provenance display.')).toBeNull()
  await user.click(screen.getByRole('button', { name: 'View source 1' }))
  expect(screen.getByRole('link', { name: /Read full source/ })).toBeTruthy()
  expect(screen.getByText('Artificial source excerpt for testing provenance display.')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Answer', exact: true }))
  expect(screen.getByText('A concise human-readable explanation.')).toBeTruthy()
})
it.each(['quote', 'rank', 'model', 'prompt', 'status', 'generation'])('rejects invalid summary %s', kind => {
  const request = { request_id: 'test', question: 'Pancreas size' }, result = generated(request)
  if (kind === 'quote') result.answer.claims[0].citations[0].quote = 'An invented quote that is not supported.'
  if (kind === 'rank') result.answer.claims[0].citations[0].rank = 8
  if (kind === 'model') result.answer.model_sha256 = 'wrong'
  if (kind === 'prompt') result.answer.prompt_sha256 = 'wrong'
  if (kind === 'status') result.answer.status = 'insufficient'
  if (kind === 'generation') result.generation = 'not_called'
  expect(() => validateAnswer(result, request)).toThrow()
})
it('keeps insufficient evidence distinct from an unavailable model', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => {
    const result = generated(r); result.answer.status = 'insufficient'; result.answer.claims = []; return result
  }} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreas size')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText(/couldn’t find enough directly relevant evidence/)).toBeTruthy()
  expect(screen.queryByText(/could not produce a checked answer/)).toBeNull()
})
