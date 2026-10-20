import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { predictionCatalog, predictStudy, disposePrediction } from '../src/lib/onDemandPrediction.js'
import OnDemandPredictionView from '../src/components/OnDemandPredictionView.jsx'
vi.mock('../src/lib/onDemandPrediction.js',()=>({predictionCatalog:vi.fn(),predictStudy:vi.fn(),disposePrediction:vi.fn()}))
vi.mock('../src/components/SavedPredictionView.jsx',()=>({default:({base,expected})=><div>Verified viewer {expected.case_id} {base}</div>}))
function setup(){predictionCatalog.mockResolvedValue({configured:true,cases:[{case_id:'A'},{case_id:'B'}]});return userEvent.setup()}
it('unconfigured worker never presents a usable prediction button',async()=>{
 predictionCatalog.mockResolvedValue({configured:false,cases:[]});render(<OnDemandPredictionView/>);
 await screen.findByText(/worker is not connected/);expect(screen.getByRole('button',{name:'Run prediction'}).disabled).toBe(true)
})
it('one completed prediction supplies the result viewer and is released on scan change',async()=>{
 const user=setup();predictStudy.mockImplementation(async(id,signal,status,onJob)=>{onJob('a'.repeat(32));status('ready');return{case_id:id,job_id:'a'.repeat(32),request_identity:'b'.repeat(64)}})
 render(<OnDemandPredictionView/>);await screen.findByRole('option',{name:/A ·/});await user.selectOptions(screen.getByLabelText('Scan'),'A');await user.click(screen.getByRole('button',{name:'Run prediction'}));
 await screen.findByText(/Verified viewer A/);expect(predictStudy).toHaveBeenCalledOnce()
 await user.selectOptions(screen.getByLabelText('Scan'),'B');expect(screen.queryByText(/Verified viewer A/)).toBeNull();expect(disposePrediction).toHaveBeenCalledWith('a'.repeat(32))
})
it('ignores a late result after switching studies and cancels its job',async()=>{
 const user=setup();let resolve,jobCallback;predictStudy.mockImplementation((id,signal,status,onJob)=>{jobCallback=onJob;return new Promise(r=>{resolve=r})})
 render(<OnDemandPredictionView/>);await screen.findByRole('option',{name:/A ·/});await user.selectOptions(screen.getByLabelText('Scan'),'A');await user.click(screen.getByRole('button',{name:'Run prediction'}));
 await user.selectOptions(screen.getByLabelText('Scan'),'B');await act(async()=>{jobCallback('a'.repeat(32));resolve({case_id:'A',job_id:'a'.repeat(32)})});expect(screen.queryByText(/Verified viewer/)).toBeNull();expect(disposePrediction).toHaveBeenCalledWith('a'.repeat(32))
})
it('failed inference does not substitute a saved prediction',async()=>{
 const user=setup();predictStudy.mockRejectedValue(new Error('Worker failed'))
 render(<OnDemandPredictionView/>);await screen.findByRole('option',{name:/A ·/});await user.selectOptions(screen.getByLabelText('Scan'),'A');await user.click(screen.getByRole('button',{name:'Run prediction'}));
 await screen.findByRole('alert');expect(screen.queryByText(/Verified viewer/)).toBeNull()
})
