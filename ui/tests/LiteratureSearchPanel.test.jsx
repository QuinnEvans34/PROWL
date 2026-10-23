import React from 'react'
import { expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel, { validateAnswer } from '../src/components/LiteratureSearchPanel.jsx'
import config from '../../configs/evidence/development-search-v1.json'
import answerConfig from '../../configs/evidence/natural-answer-v6.1.json'
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
  expect(screen.getByText(/passages returned by this search/)).toBeTruthy()
  expect(screen.queryByText(/Written by the local AI using/)).toBeNull()
})

it.each([
  ['timeout', /reached its 60-second answer limit/],
  ['incomplete', /stopped before finishing/],
  ['support_rejected', /could not confirm the draft/],
  ['qualifier_mismatch', /overstated or changed the source/],
  ['model_unavailable', /local answer model is unavailable/],
  ['validation_failed', /did not pass citation or answer-format checks/],
])('explains %s and preserves access to sources', async (code, message) => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => ({ ...response(r), generation_failure: code })} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreas size')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText(message)).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Sources (1)' })).toBeTruthy()
})
it('rejects arbitrary provider error text', () => {
  const request = { request_id: 'test', question: 'Pancreas size' }
  expect(() => validateAnswer({ ...response(request), generation_failure: 'PRIVATE_ERROR' }, request)).toThrow()
})
it('shows elapsed time and exits a stalled request at the browser limit', async () => {
  vi.useFakeTimers()
  const search = vi.fn((r, signal) => new Promise((resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')))
  }))
  try {
    render(<LiteratureSearchPanel search={search} />)
    fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: 'Pancreas size' } })
    fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
    await act(async () => vi.advanceTimersByTime(4000))
    expect(screen.getByText(/4s elapsed/)).toBeTruthy()
    await act(async () => vi.advanceTimersByTime(146000))
    expect(search.mock.calls[0][1].aborted).toBe(true)
    expect(screen.getByRole('alert').textContent).toMatch(/timed out/)
    expect(screen.getByRole('button', { name: 'Try again' }).disabled).toBe(false)
  } finally { vi.useRealTimers() }
})

// Source retrieval and generated answers have separate contracts and actions.
import { validateSourceSearch } from '../src/components/LiteratureSearchPanel.jsx'
import diseaseCatalog from '../../configs/evidence/source-facts-disease-v1.json'
import recordConfig from '../../configs/evidence/development-search-v3-records.json'
function sourceResponse(request) {
  const result = response(request), record = diseaseCatalog.records[0]
  const ids = [...new Set(record.facts.flatMap(f => f.evidence.map(id => diseaseCatalog.spans[id].passage_id)))].sort()
  result.schema_version = 'prowl-development-search-response-v1'; result.generation = 'not_called'
  result.retrieval_policy = recordConfig.retriever
  result.record_selection = { policy: recordConfig.retriever, status: 'matched', reason: 'literature_examples_not_exhaustive',
    matches: [{ record_id: record.id, comparison: record.comparison, topic: record.topic, score: 1,
      anchor_passage_ids: record.retrieval_anchors, evidence_passage_ids: ids }] }
  const original = result.evidence[0]
  result.evidence = ids.map((id, i) => ({ ...original, rank: i + 1, record: { ...original.record,
    passage: { ...original.record.passage, passage_id: id }, text: `Artificial source context ${i + 1}.` } }))
  return result
}
it('finds sources without calling the answer path and keeps citations accessible', async () => {
  const user = userEvent.setup(), search = vi.fn(), findSources = vi.fn(async r => sourceResponse(r))
  render(<LiteratureSearchPanel search={search} findSources={findSources} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatic head swelling and disease')
  await user.click(screen.getByRole('button', { name: 'Find sources' }))
  expect(await screen.findByText(/Relevant comparison sources/)).toBeTruthy()
  expect(search).not.toHaveBeenCalled(); expect(findSources).toHaveBeenCalledOnce()
  expect(screen.queryByText(/could not produce a checked answer/)).toBeNull()
  await user.click(screen.getByRole('button', { name: 'View source 1' }))
  expect(screen.getAllByRole('link', { name: /Read full source/ }).length).toBe(4)
})
it.each(['missing', 'unknown', 'extra', 'wrongPair', 'answerPath'])('rejects %s source-record mismatch', kind => {
  const request = { request_id: 'test', question: 'Pancreatic head swelling' }, result = sourceResponse(request)
  if (kind === 'missing') result.evidence.pop()
  if (kind === 'unknown') result.record_selection.matches[0].record_id = 'invented'
  if (kind === 'extra') result.record_selection.matches.push(result.record_selection.matches[0])
  if (kind === 'wrongPair') result.record_selection.matches[0].comparison = ['all inflammation', 'all tumors']
  if (kind === 'answerPath') expect(() => validateAnswer(result, request)).toThrow()
  else expect(() => validateSourceSearch(result, request)).toThrow()
})

import composerConfig from '../../configs/evidence/record-answer-v1.json'
import wording from '../../configs/evidence/record-answer-wording-v1.json'
function composed(request, fallback = false) {
  const result = sourceResponse(request), record = diseaseCatalog.records[0]
  result.schema_version = 'prowl-record-answer-response-v1'; result.answer_policy = composerConfig.version
  result.generation = fallback ? 'fallback' : 'completed'
  const units = wording.records[record.id].units
  result.answer = { status: 'summarized', policy: composerConfig.version,
    provenance: fallback ? 'reviewed_source_fallback' : 'local_model_composition', failure: fallback ? 'timeout' : null,
    model: fallback ? null : composerConfig.model, model_sha256: fallback ? null : composerConfig.model_sha256,
    prompt_sha256: composerConfig.prompt_sha256, wording_content_sha256: composerConfig.wording_content_sha256,
    validation: 'complete_reviewed_units_and_exact_citations', quality: 'engineering_reviewed_independent_review_pending',
    scope: composerConfig.scope, limitation: composerConfig.limitation,
    claims: [false, true].map(limit => {
      const selected = units.filter(u => u.qualification === limit)
      const ids = new Set(selected.flatMap(u => u.facts.flatMap(i => record.facts[i].evidence.map(s => diseaseCatalog.spans[s].passage_id))))
      return { record_id: record.id, units: selected.map(u => ({ unit_id: u.id, wording: 0 })), text: selected.map(u => u.wordings[0]).join(' '),
        citations: result.evidence.filter(e => ids.has(e.record.passage.passage_id)).map(e => ({ rank: e.rank, quote: e.record.text })) }
    }),
  }
  return result
}
it.each([false, true])('shows readable composition, honest fallback=%s, and opens precise citations', async fallback => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => composed(r, fallback)} />)
  await user.type(screen.getByLabelText('Literature question'), 'Could pancreatic head enlargement indicate disease?')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText(fallback ? /not model-written text/ : /Local AI summary/)).toBeTruthy()
  expect(screen.getByText(/No single imaging feature reliably separates MFCP/)).toBeTruthy()
  expect(screen.queryByText('Artificial source context 1.')).toBeNull()
  await user.click(screen.getAllByRole('button', { name: 'View source 1' })[0])
  expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
  expect(document.activeElement.textContent).toContain('[1]')
})
it.each(['text', 'omittedLimit', 'unit', 'scope', 'quote', 'rank', 'pin', 'falseAI', 'failure', 'noCall', 'reorder'])('rejects record composition %s corruption', kind => {
  const request = { request_id: 'test', question: 'Head enlargement' }, r = composed(request)
  if (kind === 'text') r.answer.claims[0].text += ' This proves cancer.'
  if (kind === 'omittedLimit') r.answer.claims.pop()
  if (kind === 'unit') r.answer.claims[0].units[0].wording = true
  if (kind === 'scope') r.answer.scope = 'All pancreatic tumors can be diagnosed.'
  if (kind === 'quote') r.answer.claims[0].citations[0].quote = 'Invented support'
  if (kind === 'rank') r.answer.claims[0].citations[0].rank = 9
  if (kind === 'pin') r.answer.wording_content_sha256 = 'changed'
  if (kind === 'falseAI') r.generation = 'fallback'
  if (kind === 'failure') r.answer.failure = 'PRIVATE_PROVIDER_TRACE'
  if (kind === 'noCall') r.generation = 'not_called'
  if (kind === 'reorder') r.answer.claims.reverse()
  expect(() => validateAnswer(r, request)).toThrow()
})
it('explains coverage fallback without pretending the AI answered', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async request => {
    const r = composed(request);r.generation = 'not_called';r.answer = null
    r.record_selection.status = 'dense_fallback';r.record_selection.matches = []
    return r
  }} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatic enzymes')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText(/outside the reviewed summary coverage/)).toBeTruthy()
  expect(screen.queryByLabelText('AI answer')).toBeNull()
})

it('reviews and edits suggested wording without silently submitting or losing the original', async () => {
  const user = userEvent.setup(), search = vi.fn(async r => response(r, 'no_results'))
  const interpret = vi.fn(async r => ({ status: 'suggested', query: 'Pancreatic inflammation imaging findings', message: 'Review this suggestion.' }))
  render(<LiteratureSearchPanel search={search} interpret={interpret} />)
  await user.type(screen.getByLabelText('Literature question'), 'What does swelling look like in the pancreas?')
  await user.click(screen.getByRole('button', { name: 'Help phrase my question' }))
  const edit = await screen.findByLabelText('Review or edit the wording')
  expect(search).not.toHaveBeenCalled()
  expect(screen.getByLabelText('Literature question').value).toBe('What does swelling look like in the pancreas?')
  await user.clear(edit); await user.type(edit, 'Pancreatic enlargement on CT')
  await user.click(screen.getByRole('button', { name: 'Use this wording' }))
  expect(search).not.toHaveBeenCalled()
  expect(screen.getByText('What does swelling look like in the pancreas?')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText('No passages found')).toBeTruthy()
  expect(search.mock.calls[0][0].question).toBe('Pancreatic enlargement on CT')
})

it('keeps the question usable when interpretation fails', async () => {
  const user = userEvent.setup(), search = vi.fn(async r => response(r, 'no_results'))
  render(<LiteratureSearchPanel search={search} interpret={async () => { throw new Error('offline') }} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatic inflammation')
  await user.click(screen.getByRole('button', { name: 'Help phrase my question' }))
  expect(await screen.findByText(/Question help is unavailable or timed out/)).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText('No passages found')).toBeTruthy()
})

it('discards a late interpretation when the user edits the question', async () => {
  const user = userEvent.setup(); let finish
  const interpret = vi.fn(() => new Promise(resolve => { finish = resolve }))
  render(<LiteratureSearchPanel interpret={interpret} />)
  await user.type(screen.getByLabelText('Literature question'), 'Pancreatic inflammation')
  await user.click(screen.getByRole('button', { name: 'Help phrase my question' }))
  await user.type(screen.getByLabelText('Literature question'), ' on CT')
  await act(async () => finish({ status: 'suggested', query: 'Old query', message: 'Old suggestion' }))
  expect(screen.queryByRole('region', { name: 'Question interpretation' })).toBeNull()
  expect(interpret.mock.calls[0][1].aborted).toBe(true)
})

it('clarifies without replacing the question or searching', async () => {
  const user = userEvent.setup(), search = vi.fn()
  render(<LiteratureSearchPanel search={search} interpret={async () => ({ status: 'clarification', query: '', message: 'Volume or diameter?' })} />)
  await user.type(screen.getByLabelText('Literature question'), 'How big is a pancreas?')
  await user.click(screen.getByRole('button', { name: 'Help phrase my question' }))
  expect(await screen.findByText('Volume or diameter?')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Keep my question' }))
  expect(screen.getByLabelText('Literature question').value).toBe('How big is a pancreas?')
  expect(search).not.toHaveBeenCalled()
})
