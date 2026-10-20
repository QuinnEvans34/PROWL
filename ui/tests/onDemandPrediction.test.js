// @vitest-environment node
import {it,expect,vi,afterEach} from 'vitest'
import {predictStudy} from '../src/lib/onDemandPrediction.js'
afterEach(()=>vi.unstubAllGlobals())
const job={job_id:'a'.repeat(32),case_id:'A',request_identity:'b'.repeat(64),status:'queued',error:null}
it('polls the same job and never starts a second prediction',async()=>{
 const fetcher=vi.fn(async(url,options)=>new Response(JSON.stringify(options?.method==='POST'?job:{...job,status:'ready'})))
 vi.stubGlobal('fetch',fetcher);const states=[]
 const result=await predictStudy('A',new AbortController().signal,s=>states.push(s),()=>{})
 expect(result.status).toBe('ready');expect(states).toEqual(['queued','ready'])
 expect(fetcher.mock.calls.filter(([,o])=>o.method==='POST')).toHaveLength(1)
})
it('cancels a job whose POST completes after its view has been abandoned',async()=>{
 const c=new AbortController();let resolve
 const fetcher=vi.fn((url,options)=>{
  if(url.endsWith('/jobs')&&options.method==='POST')return new Promise(r=>{resolve=r})
  return Promise.resolve(new Response(JSON.stringify({...job,status:'cancelled'})))
 })
 vi.stubGlobal('fetch',fetcher);const pending=predictStudy('A',c.signal,()=>{},()=>{});const caught=pending.catch(e=>e)
 c.abort();resolve(new Response(JSON.stringify(job)));await caught
 await new Promise(r=>setTimeout(r,10))
 expect(fetcher.mock.calls.some(([url])=>url.endsWith('/cancel'))).toBe(true)
})
it('rejects identity changes during polling',async()=>{
 const fetcher=vi.fn(async(url,options)=>new Response(JSON.stringify(url.endsWith('/jobs')?job:{...job,case_id:'B',status:'ready'})))
 vi.stubGlobal('fetch',fetcher)
 await expect(predictStudy('A',new AbortController().signal,()=>{},()=>{})).rejects.toThrow('identity changed')
})
