import { it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import fs from 'node:fs'
import path from 'node:path'
import LiteratureSearchPanel, { validateAnswer, validateSourceSearch } from '../src/components/LiteratureSearchPanel'
import config from '../../configs/evidence/development-search-v1.json'
import catalog from '../../configs/evidence/source-facts-measurement-v1.json'
import wording from '../../configs/evidence/measurement-answer-wording-v1.json'
import composer from '../../configs/evidence/measurement-answer-v1.json'
afterEach(cleanup)
const question='How does measuring pancreatic tumor diameter differ from measuring its volume on CT?'
function fixture(request,fallback=false) {
 const r=catalog.records[0],pids=[...new Set(r.facts.flatMap(f=>f.evidence.map(id=>catalog.spans[id].passage_id)))].sort()
 const evidence=pids.map((pid,i)=>({rank:i+1,score:1,record:{text:`Invented method source ${i+1}.`,passage:{passage_id:pid},citation:{title:'Method fixture',pmcid:'PMC7540900',pmid:'33027288',authors:['Fixture author'],year:'2020'},rights:{permissions:{display_snippet:true}}}}))
 return {schema_version:'prowl-measurement-answer-response-v1',answer_policy:composer.version,request_id:request.request_id,question:request.question,collection:config.collection,
 target:{manifest_sha256:config.manifest.sha256,inventory:{content_sha256:config.corpus_content_sha256}},state:'evidence_unassessed',reason:null,generation:fallback?'fallback':'completed',evidence,
 retrieval_policy:'source-linked-measurement-search-v1',record_selection:{policy:'source-linked-measurement-search-v1',status:'matched',reason:'selected_ct_measurement_method_not_patient_interpretation',matches:[{record_id:r.id,topic:r.topic,score:1,anchor_passage_ids:r.retrieval_anchors,evidence_passage_ids:pids}]},
 answer:{status:'summarized',policy:composer.version,provenance:fallback?'reviewed_source_fallback':'local_model_composition',failure:fallback?'timeout':null,model:fallback?null:composer.model,model_sha256:fallback?null:composer.model_sha256,prompt_sha256:composer.prompt_sha256,wording_content_sha256:composer.wording_content_sha256,validation:'complete_reviewed_units_and_exact_citations',quality:'engineering_reviewed_independent_review_pending',scope:composer.scope,limitation:composer.limitation,
 claims:[false,true].map(limit=>{
  const units=wording.records[r.id].units.filter(u=>u.qualification===limit),ids=new Set(units.flatMap(u=>u.facts.flatMap(i=>r.facts[i].evidence.map(sid=>catalog.spans[sid].passage_id))))
  return {record_id:r.id,units:units.map(u=>({unit_id:u.id,wording:0})),text:units.map(u=>u.wordings[0]).join(' '),citations:evidence.filter(e=>ids.has(e.record.passage.passage_id)).map(e=>({rank:e.rank,quote:e.record.text}))}
 })}}
}
it.each([false,true])('shows readable methods, separate qualifications and source navigation; fallback=%s',async fallback=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async q=>fixture(q,fallback)}/>)
 await user.type(screen.getByLabelText('Literature question'),question);await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText(/Diameter describes a length/)).toBeTruthy()
 expect(screen.getByText(/study was retrospective/)).toBeTruthy()
 expect(screen.getByText(/no measurement of your scan/)).toBeTruthy()
 expect(screen.getByText(fallback?/not model-written text/:/Local AI summary/)).toBeTruthy()
 expect(screen.queryByText('Invented method source 1.')).toBeNull()
 await user.click(screen.getAllByRole('button',{name:'View source 1'})[0])
 expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
})
it.each(['prose','qualifier','quote','source','duplicate','topic','schema','falseAI','anchor'])('rejects %s corruption',kind=>{
 const req={question,request_id:'fixture'},r=fixture(req)
 if(kind==='prose')r.answer.claims[0].text='Volume always proves cancer.'
 if(kind==='qualifier')r.answer.claims.pop()
 if(kind==='quote')r.answer.claims[0].citations[0].quote='Fabricated'
 if(kind==='source')r.evidence.pop()
 if(kind==='duplicate')r.record_selection.matches[0].evidence_passage_ids[0]=r.record_selection.matches[0].evidence_passage_ids[1]
 if(kind==='topic')r.record_selection.matches[0].topic='patient_diagnosis'
 if(kind==='schema')r.schema_version='prowl-volume-answer-response-v1'
 if(kind==='falseAI')r.generation='fallback'
 if(kind==='anchor')r.record_selection.matches[0].anchor_passage_ids=[]
 expect(()=>validateAnswer(r,req)).toThrow()
})
const dir=process.env.PROWL_MEASUREMENT_CHECK_DIR
it.skipIf(!dir)('replays every actual HTTP response through the UI contract',()=>{
 const receipt=JSON.parse(fs.readFileSync(path.join(dir,'receipt.json'),'utf8'));expect(receipt.automated_gate).toBe(true)
 for(const c of receipt.cases){
  const {request,response}=JSON.parse(fs.readFileSync(path.join(dir,c.id+'.json'),'utf8'))
  expect(response.schema_version==='prowl-development-search-response-v1'?validateSourceSearch(response,request):validateAnswer(response,request)).toBe(response)
 }
})
