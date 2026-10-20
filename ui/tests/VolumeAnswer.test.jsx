import { describe, it, expect } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel, { validateAnswer, validateSourceSearch } from '../src/components/LiteratureSearchPanel'
import config from '../../configs/evidence/development-search-v1.json'
import catalog from '../../configs/evidence/source-facts-volume-v1.json'
import wording from '../../configs/evidence/volume-answer-wording-v1.json'
import composer from '../../configs/evidence/volume-answer-v1.json'
afterEach(cleanup)
const groups = [
  ['object','extent','quantity','unit','population','sample_size','method','statistic','mean'],
  ['uncertainty','uncertainty_kind','unit'], ['matching'], ['population','sample_size','method'],
]
function fixture(request, fallback=false) {
  const required = r => [...new Set(Object.values(r.fields).flatMap(f=>f.evidence.map(id=>catalog.spans[id].passage_id)))].sort()
  const pids=required(catalog.records[0])
  const evidence=pids.map((pid,i)=>({rank:i+1,score:1,record:{text:`Invented volume source ${i+1}.`,passage:{passage_id:pid},
    citation:{title:'Volume study fixture',pmcid:'PMC4423920',pmid:'25950180',authors:['Fixture author'],year:'2015'},rights:{permissions:{display_snippet:true}}}}))
  const result={schema_version:'prowl-volume-answer-response-v1',answer_policy:composer.version,
    request_id:request.request_id,question:request.question,collection:config.collection,
    target:{manifest_sha256:config.manifest.sha256,inventory:{content_sha256:config.corpus_content_sha256}},
    state:'evidence_unassessed',reason:null,generation:fallback?'fallback':'completed',evidence,
    retrieval_policy:'source-linked-volume-search-v1',record_selection:{policy:'source-linked-volume-search-v1',status:'matched',reason:'selected_study_examples_not_reference_ranges',
      matches:catalog.records.map(r=>({record_id:r.id,population:r.fields.population.value,score:1,evidence_passage_ids:required(r)}))}}
  result.answer={status:'summarized',policy:composer.version,provenance:fallback?'reviewed_source_fallback':'local_model_composition',failure:fallback?'timeout':null,
    model:fallback?null:composer.model,model_sha256:fallback?null:composer.model_sha256,prompt_sha256:composer.prompt_sha256,wording_content_sha256:composer.wording_content_sha256,
    validation:'complete_reviewed_units_and_exact_citations',quality:'engineering_reviewed_independent_review_pending',scope:composer.scope,limitation:composer.limitation,
    claims:catalog.records.flatMap(r=>[false,true].map(limit=>{
      const units=wording.records[r.id].units.filter(u=>u.qualification===limit)
      const ids=new Set(units.flatMap(u=>u.facts.flatMap(i=>groups[i].flatMap(f=>r.fields[f].evidence.map(s=>catalog.spans[s].passage_id)))))
      return {record_id:r.id,units:units.map(u=>({unit_id:u.id,wording:1})),text:units.map(u=>u.wordings[1]).join(' '),citations:evidence.filter(e=>ids.has(e.record.passage.passage_id)).map(e=>({rank:e.rank,quote:e.record.text}))}
    }))}
  return result
}
const request={request_id:'fixture',question:'Compare mean pancreas volume in normal glucose tolerance versus type 2 diabetes.'}
it.each([false,true])('renders separate groups and opens exact sources; fallback=%s',async fallback=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async q=>fixture(q,fallback)}/> )
 await user.type(screen.getByLabelText('Literature question'),request.question)
 await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText(/82.6 cm³ among 14 people/)).toBeTruthy()
 expect(screen.getByText(/55.5 cm³ among 41 people/)).toBeTruthy()
 expect(screen.getAllByText(/cannot tell you whether an individual scan/)).toHaveLength(2)
 expect(screen.queryByText('Invented volume source 1.')).toBeNull()
 expect(screen.getByText(fallback?/not model-written text/:/local AI selected reviewed wording/)).toBeTruthy()
 await user.click(screen.getAllByRole('button',{name:'View source 1'})[0])
 expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
})
it.each(['number','population','sem','qualification','quote','rank','missing','extra','policy','schema','falseAI','pin','order'])('rejects %s corruption',kind=>{
 const r=fixture(request)
 if(kind==='number')r.answer.claims[0].text=r.answer.claims[0].text.replace('82.6','55.5')
 if(kind==='population')r.record_selection.matches[0].population='healthy'
 if(kind==='sem')r.answer.claims[0].units.splice(1,1)
 if(kind==='qualification')r.answer.claims.pop()
 if(kind==='quote')r.answer.claims[0].citations[0].quote='Fake'
 if(kind==='rank')r.answer.claims[0].citations[0].rank=99
 if(kind==='missing')r.evidence.pop()
 if(kind==='extra')r.record_selection.matches.push(r.record_selection.matches[0])
 if(kind==='policy')r.retrieval_policy='source-linked-record-search-v1'
 if(kind==='schema')r.schema_version='prowl-record-answer-response-v1'
 if(kind==='falseAI')r.generation='fallback'
 if(kind==='pin')r.answer.prompt_sha256='wrong'
 if(kind==='order')r.answer.claims.reverse()
 expect(()=>validateAnswer(r,request)).toThrow()
})
it('clarifies size without claiming an AI answer',async()=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async q=>{
  const r=fixture(q);r.answer=null;r.generation='not_called';r.record_selection={policy:r.retrieval_policy,status:'dense_fallback',reason:'specify_volume_or_linear_size',matches:[]};return r
 }}/>)
 await user.type(screen.getByLabelText('Literature question'),'How large is the average pancreas?')
 await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText(/Do you mean the volume/)).toBeTruthy()
 expect(screen.queryByLabelText('AI answer')).toBeNull()
})
it('accepts source-only volume context without an answer',()=>{
 const r=fixture(request);r.schema_version='prowl-development-search-response-v1';r.answer=null;r.generation='not_called'
 expect(validateSourceSearch(r,request)).toBe(r)
})
