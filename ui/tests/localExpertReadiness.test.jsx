import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import LocalExpertReadiness from '../src/components/LocalExpertReadiness'
afterEach(() => { cleanup(); vi.unstubAllGlobals() })
it('prepares explicitly and explains the teacher GPU reservation', async () => {
  const fetch = vi.fn().mockResolvedValue({ok:true,json:async()=>({drive:true,database:true,search:true,ollama:true,model:false,gpu_busy:true})})
  vi.stubGlobal('fetch',fetch)
  render(<LocalExpertReadiness />)
  expect(fetch).not.toHaveBeenCalled()
  fireEvent.click(screen.getByText('Prepare AI expert'))
  expect(await screen.findByText(/teacher is using the GPU/)).toBeTruthy()
  expect(fetch.mock.calls[0][0]).toBe('/local-expert/prepare')
  expect(fetch.mock.calls[0][1].method).toBe('POST')
})
it('shows the actionable mount failure',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({error:'Restart Docker Desktop to refresh its mount.'})}))
  render(<LocalExpertReadiness />)
  fireEvent.click(screen.getByText('Prepare AI expert'))
  expect(await screen.findByRole('alert')).toHaveProperty('textContent','Restart Docker Desktop to refresh its mount.')
})
