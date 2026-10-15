import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ResearchEvidencePanel, { requestResearch } from '../src/components/ResearchEvidencePanel.jsx'
import questions from '../../configs/evidence/research-questions-v1.json'

function emptyResponse(request, answers) {
  return {
    schema_version: answers ? 'prowl-research-answer-v1' : 'prowl-research-search-v1',
    response_id: request.request_id, request,
    question: questions.find(q => q.id === request.question_id).label,
    state: 'no_results', passages: [], content_sha256: 'a'.repeat(64),
    provenance: { collection: 'research-v1', encoder_id: 'test', generation_model: answers ? 'qwen3:8b' : null },
    ...(answers ? { generation: { validation: 'no_passages', answer: { status: 'insufficient_evidence', extracts: [] } } } : {}),
  }
}

it.each([false, true])('retries the same request after failure in answers=%s mode', async answers => {
  const user = userEvent.setup()
  const load = vi.fn().mockRejectedValueOnce(new Error('offline'))
    .mockImplementation(async request => emptyResponse(request, answers))
  render(<ResearchEvidencePanel answers={answers} loadResponse={load} />)
  await user.click(screen.getByText(answers ? 'Grounded research answers' : 'Research passage search'))
  await user.click(screen.getByRole('button'))
  expect(await screen.findByRole('alert')).toBeTruthy()
  expect(screen.queryByRole('article')).toBeNull()
  await user.click(screen.getByRole('button'))
  expect(await screen.findByRole('article')).toBeTruthy()
  expect(load.mock.calls[1][0]).toEqual(load.mock.calls[0][0])
  expect(Object.keys(load.mock.calls[0][0]).sort()).toEqual(['question_id', 'request_id'])
  expect(screen.getByRole('heading', { name: 'No passages found' })).toBeTruthy()
  if (answers) expect(screen.getByRole('heading', { name: 'Unable to provide a supported answer' })).toBeTruthy()
})

it('rejects an invented quotation even when response identifiers match', async () => {
  const request = { request_id: 'test-request', question_id: 'radiomics' }
  const result = emptyResponse(request, true)
  result.generation.answer = { status: 'excerpts', extracts: [
    { passage_id: 'invented', quote: 'This unsupported quotation is not in any retrieved passage.' },
  ] }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => result }))
  await expect(requestResearch(request, undefined, true)).rejects.toThrow('Invalid grounded answer')
})
