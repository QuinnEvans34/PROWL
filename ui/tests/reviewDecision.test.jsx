import React from 'react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import ReviewDecisionPanel from '../src/components/ReviewDecisionPanel.jsx'
const hash = 'a'.repeat(64), otherHash = 'b'.repeat(64)
const manifest = {case_id:'invented_case',model_sha256:{segmenter:'c'.repeat(64)}}
const target = {manifest_sha256:hash,case_package_id:`case-package:${hash}`,prediction_id:`prediction:${hash}`,history:[]}
const record = {
  event:{review_event_id:'review:12345678-1234-4234-8234-123456789abc',case_package_id:target.case_package_id,prediction_id:target.prediction_id,
    revision:1,action:'edit_required',reason_codes:['boundary_correction'],note:'Synthetic review',reviewer:{reviewer_id:'Invented operator'},recorded_at:'2026-10-21T12:00:00Z'},
  receipt:{review_event_id:'review:12345678-1234-4234-8234-123456789abc',revision:1,sequence:1,content_sha256:'d'.repeat(64),location:`${hash}/event-000001.json`,case_package_id:target.case_package_id,prediction_id:target.prediction_id},
}
const ok = data => Promise.resolve(new Response(JSON.stringify(data)))
function renderPanel(props={}) {return render(<ReviewDecisionPanel base="/saved-prediction" manifestHash={hash} manifest={manifest} {...props}/>)}
async function fill() {
  await screen.findByText('No recorded decisions for this prediction.')
  fireEvent.change(screen.getByLabelText('Your name'),{target:{value:'Invented operator'}})
  fireEvent.change(screen.getByLabelText('Decision'),{target:{value:'edit_required'}})
  fireEvent.click(screen.getByLabelText('Boundary needs correction'))
  fireEvent.change(screen.getByLabelText(/Review note/),{target:{value:'Synthetic review'}})
  fireEvent.click(screen.getByText('Review before saving'))
}
afterEach(()=>{cleanup();vi.unstubAllGlobals()})
describe('durable decisions',()=>{
  it('confirms exact identities and waits for a durable receipt, then reloads history',async()=>{
    let resolve
    const fetch=vi.fn().mockImplementationOnce(()=>ok(target)).mockImplementationOnce(()=>new Promise(r=>resolve=r))
    vi.stubGlobal('fetch',fetch)
    const view=renderPanel();await fill()
    expect(screen.getByText(`case-package:${hash}`)).toBeTruthy()
    expect(screen.getByText(`prediction:${hash}`)).toBeTruthy()
    fireEvent.click(screen.getByText('Confirm and save locally'))
    expect(screen.queryByText(/Saved locally/)).toBeNull()
    resolve(new Response(JSON.stringify(record)))
    await screen.findByText(/Saved locally — revision 1/)
    expect(screen.getByRole('link',{name:'Reopen this saved prediction'}).getAttribute('href')).toBe(`/saved?review=${hash}`)
    const sent=JSON.parse(fetch.mock.calls[1][1].body)
    expect(sent.expected_latest_id).toBeNull();expect(sent.manifest_sha256).toBe(hash)
    view.unmount();fetch.mockImplementation(()=>ok({...target,history:[record]}));renderPanel()
    await screen.findByText('Revision 1: Needs correction')
    expect(screen.queryByText('No recorded decisions for this prediction.')).toBeNull()
  })
  it('keeps the draft and uses the same request when the acknowledgment fails',async()=>{
    const fetch=vi.fn().mockImplementationOnce(()=>ok(target)).mockRejectedValueOnce(new Error('Lost acknowledgment')).mockImplementationOnce(()=>ok(record))
    vi.stubGlobal('fetch',fetch);renderPanel();await fill()
    fireEvent.click(screen.getByText('Confirm and save locally'))
    await screen.findByRole('alert')
    expect(screen.getByLabelText(/Review note/).value).toBe('Synthetic review')
    expect(screen.queryByText(/Saved locally/)).toBeNull()
    fireEvent.click(screen.getByText('Retry same save'))
    await screen.findByText(/Saved locally — revision 1/)
    expect(fetch.mock.calls[2][1].body).toBe(fetch.mock.calls[1][1].body)
  })
  it('rejects a mismatched target and never enables saving',async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>ok({...target,manifest_sha256:otherHash})));renderPanel()
    await screen.findByRole('alert');expect(screen.queryByText('Review before saving')).toBeNull()
  })
  it('does not report success for a receipt belonging to another prediction',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockImplementationOnce(()=>ok(target)).mockImplementationOnce(()=>ok({...record,receipt:{...record.receipt,prediction_id:`prediction:${otherHash}`}})))
    renderPanel();await fill();fireEvent.click(screen.getByText('Confirm and save locally'))
    await screen.findByRole('alert');expect(screen.queryByText(/Saved locally/)).toBeNull()
  })
  it('binds a revision to the latest event and requires a note for Other',async()=>{
    const fetch=vi.fn(()=>ok({...target,history:[record]}));vi.stubGlobal('fetch',fetch);renderPanel()
    await screen.findByText('Revision 1: Needs correction')
    fireEvent.change(screen.getByLabelText('Your name'),{target:{value:'Invented operator'}})
    fireEvent.change(screen.getByLabelText('Decision'),{target:{value:'reject'}})
    fireEvent.click(screen.getByLabelText('Other'))
    expect(screen.getByText('Review before saving').disabled).toBe(true)
    fireEvent.change(screen.getByLabelText(/Review note/),{target:{value:'Cannot use the proposed outline'}})
    fireEvent.click(screen.getByText('Review before saving'));fireEvent.click(screen.getByText('Confirm and save locally'))
    await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(2))
    expect(JSON.parse(fetch.mock.calls[1][1].body).expected_latest_id).toBe(record.event.review_event_id)
  })
})
