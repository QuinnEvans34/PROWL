// Replay real retained responses through the shipped UI without model/network calls.
import { it, expect } from 'vitest'
import React from 'react'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import fs from 'node:fs'
import path from 'node:path'
import { validateAnswer } from '../src/components/LiteratureSearchPanel'
import LiteratureSearchPanel from '../src/components/LiteratureSearchPanel'

const directories = (process.env.PROWL_WEEK3_CHECK_DIRS || '').split(path.delimiter).filter(Boolean)
it.skipIf(!directories.length)('validates every retained Week 3 response, including rollout compatibility', () => {
  for (const directory of directories) {
    const receipt = JSON.parse(fs.readFileSync(path.join(directory, 'receipt.json'), 'utf8'))
    expect(receipt.state).toBe('completed')
    expect(receipt.cases).toHaveLength(30)
    for (const item of receipt.cases) {
      const { request, response } = JSON.parse(fs.readFileSync(path.join(directory, `${item.id}.json`), 'utf8'))
      expect(validateAnswer(response, request)).toBe(response)
      if (response.answer) {
        const forged = structuredClone(response)
        forged.answer.claims[0].text += ' This proves cancer.'
        expect(() => validateAnswer(forged, request)).toThrow()
        const unknown = structuredClone(response)
        unknown.answer_policy = unknown.answer.policy = 'unreviewed-policy'
        expect(() => validateAnswer(unknown, request)).toThrow()
      }
    }
  }
})

it.skipIf(!directories.length)('renders the retained candidate answers and opens their exact source excerpts', async () => {
  const directory = directories.at(-1)
  const receipt = JSON.parse(fs.readFileSync(path.join(directory, 'receipt.json'), 'utf8'))
  for (const item of receipt.cases) {
    const { request, response } = JSON.parse(fs.readFileSync(path.join(directory, `${item.id}.json`), 'utf8'))
    render(<LiteratureSearchPanel search={async fresh => ({ ...response, request_id: fresh.request_id })} />)
    fireEvent.change(screen.getByLabelText('Literature question'), { target: { value: request.question } })
    fireEvent.click(screen.getByRole('button', { name: 'Ask question' }))
    await screen.findByLabelText('Literature search results')
    if (response.answer) {
      const answer = screen.getByLabelText('AI answer')
      for (const claim of response.answer.claims) expect(answer.textContent).toContain(claim.text)
      expect(screen.queryByLabelText('Sources')).toBeNull()
      const rank = response.answer.claims[0].citations[0].rank
      fireEvent.click(within(answer).getAllByRole('button', { name: `View source ${rank}` })[0])
      expect(screen.getByText(`Original excerpt [${rank}]`).closest('details').open).toBe(true)
      expect(screen.getByLabelText('Sources').textContent).toContain(response.evidence[rank-1].record.text)
      fireEvent.click(screen.getByRole('button', { name: 'Answer' }))
      expect(screen.getByLabelText('AI answer').textContent).toContain(response.answer.claims[0].text)
    } else {
      expect(screen.queryByLabelText('AI answer')).toBeNull()
    }
    cleanup()
  }
})
