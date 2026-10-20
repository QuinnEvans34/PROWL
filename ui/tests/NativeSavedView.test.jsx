import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'
import SavedPredictionView from '../src/components/SavedPredictionView.jsx'
vi.mock('../src/lib/savedPrediction.js',()=>({loadSavedPrediction:vi.fn()}))
vi.mock('../src/components/NiivueViewer.jsx',()=>({default:()=> <div>Native viewer</div>}))
function pack(id, volume) {
  return {manifest:{case_id:id,result_sha256:id,warnings:[],geometry:{},files:{ct:{content_sha256:'ct'},pred:{content_sha256:'pred'}}},urls:{},release:vi.fn(),
    measurement:{status:'ready',pancreasMl:volume,lesionVoxels:0}}
}
async function ask(user) {
  await user.type(await screen.findByLabelText('Measurement question'),'How big is this pancreas?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
}
it('reload immediately removes the old native answer and releases the old package',async()=>{
  const user=userEvent.setup();const a=pack('A',44); let resolve
  loadSavedPrediction.mockResolvedValueOnce(a).mockImplementationOnce(()=>new Promise(r=>{resolve=r}))
  render(<SavedPredictionView/>);await ask(user);expect(screen.getByText(/44.00 mL/)).toBeTruthy()
  await user.click(screen.getByRole('button',{name:'Reload saved package'}))
  expect(screen.queryByText(/44.00 mL/)).toBeNull();expect(a.release).toHaveBeenCalledOnce()
  await act(async()=>resolve(pack('A-new',88)))
  expect(screen.getByLabelText('Measurement question').value).toBe('');expect(screen.queryByText(/44.00 mL/)).toBeNull()
})
it('a late native package cannot replace a different selected package',async()=>{
  let resolve;const a=pack('A',44);const b=pack('B',88)
  loadSavedPrediction.mockImplementationOnce(()=>new Promise(r=>{resolve=r})).mockResolvedValueOnce(b)
  const {rerender}=render(<SavedPredictionView base="/a"/>);rerender(<SavedPredictionView base="/b"/>)
  await screen.findByRole('heading',{name:'B'})
  await act(async()=>resolve(a))
  expect(screen.queryByRole('heading',{name:'A'})).toBeNull();expect(a.release).toHaveBeenCalledOnce()
})
