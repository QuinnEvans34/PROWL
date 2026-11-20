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
 answer:{...candidate,provenance:'model_synthesized_passages',validation:'citation_binding_and_model_review',coverage:'supported',status:'summarized',limitation:'',claims:[{text,citations:[{rank:1,quote}]}]}
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
   await expect(page.getByRole('status',{name:'Synthetic viewer stub'})).toHaveCount(1)
   await expect(page.getByRole('status',{name:'Synthetic viewer stub'}).first()).toBeVisible()
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

for (const variant of ['page', 'panel']) test(`contextual follow-up transport and source access (${variant})`, async ({ page }) => {
 const requests = []
 await page.route('**/*', async route => {
   const url = new URL(route.request().url())
   if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ contentType: 'text/css', body: '' })
   if (url.origin !== 'http://127.0.0.1:5179') return route.abort()
   if (url.pathname !== '/literature-search/answer') return route.continue()
   const body = route.request().postDataJSON()
   requests.push(body)
   const request = body.request || body
   const result = response(request, 'An invented research explanation for this interface test.')
   result.context = { policy: 'pancreatic-conversation-v1', topic: 'pancreatic research',
     resolved_question: request.question === 'Does it produce insulin?' ? 'Does the pancreas produce insulin?' : request.question,
     previous_questions: body.conversation?.map(turn => turn.question) || [] }
   return route.fulfill({ json: result })
 })
 await page.goto('/?summary=' + variant)
 if (variant === 'panel') await page.getByRole('tab', { name: 'Ask PROWL' }).click()
 const input = page.getByLabel('Literature question')
 const current = page.getByRole('article', { name: 'Literature search results' })
 await input.fill('What does the pancreas do?')
 await page.getByRole('button', { name: 'Ask question', exact: true }).click()
 await expect(current.getByText('An invented research explanation for this interface test.')).toBeVisible()
 await input.fill('Does it produce insulin?')
 await page.getByRole('button', { name: 'Ask question', exact: true }).click()
 await expect(current.getByText('How I understood your question')).toBeVisible()
 expect(requests[1].conversation).toEqual([{ question: 'What does the pancreas do?' }])
 expect(requests[1].request.question).toBe('Does it produce insulin?')
 expect(requests[1]).not.toHaveProperty('answer')
 await current.getByText('How I understood your question').click()
 await expect(current.getByText('Does the pancreas produce insulin?', { exact: true })).toBeVisible()
 await current.getByRole('button', { name: 'View source 1' }).click()
 await expect(current.getByRole('link', { name: /Read full source/ })).toHaveAttribute('href', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC123/')
 await page.getByRole('button', { name: 'Clear recent responses' }).click()
 await input.fill('Where is the pancreas located?')
 await page.getByRole('button', { name: 'Ask question', exact: true }).click()
 await expect(current.getByText('An invented research explanation for this interface test.')).toBeVisible()
 expect(requests[2].question).toBe('Where is the pancreas located?')
 expect(requests[2]).not.toHaveProperty('conversation')
})
