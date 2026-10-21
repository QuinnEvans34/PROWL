export function startApp(doc=document, fetcher=fetch, download=defaultDownload) {
  const $=id=>doc.getElementById(id);
  let token='', state={cases:[],sources:[]}, current=null, busy=false;
  const controls=['propose','revise','accept','reject','consistency','export','cases','author','question'];
  function notice(text,error=false){$('status').textContent=text;$('status').className=error?'error':'';}
  function buttons(){
    for(const id of controls)$(id).disabled=busy;
    if(!busy){
      $('revise').disabled=!current;
      $('accept').disabled=!current || current.state!=='needs_review';
      $('reject').disabled=!current || current.state!=='needs_review';
      $('consistency').disabled=!current || current.state!=='human_accepted_invented' || current.consistency_reviewed;
    }
  }
  async function api(path,data){
    const response=await fetcher(path,data===undefined?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify(data)});
    const result=await response.json();if(!response.ok)throw Error(result.error||'The local request failed.');return result;
  }
  function node(tag,text,cls){const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  const names={direct:'Supports a requested fact',partial_context:'Adds context or a qualification',contradicting_or_limiting:'Conflict needs review',not_relevant:'Does not answer this question',uncertain:'Support is uncertain'};
  function renderCase(c){
    current=c;const root=$('review');root.replaceChildren();$('actions').hidden=!c;$('meaning-reviewed').checked=false;$('correction').value='';
    if(!c){root.append(node('p','Your proposed meaning and source excerpts will appear here.','empty'));buttons();return;}
    root.append(node('p',c.question),node('span',`Revision ${c.revision} · ${c.state==='needs_review'?'Needs your review':c.state==='rejected'?'Rejected':'Accepted for rehearsal'}${c.consistency_reviewed?' · Consistency reviewed':''}`,'badge'));
    root.append(node('h3',c.proposal.answerability==='answerable'?'Proposed meaning':'Proposed evidence gap'),node('p',c.proposal.meaning,'meaning'));
    root.append(node('p',`Prepared by ${c.provenance.model} · ${c.provenance.seconds}s · Review every source below.`,'small'));
    const e=c.proposal.evidence;
    if(e.missing_direct_concepts.length)root.append(node('p','Not directly supported: '+e.missing_direct_concepts.map(id=>c.proposal.concepts[id]).join('; '),'warning'));
    if(e.unresolved.length)root.append(node('p','Some evidence is uncertain or conflicting. Request a correction before acceptance.','warning'));
    for(const row of e.rows){
      const section=node('article',undefined,'source');section.append(node('h3',row.title),node('span',names[row.judgment],'badge'),node('p',row.rationale));
      for(const span of row.spans){section.append(node('blockquote',span.quote));section.append(node('p',names[span.grade]+(span.concept_ids.length?' — '+span.concept_ids.map(id=>c.proposal.concepts[id]).join('; '):''),'small'));}
      const details=node('details'),summary=node('summary','Read full source context');details.append(summary,node('p',state.sources.find(s=>s.id===row.source_id).text));section.append(details);
      const label=node('label',undefined,'check'),checkbox=node('input');checkbox.type='checkbox';checkbox.dataset.source=row.source_id;
      label.append(checkbox,node('span','I reviewed this source and its proposed relevance.'));section.append(label);root.append(section);
    }
    buttons();
  }
  async function refresh(selected){
    state=await api('/api/session');token=state.token;
    const select=$('cases');select.replaceChildren(node('option','Select a reviewed question'));select.firstChild.value='';
    for(const c of state.cases){const option=node('option',c.question);option.value=c.id;select.append(option);}
    const chosen=state.cases.find(c=>c.id===selected)||null;select.value=chosen?.id||'';renderCase(chosen);
  }
  async function run(work,message){
    busy=true;buttons();notice(message);
    try{await work();}catch(error){notice(error.message||'The local service is unavailable. Please retry.',true);}
    finally{busy=false;buttons();}
  }
  $('propose').onclick=()=>run(async()=>{
    const c=await api('/api/propose',{question:$('question').value,author:$('author').value,correction:'',case_id:null,revision:null});
    await refresh(c.id);notice('Proposal ready. Check the meaning and every source before deciding.');
  },'Reading the fictional sources with the local model…');
  $('revise').onclick=()=>run(async()=>{
    const c=await api('/api/propose',{question:current.question,author:$('author').value,correction:$('correction').value,case_id:current.id,revision:current.revision});
    await refresh(c.id);notice('Revised proposal ready. Previous reviews are preserved; review this revision again.');
  },'Preparing a revision from your correction…');
  for(const action of ['accept','reject','consistency'])$(action).onclick=()=>run(async()=>{
    const c=await api('/api/decision',{case_id:current.id,revision:current.revision,proposal_sha256:current.proposal_sha256,reviewer:$('author').value,action,meaning_reviewed:$('meaning-reviewed').checked,reviewed_sources:[...doc.querySelectorAll('[data-source]:checked')].map(n=>n.dataset.source),note:$('correction').value});
    await refresh(c.id);notice(action==='accept'?'Your acceptance is recorded for this rehearsal revision.':action==='reject'?'Rejection recorded. You can request a revised proposal.':'Your separate consistency review is recorded.');
  },'Recording your review…');
  $('cases').onchange=()=>renderCase(state.cases.find(c=>c.id===$('cases').value)||null);
  $('export').onclick=()=>run(async()=>{download(await api('/api/export',{}));notice('Session exported, including proposals, corrections and review events.');},'Preparing the session export…');
  const ready=run(async()=>{
    await refresh(null);for(const example of state.examples){const button=node('button',example);button.onclick=()=>{$('question').value=example;};$('examples').append(button);}
    notice('Ready. Enter your name and a fictional Luma question.');
  },'Connecting to the local rehearsal…');
  return {ready};
}
function defaultDownload(data){
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='prowl-invented-review.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
if(typeof document!=='undefined' && document.getElementById('propose'))startApp();
