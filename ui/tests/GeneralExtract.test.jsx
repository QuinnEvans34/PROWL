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
it('renders a general source answer and opens the exact citation',async()=>{
 const user=userEvent.setup();render(<LiteratureSearchPanel search={async r=>fixture(r)}/> )
 await user.type(screen.getByLabelText('Literature question'),'What does the pancreas do?')
 await user.click(screen.getByRole('button',{name:'Ask question'}))
 expect(await screen.findByText(/Source-based answer/)).toBeTruthy()
 expect(screen.getByText(quote)).toBeTruthy()
 await user.click(screen.getByRole('button',{name:'View source 1'}))
 expect(screen.getByText('Original excerpt [1]').closest('details').open).toBe(true)
})
it.each(['text','quote','rank','model','status','coverage'])('rejects altered %s',kind=>{
 const request={request_id:'test',question:'Question'},r=fixture(request)
 if(kind==='text')r.answer.claims[0].text='The gland releases invented hormones.'
 if(kind==='quote')r.answer.claims[0].citations[0].quote='Not source text'
 if(kind==='rank')r.answer.claims[0].citations[0].rank=8
 if(kind==='model')r.answer.model='unknown'
 if(kind==='status')r.answer.status='insufficient'
 if(kind==='coverage')r.answer.coverage='none'
 expect(()=>validateAnswer(r,request)).toThrow()
})
it('preserves passages on model timeout',()=>{
 const request={request_id:'test',question:'Question'},r=fixture(request)
 r.answer=null;r.generation='unavailable';r.message='Selection unavailable.'
 expect(validateAnswer(r,request)).toBe(r)
})
