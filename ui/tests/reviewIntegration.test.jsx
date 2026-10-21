import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SavedPredictionView from '../src/components/SavedPredictionView.jsx'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'
vi.mock('../src/lib/savedPrediction.js',()=>({loadSavedPrediction:vi.fn()}))
vi.mock('../src/components/NiivueViewer.jsx',()=>({default:()=> <div>Invented CT viewer</div>}))
const a='a'.repeat(64),b='b'.repeat(64)
function loaded(hash) {return {manifestHash:hash,manifest:{case_id:`invented_${hash[0]}`,warnings:[],model_sha256:{segmenter:a},files:{ct:{content_sha256:a},pred:{content_sha256:a}},geometry:{},ct_window:[-100,300]},
  urls:{},measurement:{status:'unavailable',reason:'Outline touches its inference boundary.'},release:vi.fn()}}
it('connects review and literature without bypassing unavailable measurements; guards an unsaved case switch',async()=>{
  loadSavedPrediction.mockImplementation(async base=>loaded(base.startsWith('/review-records/')?b:a))
  vi.stubGlobal('fetch',vi.fn(async url=>new Response(JSON.stringify(url.endsWith('/packages') ? {packages:[{manifest_sha256:b,case_id:'invented_b',latest:{action:'reject',revision:1}}]} : {
    manifest_sha256:url.includes('archive')?b:a,case_package_id:`case-package:${url.includes('archive')?b:a}`,prediction_id:`prediction:${url.includes('archive')?b:a}`,history:[],
  }))))
  vi.stubGlobal('confirm',vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true))
  render(<SavedPredictionView />)
  await screen.findByText('No recorded decisions for this prediction.')
  expect(screen.getByText('Search supporting literature')).toBeTruthy()
  expect(screen.getByRole('note').textContent).toContain('Measurements are withheld: Outline touches its inference boundary.')
  fireEvent.change(screen.getByLabelText('Measurement question'),{target:{value:'How big is this pancreas?'}})
  fireEvent.click(screen.getByText('Calculate volume'))
  expect(screen.getByText('Measurement unavailable')).toBeTruthy()
  expect(screen.getByText('Outline touches its inference boundary.')).toBeTruthy()
  fireEvent.change(screen.getByLabelText('Decision'),{target:{value:'reject'}})
  const selector=screen.getByLabelText('Prediction')
  fireEvent.change(selector,{target:{value:b}})
  expect(confirm).toHaveBeenCalledTimes(1)
  expect(selector.value).toBe('')
  fireEvent.change(selector,{target:{value:b}})
  await screen.findByText('invented_b',{selector:'h2'})
  await waitFor(()=>expect(screen.getByLabelText('Decision').value).toBe(''))
  expect(loadSavedPrediction.mock.calls.at(-1)[0]).toBe(`/review-records/packages/${b}/files`)
})

it('opens a linked archived prediction directly, without loading the configured demo first',async()=>{
  loadSavedPrediction.mockClear()
  loadSavedPrediction.mockResolvedValue(loaded(b))
  vi.stubGlobal('fetch',vi.fn(async url=>new Response(JSON.stringify(url.endsWith('/packages') ? {packages:[]} : {
    manifest_sha256:b,case_package_id:`case-package:${b}`,prediction_id:`prediction:${b}`,history:[],
  }))))
  render(<SavedPredictionView reviewHash={b} onSelectReview={vi.fn()} />)
  await screen.findByText('invented_b',{selector:'h2'})
  expect(loadSavedPrediction.mock.calls.map(call=>call[0])).toEqual([`/review-records/packages/${b}/files`])
  expect(screen.getByLabelText('Prediction').value).toBe(b)
})
