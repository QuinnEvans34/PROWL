import React from 'react'
import { it,expect,vi } from 'vitest'
import { render,screen,waitFor } from '@testing-library/react'
import TrainingPage from '../src/pages/TrainingPage.jsx'
import snapshot from '../../configs/training-hours/recorded-hours-v1.json'
import { parseLocation,hrefFor } from '../src/lib/router.js'

it('routes directly to training without selecting a scan',()=>{
 expect(parseLocation({pathname:'/training',search:''}).view).toBe('training')
 expect(hrefFor({view:'training',study:'irrelevant'})).toBe('/training')
})
it('shows machine totals and distinguishes timestamp estimates and teacher work',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({...snapshot,refresh_state:'local_read'}))))
 render(<TrainingPage />)
 await screen.findByText('Local counters checked. Lenovo uses its verified export.')
 expect(screen.getByText('Teacher targets')).toBeTruthy()
 expect(screen.getByText(/not measure GPU-busy time/)).toBeTruthy()
 expect(screen.getByText(/Historical MLflow durations/)).toBeTruthy()
 expect(screen.getByText(/rather than a third machine/)).toBeTruthy()
})
it('retains the snapshot on a failed live read instead of showing zero',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('',{status:503})))
 render(<TrainingPage />)
 await screen.findByText(/Live accounting is unavailable/)
 expect(screen.getByLabelText('Recorded training sessions').textContent).toContain((snapshot.totals.recorded_training_seconds/3600).toFixed(1))
})
