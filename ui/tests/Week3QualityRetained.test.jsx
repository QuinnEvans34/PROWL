// Replay real retained responses through the shipped UI without model/network calls.
import { it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { validateAnswer } from '../src/components/LiteratureSearchPanel'

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
