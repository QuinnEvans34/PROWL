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

it('hides stale readiness after a failed check and allows recovery',async()=>{
  const ready={drive:true,database:true,search:true,ollama:true,model:true,gpu_busy:false}
  const fetch=vi.fn()
    .mockResolvedValueOnce({ok:true,json:async()=>ready})
    .mockRejectedValueOnce(new Error('Service disconnected.'))
    .mockResolvedValueOnce({ok:true,json:async()=>ready})
  vi.stubGlobal('fetch',fetch)
  render(<LocalExpertReadiness />)
  fireEvent.click(screen.getByText('Check status'))
  expect(await screen.findByText(/Source search is ready/)).toBeTruthy()
  fireEvent.click(screen.getByText('Check status'))
  expect(await screen.findByRole('alert')).toHaveProperty('textContent','Service disconnected.')
  expect(screen.queryByText(/Source search is ready/)).toBeNull()
  fireEvent.click(screen.getByText('Check status'))
  expect(await screen.findByText(/Source search is ready/)).toBeTruthy()
  expect(screen.queryByRole('alert')).toBeNull()
})
