// Optional replay of a retained development check; never sends model/network requests.
import { it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { validateAnswer } from '../src/components/LiteratureSearchPanel'
const directory = process.env.PROWL_VOLUME_CHECK_DIR
it.skipIf(!directory)('validates all eight retained HTTP responses through the actual UI contract', () => {
  const receipt = JSON.parse(fs.readFileSync(path.join(directory, 'receipt.json'), 'utf8'))
  expect(receipt.automated_gate).toBe(true)
  expect(receipt.cases).toHaveLength(8)
  for (const c of receipt.cases) {
    const { request, response } = JSON.parse(fs.readFileSync(path.join(directory, `${c.id}.json`), 'utf8'))
    expect(validateAnswer(response, request)).toBe(response)
  }
})
