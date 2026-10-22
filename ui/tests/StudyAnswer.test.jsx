import { it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import fs from 'node:fs'
import path from 'node:path'
import LiteratureSearchPanel, { validateAnswer, validateSourceSearch } from '../src/components/LiteratureSearchPanel'
import config from '../../configs/evidence/development-search-v1.json'
import catalog from '../../configs/evidence/source-facts-ct-study-v4.json'
import wording from '../../configs/evidence/ct-study-answer-wording-v4.json'
import composer from '../../configs/evidence/ct-study-answer-v4.json'
afterEach(cleanup)
function fixture(request) {
 const r=catalog.records[1],pids=[...new Set(r.facts.flatMap(f=>f.evidence.map(id=>catalog.spans[id].passage_id)))].sort()
 const evidence=pids.map((pid,i)=>({rank:i+1,score:1,record:{text:`Invented study source ${i+1}.`,passage:{passage_id:pid},citation:{title:'Study fixture',pmcid:'PMC123',pmid:'123',authors:['Fixture author']},rights:{permissions:{display_snippet:true}}}}))
 return {schema_version:'prowl-study-answer-response-v1',answer_policy:composer.version,request_id:request.request_id,question:request.question,collection:config.collection,
 target:{manifest_sha256:config.manifest.sha256,inventory:{content_sha256:config.corpus_content_sha256}},state:'evidence_unassessed',reason:null,generation:'completed',evidence,
 retrieval_policy:'source-linked-study-search-v1',record_selection:{policy:'source-linked-study-search-v1',status:'matched',reason:'selected_ct_study_limits',matches:[{record_id:r.id,topic:r.topic,score:1,anchor_passage_ids:r.retrieval_anchors,evidence_passage_ids:pids}]},
 answer:{status:'summarized',policy:composer.version,provenance:'local_model_composition',failure:null,model:composer.model,model_sha256:composer.model_sha256,prompt_sha256:composer.prompt_sha256,wording_content_sha256:composer.wording_content_sha256,validation:'complete_reviewed_units_and_exact_citations',quality:'engineering_reviewed_independent_review_pending',scope:composer.scope,limitation:composer.limitation,
 claims:[false,true].map(limit=>{
  const units=wording.records[r.id].units.filter(u=>u.qualification===limit),ids=new Set(units.flatMap(u=>u.facts.flatMap(i=>r.facts[i].evidence.map(sid=>catalog.spans[sid].passage_id))))
  return {record_id:r.id,units:units.map(u=>({unit_id:u.id,wording:0})),text:units.map(u=>u.wordings[0]).join(' '),citations:evidence.filter(e=>ids.has(e.record.passage.passage_id)).map(e=>({rank:e.rank,quote:e.record.text}))}
 })}}
}
it('shows study limitations as prose and opens cited evidence separately',async()=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async q=>fixture(q)}/>)
 await user.type(screen.getByLabelText('Literature question'),'What limitations did the pancreatic tumor study report?')
 await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText(/retrospective data from one center/)).toBeTruthy()
 expect(screen.getByText(/could not evaluate how isoattenuating carcinomas differed/)).toBeTruthy()
 expect(screen.queryByText('Invented study source 1.')).toBeNull()
 await user.click(screen.getAllByRole('button',{name:'View source 1'})[0])
 expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
})
it.each(['qualification','citation','wrong family','prose'])('rejects %s corruption',kind=>{
 const req={question:'Study limits',request_id:'fixture'},r=fixture(req)
 if(kind==='qualification')r.answer.claims.pop()
 if(kind==='citation')r.answer.claims[0].citations[0].quote='Invented replacement'
 if(kind==='wrong family')r.retrieval_policy='source-linked-measurement-search-v1'
 if(kind==='prose')r.answer.claims[0].text='The test can diagnose any patient.'
 expect(()=>validateAnswer(r,req)).toThrow()
})
it.each(['clarification_size','clarification_negation','clarification_subject'])('shows a useful %s clarification without an AI answer',async reason=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async q=>{
  const r=fixture(q);return {...r,state:'not_searched',reason,evidence:[],generation:'not_called',answer:null,record_selection:{policy:r.retrieval_policy,status:'not_searched',reason,matches:[]}}
 }}/>)
 await user.type(screen.getByLabelText('Literature question'),'How big is it?');await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText('Clarify your question')).toBeTruthy()
 expect(screen.queryByLabelText('AI answer')).toBeNull()
})
const dirs=(process.env.PROWL_PUBLIC_CHECK_DIRS || '').split(path.delimiter).filter(Boolean)
it.skipIf(!dirs.length)('accepts every actual public HTTP response through the UI validation contract',()=>{
 for(const dir of dirs){
  const receipt=JSON.parse(fs.readFileSync(path.join(dir,'receipt.json'),'utf8'));expect(receipt.state).toBe('completed')
  receipt.cases.forEach((c,i)=>{
   const {request,response}=JSON.parse(fs.readFileSync(path.join(dir,`${String(i+1).padStart(2,'0')}.json`),'utf8'))
   expect(response.schema_version==='prowl-development-search-response-v1' ? validateSourceSearch(response,request) : validateAnswer(response,request)).toBe(response)
  })
 }
})
