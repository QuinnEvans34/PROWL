import React, { useEffect, useRef, useState } from 'react'
import { validateAnswer, LiteratureReadingView } from './LiteratureSearchPanel.jsx'

const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value)
export default function ReviewLiteratureAttachments({ manifestHash, event, receipt, request }) {
  const [rows,setRows]=useState(null), [draft,setDraft]=useState(null), [opened,setOpened]=useState(null)
  const [error,setError]=useState(''), [notice,setNotice]=useState(''), [busy,setBusy]=useState(false)
  const alive=useRef(true), selection=useRef(0)
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;selection.current++}},[])
  const endpoint=`literature/${manifestHash}/${event.review_event_id}`
  function valid(row) {
    return row?.manifest_sha256===manifestHash && row.review_event_id===event.review_event_id
      && /^review-literature:[a-f0-9]{64}$/.test(row.artifact_id) && hash(row.receipt_sha256)
  }
  async function load() {
    setBusy(true);setError('')
    try {
      const value=await request(endpoint)
      if (!Array.isArray(value.attachments) || !value.attachments.every(r=>valid(r)&&typeof r.question==='string')) throw Error('Attachment history could not be verified.')
      if(alive.current)setRows(value.attachments)
    } catch(e){if(alive.current)setError(e.status===404?'Literature attachments are not enabled on this review service yet.':e.message)}
    finally{if(alive.current)setBusy(false)}
  }
  async function select(file) {
    const token=++selection.current
    setDraft(null);setError('');setNotice('')
    if(!file)return
    try {
      if(file.size>1024*1024)throw Error('Choose a response capture no larger than 1 MiB.')
      const text=await file.text(), capture=JSON.parse(text)
      if(Object.keys(capture).sort().join(',')!=='request,response' || Object.keys(capture.request||{}).sort().join(',')!=='question,request_id')throw Error('Choose a PROWL response capture JSON file.')
      validateAnswer(capture.response,capture.request)
      if(alive.current && token===selection.current)setDraft({text,capture})
    }catch(e){if(alive.current && token===selection.current)setError('This capture could not be validated. '+e.message)}
  }
  async function save() {
    setBusy(true);setError('');setNotice('')
    try {
      const result=await request(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({capture_text:draft.text,review_receipt:receipt})})
      if(!valid(result))throw Error('Attachment acknowledgment could not be verified. Retry the same capture.')
      if(!alive.current)return
      setDraft(null);setNotice(`Response attached to revision ${event.revision}. Your decision is unchanged.`)
      await load()
    }catch(e){if(alive.current)setError(e.message+' The capture remains selected; retry to recover its receipt.')}
    finally{if(alive.current)setBusy(false)}
  }
  async function reopen(row) {
    setBusy(true);setError('');setOpened(null)
    try {
      const value=await request(`literature-capture/${row.artifact_id.split(':')[1]}/${row.receipt_sha256}`)
      if(value.binding?.manifest_sha256!==manifestHash || value.binding.review_event_id!==event.review_event_id
        || value.binding.decision_changed!==false || value.review?.receipt?.content_sha256!==receipt.content_sha256
        || value.review?.event?.review_event_id!==event.review_event_id)throw Error('Attachment belongs to a different review.')
      validateAnswer(value.capture.response,value.capture.request)
      if(alive.current)setOpened(value.capture)
    }catch(e){if(alive.current)setError(e.message)}
    finally{if(alive.current)setBusy(false)}
  }
  return <details onToggle={e=>{if(e.currentTarget.open && rows===null && !busy)load()}}>
    <summary>Literature attached to revision {event.revision}</summary>
    <p>Associate a downloaded response with this exact revision. This does not change your decision or establish a diagnosis.</p>
    {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
    <button disabled={busy} onClick={load}>Reload attachments</button>
    {rows!==null&&<>
      {!rows.length&&<p>No literature attached to this revision.</p>}
      <ul>{rows.map(row=><li key={row.artifact_id}><button disabled={busy} onClick={()=>reopen(row)}>{row.question}</button></li>)}</ul>
      <label>Response capture for revision {event.revision}<input type="file" accept=".json,application/json" disabled={busy} onChange={e=>select(e.target.files?.[0])}/></label>
      {draft&&<div><p>Attach “{draft.capture.request.question}” to revision {event.revision}?</p>
        <p>The response and citations will be retained locally. General literature does not become a finding about this scan.</p>
        <button disabled={busy} onClick={save}>Confirm attachment to revision {event.revision}</button>
        <button disabled={busy} onClick={()=>{selection.current++;setDraft(null)}}>Cancel attachment</button></div>}
    </>}
    {opened&&<section aria-label="Attached literature response"><h4>{opened.request.question}</h4>
      <p>{opened.response.generation==='not_called'?'No answer model was called.':opened.response.answer?'Retained response — inspect the cited evidence.':'No checked answer was produced.'}</p>
      {opened.response.message&&<p>{opened.response.message}</p>}
      {!opened.response.evidence.length&&opened.response.answer?.limitation&&<p>{opened.response.answer.limitation}</p>}
      {opened.response.evidence.length>0&&<LiteratureReadingView key={opened.request.request_id} evidence={opened.response.evidence} answer={opened.response.answer}/>}
    </section>}
  </details>
}
