// @vitest-environment node

import { expect, it } from 'vitest'
import { localRequest } from '../localExpertPlugin.js'
it('rejects cross-site lifecycle requests and foreign Host headers',()=>{
  expect(localRequest({headers:{host:'127.0.0.1:5180',origin:'http://127.0.0.1:5180'}})).toBe(true)
  expect(localRequest({headers:{host:'127.0.0.1:5180',origin:'https://evil.example'}})).toBe(false)
  expect(localRequest({headers:{host:'evil.example',origin:'http://127.0.0.1:5180'}})).toBe(false)
  expect(localRequest({headers:{host:'127.0.0.1:5180','sec-fetch-site':'cross-site'}})).toBe(false)
})
