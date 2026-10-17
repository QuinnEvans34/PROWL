import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ResearchWorkflowPanel, { workflowRequest } from '../src/components/ResearchWorkflowPanel.jsx'
import questions from '../../configs/evidence/research-questions-v1.json'

function run(request, state = 'failed') {
  const completed = state === 'completed'
  return { schema_version: 'prowl-research-workflow-v1', run_id: request.request_id, request,
    question: questions.find(q => q.id === request.question_id).label, state,
    stages: ['retrieve', 'select', 'validate', 'save'].map((stage, i) => ({ stage,
      state: completed ? (i === 0 ? 'reused' : 'completed') : ['completed', 'completed', 'failed', 'pending'][i],
      ...(!completed && i === 2 ? { reason: 'invalid_generation' } : {}) })),
    ...(completed ? { response: { schema_version: 'prowl-research-answer-v1', response_id: request.request_id,
      request: { request_id: request.request_id, question_id: request.question_id },
      question: questions.find(q => q.id === request.question_id).label, state: 'no_results', passages: [],
      provenance: { collection: 'research-v1', generation_model: 'qwen3:8b' },
      generation: { validation: 'no_passages', answer: { status: 'insufficient_evidence', extracts: [] } } } } : {}) }
}

it('explicit failed retry creates a linked ID and distinguishes valid abstention', async () => {
  const user = userEvent.setup()
  const load = vi.fn().mockImplementation(async request => run(request, request.resume_of ? 'completed' : 'failed'))
  render(<ResearchWorkflowPanel loadWorkflow={load} />)
  await user.click(screen.getByText('Research evidence workflow'))
  await user.click(screen.getByRole('button'))
  expect((await screen.findByRole('alert')).textContent).toContain('does not mean the sources lack evidence')
  expect(screen.queryByRole('article')).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Retry failed stage' }))
  expect((await screen.findByRole('article')).textContent).toContain('Insufficient evidence')
  const [first, second] = load.mock.calls.map(c => c[0])
  expect(second.request_id).not.toBe(first.request_id)
  expect(second.resume_of).toBe(first.request_id)
  expect(screen.getByRole('list').textContent).toContain('Reused from prior attempt')
  expect(screen.queryByRole('alert')).toBeNull()
  expect(screen.getByRole('button').textContent).toContain('Run evidence workflow')
})

it('unknown transport outcome checks the same ID without starting another generation', async () => {
  const user = userEvent.setup()
  const load = vi.fn().mockRejectedValueOnce(new Error('lost reply')).mockImplementation(async request => run(request))
  render(<ResearchWorkflowPanel loadWorkflow={load} />)
  await user.click(screen.getByText('Research evidence workflow'))
  await user.click(screen.getByRole('button'))
  expect((await screen.findByRole('alert')).textContent).toContain('could not confirm')
  await user.click(screen.getByRole('button', { name: 'Check same request' }))
  expect(await screen.findByRole('button', { name: 'Retry failed stage' })).toBeTruthy()
  expect(load.mock.calls[1][0]).toEqual(load.mock.calls[0][0])
})

it.each(['wrong-id', 'premature-answer', 'rejected-complete', 'unfinished-complete'])('rejects unsafe workflow response: %s', async kind => {
  const request = { request_id: 'known-id', question_id: 'radiomics' }
  const value = run(request, 'completed')
  if (kind === 'wrong-id') value.run_id = 'other'
  if (kind === 'premature-answer') value.state = 'failed'
  if (kind === 'rejected-complete') value.response.generation.validation = 'generation_rejected'
  if (kind === 'unfinished-complete') value.stages[2].state = 'failed'
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => value }))
  await expect(workflowRequest(request)).rejects.toThrow()
})

it('aborts status polling on case switch and ignores a late result', async () => {
  const user = userEvent.setup()
  let finish, signal
  const load = (request, incoming) => { signal = incoming; return new Promise(resolve => { finish = () => resolve(run(request, 'completed')) }) }
  const { rerender } = render(<ResearchWorkflowPanel key="first" loadWorkflow={load} />)
  await user.click(screen.getByText('Research evidence workflow'))
  await user.click(screen.getByRole('button'))
  rerender(<ResearchWorkflowPanel key="next" loadWorkflow={load} />)
  expect(signal.aborted).toBe(true)
  finish()
  expect(screen.queryByRole('article')).toBeNull()
})
