import React from 'react'
import { afterEach, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SavedReviewList from '../src/components/SavedReviewList.jsx'
import App from '../src/App.jsx'

vi.mock('../src/components/ReviewWorkspace.jsx', () => ({default: () => <div>Prepared workspace</div>}))
vi.mock('../src/components/SavedPredictionView.jsx', () => ({default: ({reviewHash}) => <div>Archived prediction: {reviewHash}</div>}))
vi.mock('../src/components/OnDemandPredictionView.jsx', () => ({default: () => <div>Choose a scan to analyze</div>}))

const a='a'.repeat(64), b='b'.repeat(64)
function saved(hash, action='reject', revision=1, at='2026-10-21T12:00:00Z') {
  return {manifest_sha256:hash,case_id:'invented_same_study',latest:{action,revision,recorded_at:at,
    case_package_id:`case-package:${hash}`,prediction_id:`prediction:${hash}`,reviewer:{reviewer_id:'Invented reviewer'}}}
}
const json = (body, status=200) => new Response(JSON.stringify(body),{status})
afterEach(() => {window.history.replaceState(null,'','/');vi.clearAllMocks()})

it('keeps different predictions of the same study separate and reopens the exact newest decision',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>json({packages:[saved(a),saved(b,'edit_required',2,'2026-10-21T13:00:00Z')]})))
  const navigate=vi.fn();render(<SavedReviewList navigate={navigate} />)
  const links=await screen.findAllByRole('link',{name:/Reopen invented_same_study/})
  expect(links.map(l=>l.getAttribute('href'))).toEqual([`/saved?review=${b}`,`/saved?review=${a}`])
  expect(screen.getByText('Needs correction')).toBeTruthy()
  expect(screen.getByText('Revision 2')).toBeTruthy()
  fireEvent.click(links[0]);expect(navigate).toHaveBeenLastCalledWith({view:'saved',review:b})
  expect(fetch).toHaveBeenCalledTimes(1)
  expect(fetch.mock.calls[0][0]).toBe('/review-records/packages')
  expect(fetch.mock.calls[0][1].method).toBeUndefined()
})

it('distinguishes unavailable storage from an empty archive and supports a read-only refresh',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(json({error:'offline'},503)).mockResolvedValueOnce(json({packages:[]})))
  render(<SavedReviewList navigate={vi.fn()} />)
  expect((await screen.findByRole('alert')).textContent).toContain('could not be loaded')
  expect(screen.queryByText(/No recorded reviews yet/)).toBeNull()
  fireEvent.click(screen.getByRole('button',{name:'Refresh saved reviews'}))
  expect(await screen.findByText(/No recorded reviews yet/)).toBeTruthy()
  expect(screen.queryByRole('alert')).toBeNull()
  expect(fetch.mock.calls.every(([,o])=>!o.method)).toBe(true)
})

it.each([
  {packages:[{...saved(a),manifest_sha256:'../../private'}]},
  {packages:[{...saved(a),latest:{...saved(a).latest,prediction_id:`prediction:${b}`}}]},
  {packages:[saved(a),saved(a)]},
])('does not offer a link for an invalid or ambiguous saved target',async data=>{
  vi.stubGlobal('fetch',vi.fn(async()=>json(data)))
  render(<SavedReviewList navigate={vi.fn()} />)
  await screen.findByRole('alert')
  expect(screen.queryByRole('link',{name:/Reopen/})).toBeNull()
  expect(screen.getByRole('link',{name:'Analyze a scan'}).getAttribute('href')).toBe('/predict')
})

it('aborts an outstanding list request when leaving the page',()=>{
  let signal
  vi.stubGlobal('fetch',vi.fn((url,options)=>{signal=options.signal;return new Promise(()=>{})}))
  const view=render(<SavedReviewList navigate={vi.fn()} />)
  expect(signal.aborted).toBe(false);view.unmount();expect(signal.aborted).toBe(true)
})

it('keeps saved reviews and Analyze accessible when the prepared-example manifest fails',async()=>{
  window.history.replaceState(null,'','/')
  vi.stubGlobal('fetch',vi.fn(async url=>String(url).endsWith('/review-records/packages')
    ? json({packages:[saved(a)]}) : json({error:'fixture offline'},503)))
  render(<App />)
  await screen.findByText('No prepared studies found')
  expect(screen.getByText('Local research workspace')).toBeTruthy()
  fireEvent.click(await screen.findByRole('link',{name:/Reopen invented_same_study/}))
  await screen.findByText(`Archived prediction: ${a}`)
  expect(window.location.pathname+window.location.search).toBe(`/saved?review=${a}`)
  expect(screen.queryByText('No prepared studies found')).toBeNull()
  fireEvent.click(screen.getByRole('link',{name:'Analyze'}))
  await screen.findByText('Choose a scan to analyze')
  expect(screen.queryByText('No prepared studies found')).toBeNull()
  await waitFor(()=>expect(fetch.mock.calls.every(([,o])=>!o?.method)).toBe(true))
})
