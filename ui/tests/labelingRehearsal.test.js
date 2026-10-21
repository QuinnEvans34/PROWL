import { readFileSync, existsSync } from 'node:fs'
import { fireEvent, waitFor } from '@testing-library/dom'
import { beforeEach, expect, it, vi } from 'vitest'
import { startApp } from '../../src/retrieval/labeling_assets/app.js'
const asset='src/retrieval/labeling_assets/index.html'
const html=readFileSync(existsSync(asset)?asset:'../'+asset,'utf8')
const sources=[{id:'invented',text:'Exact invented source <script>unsafe()</script>'}]
const makeCase=(revision=1)=>({id:'one',revision,question:'Invented question?',state:'needs_review',consistency_reviewed:false,proposal_sha256:`hash${revision}`,provenance:{model:'Invented test model',seconds:0},proposal:{answerability:'answerable',meaning:revision===1?'Original meaning':'Corrected meaning',concepts:{c1:'Invented point'},evidence:{missing_direct_concepts:[],unresolved:[],rows:[{source_id:'invented',title:'Invented title',judgment:'direct',rationale:'Invented rationale',spans:[{quote:sources[0].text,grade:'direct',concept_ids:['c1']}]}]}}})
beforeEach(()=>{document.documentElement.innerHTML=html})
it('supports question, evidence review, correction, acceptance, consistency and export',async()=>{
  let cases=[];const requests=[];const exported=vi.fn()
  const fetcher=vi.fn(async(path,options)=>{
    const data=options.body?JSON.parse(options.body):null;requests.push({path,data})
    let result
    if(path==='/api/session')result={token:'test',sources,cases,examples:['Invented question?']}
    if(path==='/api/propose'){cases=[makeCase(data.case_id?2:1)];result=cases[0]}
    if(path==='/api/decision'){
      expect(data.reviewed_sources).toEqual(['invented']);expect(data.meaning_reviewed).toBe(true)
      cases[0]={...cases[0],state:'human_accepted_invented',consistency_reviewed:data.action==='consistency'};result=cases[0]
    }
    if(path==='/api/export')result={scope:'invented_rehearsal_only',cases}
    return {ok:true,json:async()=>structuredClone(result)}
  })
  await startApp(document,fetcher,exported).ready
  document.getElementById('author').value='Test operator'
  fireEvent.click(document.querySelector('#examples button'))
  fireEvent.click(document.getElementById('propose'))
  await waitFor(()=>expect(document.querySelector('.meaning')?.textContent).toBe('Original meaning'))
  expect(document.querySelector('#review script')).toBeNull()
  expect(document.querySelector('blockquote').textContent).toContain('<script>')
  fireEvent.click(document.getElementById('meaning-reviewed'));fireEvent.click(document.querySelector('[data-source]'))
  document.getElementById('correction').value='Please clarify the scope.'
  fireEvent.click(document.getElementById('revise'))
  await waitFor(()=>expect(document.querySelector('.meaning')?.textContent).toBe('Corrected meaning'))
  expect(document.getElementById('meaning-reviewed').checked).toBe(false)
  expect(document.querySelector('[data-source]').checked).toBe(false)
  expect(requests.filter(r=>r.path==='/api/propose')[1].data).toMatchObject({case_id:'one',revision:1,correction:'Please clarify the scope.'})
  fireEvent.click(document.getElementById('meaning-reviewed'));fireEvent.click(document.querySelector('[data-source]'))
  fireEvent.click(document.getElementById('accept'))
  await waitFor(()=>expect(document.getElementById('status').textContent).toContain('acceptance is recorded'))
  expect(document.getElementById('accept').disabled).toBe(true)
  fireEvent.click(document.getElementById('meaning-reviewed'));fireEvent.click(document.querySelector('[data-source]'))
  document.getElementById('correction').value='Compared scope and wording with the other question.'
  fireEvent.click(document.getElementById('consistency'))
  await waitFor(()=>expect(document.getElementById('status').textContent).toContain('consistency review is recorded'))
  fireEvent.click(document.getElementById('export'))
  await waitFor(()=>expect(exported).toHaveBeenCalledOnce())
  expect(exported.mock.calls[0][0].cases[0]).toMatchObject({revision:2,consistency_reviewed:true})
})
it('shows local-model failure and restores controls without an acceptance',async()=>{
  const fetcher=vi.fn(async path=>path==='/api/session'?{ok:true,json:async()=>({token:'test',sources,cases:[],examples:[]})}:{ok:false,json:async()=>({error:'Local model unavailable.'})})
  await startApp(document,fetcher).ready
  fireEvent.click(document.getElementById('propose'))
  await waitFor(()=>expect(document.getElementById('status').textContent).toBe('Local model unavailable.'))
  expect(document.getElementById('propose').disabled).toBe(false)
  expect(document.getElementById('actions').hidden).toBe(true)
})
