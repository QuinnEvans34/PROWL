import { it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { validateSearch } from '../src/components/LiteratureSearchPanel'
import { validateRecordAnswer } from '../src/components/recordAnswer'
import { validateMeasurementSources } from '../src/components/measurementAnswer'
import searchConfig from '../../configs/evidence/development-study-search-v4.json'
import catalog from '../../configs/evidence/source-facts-ct-study-v4.json'
import config from '../../configs/evidence/ct-study-answer-v4.json'
import wording from '../../configs/evidence/ct-study-answer-wording-v4.json'
const reasons = ['selected_ct_visibility','selected_ct_study_limits','selected_ct_reader_variation','selected_ct_radiomics_limits','selected_ct_contour_protocol',
 ...catalog.records.filter(r => !r.topic.startsWith('ct_')).map(r => 'selected_'+r.topic)]
const sources = (r,q) => validateMeasurementSources(r,q,validateSearch,{searchConfig,catalog,reasons})
const validate = (r,q) => validateRecordAnswer(r,q,sources,{config,wording,catalog,schema:'prowl-study-answer-response-v1'})
const dirs=(process.env.PROWL_PUBLIC_CHECK_DIRS || '').split(path.delimiter).filter(Boolean)
it.skipIf(!dirs.length)('accepts candidate study responses before changing the live UI contract',()=>{
 let checked=0
 for(const dir of dirs){
  const receipt=JSON.parse(fs.readFileSync(path.join(dir,'receipt.json'),'utf8'));expect(receipt.state).toBe('completed')
  receipt.cases.forEach((_,i)=>{
   const {request,response}=JSON.parse(fs.readFileSync(path.join(dir,`${String(i+1).padStart(2,'0')}.json`),'utf8'))
   if(response.retrieval_policy==='source-linked-study-search-v1'){
    expect(validate(response,request)).toBe(response);checked++
    if(response.answer){
     const changed=structuredClone(response);changed.answer.claims.pop()
     expect(()=>validate(changed,request)).toThrow()
     const wrongSource=structuredClone(response);wrongSource.answer.claims[0].citations[0].quote='Unrelated evidence'
     expect(()=>validate(wrongSource,request)).toThrow()
    }
   }
  })
 }
 expect(checked).toBeGreaterThan(0)
})
