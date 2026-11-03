// @vitest-environment node
// Explicit private-package check. CI never discovers or reads local imaging data.
import { it, expect, vi } from 'vitest'
import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'
const folder=process.env.PROWL_PHYSICAL_PACKAGE
it.skipIf(!folder)('verifies and measures an explicitly selected physical package without rendering or inference',async()=>{
 const files=new Set(['manifest.json','ct.nii.gz','prediction.nii.gz','result.json','evidence.json'])
 vi.stubGlobal('fetch',vi.fn(async url=>{
   const name=url.split('/').at(-1)
   if(!files.has(name))throw new Error('Unexpected artifact request')
   return new Response(readFileSync(resolve(folder,name)))
 }))
 const before=performance.now()
 const loaded=await loadSavedPrediction('/explicit-private-package')
 try{
   expect(loaded.manifest.schema_version).toBe('physical-prediction-view-v1')
   expect(['ready','unavailable']).toContain(loaded.measurement.status)
   if(loaded.measurement.status==='unavailable'){
     expect(loaded.measurement.reason).toBeTruthy()
     expect(loaded.measurement.pancreasMl).toBeUndefined()
   }
   const receipt={scope:'actual-private-package-CPU-check; no render, inference or human review',
     manifest_sha256:loaded.manifestHash,case_id:loaded.manifest.case_id,
     measurement:loaded.measurement,seconds:(performance.now()-before)/1000}
   if(process.env.PROWL_PHYSICAL_RECEIPT)writeFileSync(process.env.PROWL_PHYSICAL_RECEIPT,JSON.stringify(receipt,null,2))
 }finally{loaded.release();vi.unstubAllGlobals()}
})
