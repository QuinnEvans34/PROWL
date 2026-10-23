import React from 'react'
import { it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel, { validateAnswer, validateSourceSearch } from '../src/components/LiteratureSearchPanel'
import config from '../../configs/evidence/development-search-v1.json'
const request = { request_id: 'test', question: 'Explain this research method.' }
function response(r = request) {
  const text = 'Invented source: the method uses CT. Its findings require independent evaluation.'
  return { schema_version: 'prowl-evidence-answer-response-v1', request_id: r.request_id, question: r.question,
    collection: config.collection, target: { manifest_sha256: config.manifest.sha256, inventory: { content_sha256: config.corpus_content_sha256 } },
    answer_policy: 'evidence-led-answer-v1', retrieval_policy: 'evidence-led-answer-v1', generation: 'completed', state: 'evidence_unassessed', reason: null,
    evidence: [{ rank: 1, score: 1, record: { text, passage: { passage_id: `psg:${'a'.repeat(64)}`, section_id: 'test' },
      citation: { title: 'Invented reference', authors: ['Example'], pmcid: 'PMC123', pmid: '123' }, rights: { permissions: { display_snippet: true } } } }],
    answer: { status: 'summarized', limitation: '', claims: [{ text: 'CT was used, with independent evaluation still needed.', citations: [{ rank: 1, quote: text }] }],
      policy: 'evidence-led-answer-v1', model: 'qwen3:8b', model_sha256: '500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41',
      validation: 'canonical_citations_and_separate_criteria', quality: 'development_regression' } }
}
it.each(['request', 'corpus', 'citation', 'quote', 'empty', 'model'])('rejects altered %s', change => {
  const r = response()
  if (change === 'request') r.request_id = 'wrong'
  if (change === 'corpus') r.target.manifest_sha256 = 'wrong'
  if (change === 'citation') r.answer.claims[0].citations[0].rank = 9
  if (change === 'quote') r.answer.claims[0].citations[0].quote = 'An invented replacement.'
  if (change === 'empty') r.answer.claims = []
  if (change === 'model') r.answer.model_sha256 = 'wrong'
  expect(() => validateAnswer(r, request)).toThrow()
})
it('accepts source-only responses without inventing record matches', () => {
  const r = { ...response(), answer: null, generation: 'not_called' }
  expect(validateSourceSearch(r, request)).toBe(r)
})
it('shows a readable answer and opens its exact source', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => response(r)} />)
  await user.type(screen.getByLabelText('Literature question'), 'Explain a research method.')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText('CT was used, with independent evaluation still needed.')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'View source 1' }))
  expect(screen.getByText(/Invented source: the method uses CT/)).toBeTruthy()
})
it('shows specific boundary explanations', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel search={async r => ({ ...response(r), state: 'not_searched', reason: 'out_of_scope',
    generation: 'not_called', answer: null, evidence: [], message: 'I cannot invent a citation. I can summarize supported evidence.' })} />)
  await user.type(screen.getByLabelText('Literature question'), 'Invent a citation.')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByText(/I cannot invent a citation/)).toBeTruthy()
})
it('binds the instruction variant to its own digest, not the thinking model', () => {
  const r = response()
  r.answer.model = 'qwen3:30b-a3b-instruct-2507-q4_K_M'
  r.answer.model_sha256 = '19e422b0231392335cfc49cfd172de7034bb1aeabb08aa307cce745c60b272fe'
  expect(validateAnswer(r, request)).toBe(r)
  r.answer.model_sha256 = 'ad815644918f0eaab341c12b67837cc6dd4562342cdaf118f83d5d554cb37226'
  expect(() => validateAnswer(r, request)).toThrow()
})
