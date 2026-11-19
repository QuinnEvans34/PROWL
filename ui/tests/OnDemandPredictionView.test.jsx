import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { predictionCatalog, predictStudy, disposePrediction } from '../src/lib/onDemandPrediction.js'
import OnDemandPredictionView from '../src/components/OnDemandPredictionView.jsx'
vi.mock('../src/lib/onDemandPrediction.js',()=>({predictionCatalog:vi.fn(),predictStudy:vi.fn(),disposePrediction:vi.fn()}))
function setup(){predictionCatalog.mockResolvedValue({configured:true,cases:[{case_id:'A'},{case_id:'B'}]});return userEvent.setup()}
const ready = {case_id:'A',job_id:'a'.repeat(32),request_identity:'b'.repeat(64),status:'ready'}
function completes(){
  predictStudy.mockImplementation(async(id,signal,status,onJob)=>{
    onJob(ready.job_id);status('ready');return {...ready,case_id:id}
  })
}
it('unconfigured worker never presents a usable prediction button',async()=>{
 predictionCatalog.mockResolvedValue({configured:false,cases:[]});render(<OnDemandPredictionView/>);
 await screen.findByText(/worker is not connected/);expect(screen.getByRole('button',{name:'Run prediction'}).disabled).toBe(true)
})
it('releases a completed prediction on scan change before it is handed off',async()=>{
 const user=setup();completes()
 render(<OnDemandPredictionView/>);await screen.findByRole('option',{name:/A ·/});await user.selectOptions(screen.getByLabelText('Scan'),'A');await user.click(screen.getByRole('button',{name:'Run prediction'}));
 await screen.findByRole('button',{name:'Open prediction in Workbench'});expect(predictStudy).toHaveBeenCalledOnce()
 await user.selectOptions(screen.getByLabelText('Scan'),'B');expect(screen.queryByRole('button',{name:'Open prediction in Workbench'})).toBeNull();expect(disposePrediction).toHaveBeenCalledWith(ready.job_id)
})
it('transfers the ready job only when Workbench accepts navigation',async()=>{
 const user=setup();completes()
 const openWorkbench=vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true)
 const {unmount}=render(<OnDemandPredictionView onOpenWorkbench={openWorkbench}/>)
 await screen.findByRole('option',{name:/A ·/})
 await user.selectOptions(screen.getByLabelText('Scan'),'A')
 await user.click(screen.getByRole('button',{name:'Run prediction'}))
 const open=await screen.findByRole('button',{name:'Open prediction in Workbench'})
 await user.click(open)
 await user.click(open)
 expect(openWorkbench).toHaveBeenCalledTimes(2)
 expect(openWorkbench).toHaveBeenLastCalledWith(ready)
 unmount()
 expect(disposePrediction).not.toHaveBeenCalled()
})
it('ignores a late result after switching studies and cancels its job',async()=>{
 const user=setup();let resolve,jobCallback;predictStudy.mockImplementation((id,signal,status,onJob)=>{jobCallback=onJob;return new Promise(r=>{resolve=r})})
 render(<OnDemandPredictionView/>);await screen.findByRole('option',{name:/A ·/});await user.selectOptions(screen.getByLabelText('Scan'),'A');await user.click(screen.getByRole('button',{name:'Run prediction'}));
 await user.selectOptions(screen.getByLabelText('Scan'),'B');await act(async()=>{jobCallback(ready.job_id);resolve(ready)});expect(screen.queryByRole('button',{name:'Open prediction in Workbench'})).toBeNull();expect(disposePrediction).toHaveBeenCalledWith(ready.job_id)
})
it('failed inference does not substitute a saved prediction',async()=>{
 const user=setup();predictStudy.mockRejectedValue(new Error('Worker failed'))
 render(<OnDemandPredictionView/>);await screen.findByRole('option',{name:/A ·/});await user.selectOptions(screen.getByLabelText('Scan'),'A');await user.click(screen.getByRole('button',{name:'Run prediction'}));
 await screen.findByRole('alert');expect(screen.queryByRole('button',{name:'Open prediction in Workbench'})).toBeNull()
})
