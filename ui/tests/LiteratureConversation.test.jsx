import React from 'react'
import { expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import LiteratureSearchPanel, { findLiteratureSources, literatureConversation, searchLiterature,
  validateAnswer, validateConversationContext } from '../src/components/LiteratureSearchPanel.jsx'
import config from '../../configs/evidence/development-search-v1.json'
import answerConfig from '../../configs/evidence/natural-answer-v6.1.json'

const quote = 'An invented source statement used only to check citation binding.'
const request = { schema_version: 'prowl-expert-request-v1', request_id: 'test', question: 'What about insulin?' }
const context = (previous = []) => ({ policy: 'pancreatic-conversation-v1', topic: 'pancreatic research',
  resolved_question: 'What does pancreatic research say about insulin?', previous_questions: previous })
function response(r, state = 'evidence_unassessed', conversation = []) {
  const found = state === 'evidence_unassessed'
  return { schema_version: 'prowl-development-answer-response-v1', request_id: r.request_id, question: r.question,
    collection: config.collection, generation: found ? 'completed' : 'not_called',
    context: context(conversation.map(turn => turn.question)),
    target: { manifest_sha256: config.manifest.sha256, inventory: { content_sha256: config.corpus_content_sha256 } },
    state, reason: state === 'not_searched' ? 'out_of_scope' : null,
    evidence: found ? [{ rank: 1, score: 1, record: { text: quote,
      passage: { passage_id: `psg:${'a'.repeat(64)}` },
      citation: { title: 'Synthetic source', pmcid: 'PMC123', pmid: '123', authors: ['Example'] },
      rights: { permissions: { display_snippet: true } } } }] : [],
    answer: found ? { status: 'summarized', claims: [{ text: 'An invented answer for testing only.', citations: [{ rank: 1, quote }] }],
      model: answerConfig.model, model_sha256: answerConfig.model_sha256, policy: answerConfig.version,
      prompt_sha256: answerConfig.prompt_sha256, validation: 'exact_quotes_and_model_review', quality: 'development_unvalidated' } : null }
}
function sources(r, conversation = []) {
  return { ...response(r, 'evidence_unassessed', conversation), schema_version: 'prowl-development-search-response-v1', generation: 'not_called', answer: null,
    retrieval_policy: 'source-linked-record-search-v1.1',
    record_selection: { policy: 'source-linked-record-search-v1.1', status: 'dense_fallback', matches: [] } }
}
async function ask(question) {
  fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: question } })
  fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
  await screen.findByRole('article', { name: 'Literature search results' })
}

it('sends recent successful questions for follow-ups without sending answers or scan identity', async () => {
  const search = vi.fn(async (r, _signal, conversation) => response(r, 'evidence_unassessed', conversation))
  render(<LiteratureSearchPanel search={search} contextKey="private-case" contextLabel="Private case" />)
  for (const question of ['Pancreas function', 'Digestive enzymes', 'Insulin', 'Glucagon', 'Explain that simply']) await ask(question)
  expect(search.mock.calls[0]).toHaveLength(2)
  expect(search.mock.calls[4][2]).toEqual([{ question: 'Digestive enzymes' }, { question: 'Insulin' }, { question: 'Glucagon' }])
  const sent = JSON.stringify(search.mock.calls[4][2])
  expect(sent).not.toContain('private-case')
  expect(sent).not.toContain('invented answer')
  expect(Object.keys(search.mock.calls[4][0]).sort()).toEqual(['question', 'request_id', 'schema_version'])
})

it('passes the same question context to Find sources', async () => {
  const findSources = vi.fn(async (r, _signal, conversation) => sources(r, conversation))
  render(<LiteratureSearchPanel search={async r => response(r)} findSources={findSources} />)
  await ask('Pancreas function')
  fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: 'What about insulin?' } })
  fireEvent.click(screen.getByRole('button', { name: 'Find sources' }))
  await waitFor(() => expect(findSources).toHaveBeenCalledTimes(1))
  expect(findSources.mock.calls[0][2]).toEqual([{ question: 'Pancreas function' }])
})

it('keeps legacy answer services on their original standalone request transport', async () => {
  const search = vi.fn(async r => {
    const result = response(r); delete result.context
    return result
  })
  render(<LiteratureSearchPanel search={search} />)
  await ask('Pancreas function')
  await ask('What about insulin?')
  expect(search.mock.calls[1]).toHaveLength(2)
})

it.each(['clear', 'study', 'prediction'])('starts a new question context after %s changes', async change => {
  const search = vi.fn(async (r, _signal, conversation) => response(r, 'evidence_unassessed', conversation))
  const view = props => <LiteratureSearchPanel search={search} contextKey="one" {...props} />
  const { rerender } = render(view({ measurementContext: { key: 'one' } }))
  await ask('What does the pancreas do?')
  if (change === 'clear') fireEvent.click(screen.getByRole('button', { name: 'Clear recent responses' }))
  if (change === 'study') rerender(view({ contextKey: 'two', measurementContext: { key: 'one' } }))
  if (change === 'prediction') rerender(view({ measurementContext: { key: 'two' } }))
  await ask('What about insulin?')
  expect(search.mock.calls[1]).toHaveLength(2)
})

it('stops context at refusals, source-only turns, missing answers, and scan measurements', () => {
  const complete = { question: 'Pancreas function', response: response(request) }
  const unavailable = response(request); unavailable.generation = 'unavailable'; unavailable.answer = null
  const insufficient = response(request); insufficient.answer.status = 'insufficient'; insufficient.answer.claims = []
  const legacy = response(request); delete legacy.context
  const boundaries = [
    { question: 'Rejected question', response: response(request, 'not_searched') },
    { question: 'No passages', response: response(request, 'no_results') },
    { question: 'Unavailable answer', response: unavailable },
    { question: 'Insufficient answer', response: insufficient },
    { question: 'Sources only', response: sources(request), sourceMode: true },
    { question: 'Scan volume', text: '72 mL', measured: true },
    { question: 'Legacy standalone answer', response: legacy },
  ]
  for (const boundary of boundaries) {
    expect(literatureConversation([complete, boundary])).toEqual([])
    expect(literatureConversation([complete, boundary, { ...complete, question: 'A new topic' }]))
      .toEqual([{ question: 'A new topic' }])
  }
})

it.each(['refusal', 'unavailable', 'error', 'scan'])('clears antecedents after a %s turn', async kind => {
  const search = vi.fn(async (r, _signal, conversation) => {
    if (r.question !== 'Boundary question') return response(r, 'evidence_unassessed', conversation)
    if (kind === 'error') throw new Error('Unavailable')
    if (kind === 'refusal') return response(r, 'not_searched', conversation)
    const result = response(r, 'evidence_unassessed', conversation); result.generation = 'unavailable'; result.answer = null
    return result
  })
  const measurementContext = { key: 'one', available: true }
  render(<LiteratureSearchPanel search={search} measurementContext={measurementContext}
    measure={async () => ({ contextKey: 'one', pancreasMl: 72, lesionMl: 0, lesionVoxels: 0,
      shape: [5, 5, 5], voxelMm3: 24 })} />)
  await ask('Pancreas function')
  if (kind === 'scan') {
    fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: 'How big is this pancreas?' } })
    fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
    await screen.findByRole('article', { name: 'Current scan measurement' })
  } else if (kind === 'error') {
    fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: 'Boundary question' } })
    fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
    await screen.findByRole('alert')
    fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: '' } })
  } else await ask('Boundary question')
  await ask('What about insulin?')
  expect(search.mock.calls.at(-1)).toHaveLength(2)
})

it('shows the resolved meaning while preserving the submitted question', async () => {
  render(<LiteratureSearchPanel search={async r => ({ ...response(r), context: context() })} />)
  await ask('What about insulin?')
  expect(screen.getByText('What about insulin?')).toBeTruthy()
  expect(screen.getByText('How I understood your question')).toBeTruthy()
  expect(screen.getByText('What does pancreatic research say about insulin?')).toBeTruthy()
  expect(screen.getByText('Uses pancreatic research as the topic.')).toBeTruthy()
})

it.each(['policy', 'topic', 'unknown', 'long', 'empty', 'history', 'substitution'])('rejects invalid context %s', kind => {
  const result = { ...response(request), context: context() }
  if (kind === 'policy') result.context.policy = 'other'
  if (kind === 'topic') result.context.topic = 'other'
  if (kind === 'unknown') result.context.case_id = 'private'
  if (kind === 'long') result.context.resolved_question = 'x'.repeat(501)
  if (kind === 'empty') result.context.resolved_question = ' '
  if (kind === 'history') result.context.previous_questions = Array(4).fill('Earlier question')
  if (kind === 'substitution') result.context.previous_questions = ['Unsent question']
  expect(() => {
    validateAnswer(result, request)
    validateConversationContext(result, [])
  }).toThrow()
})

it.each(['answer', 'sources'])('keeps the original request closed inside optional %s transport context', async kind => {
  const calls = []
  vi.stubGlobal('fetch', vi.fn(async (url, options) => {
    calls.push({ url, body: JSON.parse(options.body) })
    const result = kind === 'answer' ? response(request) : sources(request)
    result.context = context(calls.at(-1).body.conversation?.map(turn => turn.question) || [])
    return new Response(JSON.stringify(result))
  }))
  const send = kind === 'answer' ? searchLiterature : findLiteratureSources
  await send(request)
  await send(request, undefined, [{ question: 'What does the pancreas do?' }])
  expect(calls[0].body).toEqual(request)
  expect(calls[1].body).toEqual({ request, conversation: [{ question: 'What does the pancreas do?' }] })
})

it('uses the new literature subject instead of a stale measured lesion', async () => {
  const measurementContext = { key: 'one:saved', available: true, source: 'saved' }
  const measure = vi.fn(async () => ({ contextKey: 'one:saved', pancreasMl: 72, lesionMl: 3,
    lesionVoxels: 50, shape: [5, 5, 5], voxelMm3: 24, unitsBasis: 'NIfTI millimeter units',
    coverage: 'Whole-organ coverage unverified' }))
  render(<LiteratureSearchPanel measurementContext={measurementContext} measure={measure} search={async r => response(r)} />)
  fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: 'How big is this lesion?' } })
  fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
  await screen.findByText(/about 3.00 mL/)
  await ask('What does the pancreas do?')
  fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: 'How big is it?' } })
  fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
  await screen.findByText(/about 72.00 mL/)
  expect(screen.getByRole('article', { name: 'Current scan measurement' }).textContent).toContain('72.00 mL')
})
