import { test,expect } from '@playwright/test'
import fs from 'node:fs'
const config=JSON.parse(fs.readFileSync(new URL('../../../configs/evidence/development-search-v1.json',import.meta.url)))
const candidate=JSON.parse(fs.readFileSync(new URL('../../../configs/evidence/single-summary-candidate-v1.json',import.meta.url)))
const quote='The invented gland releases digestive enzymes.'
function response(r,text){return {
 schema_version:'prowl-single-summary-response-v1',request_id:r.request_id,question:r.question,
 collection:config.collection,target:{manifest_sha256:config.manifest.sha256,inventory:{content_sha256:config.corpus_content_sha256}},
 state:'evidence_unassessed',reason:null,generation:'completed',answer_policy:candidate.policy,
 retrieval_policy:'source-linked-record-search-v1.1',record_selection:{policy:'source-linked-record-search-v1.1',status:'dense_fallback',reason:'unmatched',matches:[]},
 evidence:[{rank:1,score:1,record:{text:quote,passage:{passage_id:`psg:${'a'.repeat(64)}`},citation:{title:'Invented source',pmcid:'PMC123',pmid:'123',authors:['Example']},rights:{permissions:{display_snippet:true}}}}],
 answer:{...candidate,provenance:'model_synthesized_passages',validation:'citation_binding_only',coverage:'supported',status:'summarized',limitation:'',claims:[{text,citations:[{rank:1,quote}]}]}
}}

for (const variant of ['page','panel']) test(`synthetic summary citations and cancelled request isolation (${variant})`,async({page},testInfo)=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message))
 let held,release
 await page.route('**/*',async route=>{
   const url=new URL(route.request().url())
   if(url.hostname==='fonts.googleapis.com')return route.fulfill({contentType:'text/css',body:''})
   if(url.origin!=='http://127.0.0.1:5179')return route.abort()
   if(url.pathname==='/literature-search/answer'){
     const r=route.request().postDataJSON()
     if(r.question==='Delayed question'){
       held=true;await new Promise(resolve=>{release=resolve})
       return route.fulfill({json:response(r,'This cancelled answer must not appear.')}).catch(()=>{})
     }
     return route.fulfill({json:response(r,'It releases enzymes to help digest food.')})
   }
   return route.continue()
 })
 await page.goto('/?summary='+variant)
 if(variant==='panel'){
   await expect(page.getByRole('status',{name:'Synthetic viewer stub'})).toBeVisible()
   await page.getByRole('tab',{name:'Ask PROWL'}).click()
 }
 const input=page.getByLabel('Literature question')
 await input.fill('Delayed question')
 await page.getByRole('button',{name:'Ask question',exact:true}).click()
 await expect.poll(()=>held).toBe(true)
 await page.getByRole('button',{name:/Cancel/}).click()
 await input.fill('What does the invented gland do?')
 await page.getByRole('button',{name:'Ask question',exact:true}).click()
 await expect(page.getByRole('article',{name:'Literature search results'}).getByText('It releases enzymes to help digest food.')).toBeVisible()
 release()
 await page.getByRole('button',{name:'View source 1'}).click()
 await expect(page.getByText(quote,{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Answer',exact:true}).click()
 await expect(page.getByText('This cancelled answer must not appear.',{exact:true})).toHaveCount(0)
 await page.screenshot({path:testInfo.outputPath('synthetic-summary.png'),fullPage:true})
 expect(errors).toEqual([])
})
