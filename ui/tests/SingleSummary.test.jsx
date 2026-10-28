import candidate from '../../configs/evidence/single-summary-candidate-v1.json'
import React from 'react'
import {it,expect,afterEach} from 'vitest'
import {render,screen,cleanup} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel,{validateAnswer} from '../src/components/LiteratureSearchPanel'
import config from '../../configs/evidence/development-search-v1.json'
afterEach(cleanup)
const quote='The invented gland releases digestive enzymes.'
function fixture(r){return {schema_version:'prowl-general-extract-response-v1',request_id:r.request_id,question:r.question,
 collection:config.collection,target:{manifest_sha256:config.manifest.sha256,inventory:{content_sha256:config.corpus_content_sha256}},state:'evidence_unassessed',reason:null,generation:'completed',
 answer_policy:'general-source-extract-v1',retrieval_policy:'source-linked-record-search-v1.1',record_selection:{policy:'source-linked-record-search-v1.1',status:'dense_fallback',reason:'unmatched',matches:[]},
 evidence:[{rank:1,score:1,record:{text:quote,passage:{passage_id:`psg:${'a'.repeat(64)}`},citation:{title:'Invented source',pmcid:'PMC123',pmid:'123',authors:['Example']},rights:{permissions:{display_snippet:true}}}}],
 answer:{prompt_sha256:'cb216828f532b41c3913f37c668ae25b8f96bd4ca287c476bcad37e601e545d6',policy:'general-source-extract-v1',model:'qwen3:8b',model_sha256:'500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41',provenance:'model_selected_source_sentences',validation:'exact_source_sentences',coverage:'supported',status:'summarized',limitation:'Selected quotations.',claims:[{text:quote,citations:[{rank:1,quote}]}]}}}

function summary(r) {
 const result=fixture(r)
 result.schema_version='prowl-single-summary-response-v1';result.answer_policy=candidate.policy
 result.answer={...candidate,provenance:'model_synthesized_passages',validation:'citation_binding_only',coverage:'supported',status:'summarized',limitation:'',claims:[{text:'It releases enzymes to help digest food.',citations:[{rank:1,quote}]}]}
 return result
}
it('shows clean summary first and opens cited source separately',async()=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async r=>summary(r)}/> )
 await user.type(screen.getByLabelText('Literature question'),'What does the pancreas do?')
 await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText(/AI summary/)).toBeTruthy()
 expect(screen.getByText('It releases enzymes to help digest food.')).toBeTruthy()
 expect(screen.queryByText(quote)).toBeNull()
 await user.click(screen.getByRole('button',{name:'View source 1'}))
 expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
 await user.click(screen.getByRole('button',{name:'Answer',exact:true}))
 expect(screen.getByText('It releases enzymes to help digest food.')).toBeTruthy()
})
it.each(['quote','rank','provenance','coverage'])('rejects invalid summary %s',kind=>{
 const request={request_id:'test',question:'Question'},r=summary(request)
 if(kind==='quote')r.answer.claims[0].citations[0].quote='An entirely invented supporting excerpt.'
 if(kind==='rank')r.answer.claims[0].citations[0].rank=99
 if(kind==='provenance')r.answer.validation='factually_verified'
 if(kind==='coverage')r.answer.coverage='none'
 expect(()=>validateAnswer(r,request)).toThrow()
})

it.each(['page','panel'])('shows partial and missing-evidence limits in %s',async variant=>{
 const user=userEvent.setup();let gap=false
 render(<LiteratureSearchPanel variant={variant} search={async r=>{
   const result=summary(r)
   result.answer.coverage=gap?'none':'partial'
   result.answer.limitation=gap?'The retrieved sources do not provide that range.':'The retrieved sources do not establish a normal range.'
   if(gap){result.answer.status='insufficient';result.answer.claims=[]}
   return result
 }}/>)
 const input=screen.getByLabelText('Literature question')
 await user.type(input,'What does the pancreas do and what is the normal range?')
 await user.click(screen.getByRole('button',{name:'Ask question',exact:true}))
 expect(await screen.findByText('The retrieved sources do not establish a normal range.')).toBeTruthy()
 gap=true;await user.clear(input);await user.type(input,'What is the pancreatic stiffness range?')
 await user.click(screen.getByRole('button',{name:'Ask question',exact:true}))
 expect(await screen.findByText('The retrieved sources do not provide that range.')).toBeTruthy()
 expect(screen.queryByText('It releases enzymes to help digest food.')).toBeNull()
 await user.click(screen.getByRole('button',{name:'Read passages',exact:true}))
 expect(screen.getByText(quote)).toBeTruthy()
})

it.each(['page','panel'])('preserves source access after candidate failure in %s',async variant=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel variant={variant} search={async r=>{
   const result=summary(r);result.answer=null;result.generation='unavailable';result.message='The summary could not be completed. You can still inspect the retrieved passages.';return result
 }}/>)
 await user.type(screen.getByLabelText('Literature question'),'What does the pancreas do?')
 await user.click(screen.getByRole('button',{name:'Ask question',exact:true}))
 expect(await screen.findByText(/summary could not be completed/)).toBeTruthy()
 expect(screen.getByText(quote)).toBeTruthy()
 expect(screen.queryByRole('button',{name:'Answer',exact:true})).toBeNull()
})
