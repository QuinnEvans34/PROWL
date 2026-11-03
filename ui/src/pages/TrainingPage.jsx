import { useEffect, useState } from 'react'
import snapshot from '../../../configs/training-hours/recorded-hours-v1.json'
import './TrainingPage.css'
const hours=n=>Number(n/3600).toLocaleString(undefined,{minimumFractionDigits:1,maximumFractionDigits:1})
const stamp=value=>value?new Date(value).toLocaleString(): 'Not recorded'
export default function TrainingPage(){
 const [data,setData]=useState({...snapshot,refresh_state:'saved_snapshot'})
 const [loading,setLoading]=useState(false),[error,setError]=useState('')
 useEffect(()=>{
  const controller=new AbortController()
  async function load(){
   setLoading(true)
   try{
    const response=await fetch('/training-hours',{signal:controller.signal,cache:'no-store'})
    if(!response.ok)throw Error()
    const next=await response.json()
    if(next.schema!=='prowl-combined-training-hours-v1')throw Error()
    setData(next);setError('')
   }catch(e){if(e.name!=='AbortError')setError('Live accounting is unavailable. The saved snapshot remains visible.')}
   finally{if(!controller.signal.aborted)setLoading(false)}
  }
  load();const timer=setInterval(load,60000)
  return()=>{controller.abort();clearInterval(timer)}
 },[])
 const kd=data.entries.filter(e=>e.period==='KD comparison')
 const kdControl=kd.filter(e=>e.arm==='control').reduce((a,e)=>a+e.seconds,0)
 const kdTreatment=kd.filter(e=>e.arm==='treatment').reduce((a,e)=>a+e.seconds,0)
 const t=data.totals
 return <main className="pw-page pw-hours">
  <header><p className="pw-eyebrow">Experiment accounting</p><h1 className="pw-display">Training time</h1>
   <p className="pw-lede">Recorded sessions across the Mac and Lenovo, including the earlier MLflow history.</p></header>
  <section className="pw-hours__total" aria-label="Recorded training sessions"><span>Recorded training sessions</span>
   <strong>{hours(t.recorded_training_seconds)} <small>hours</small></strong>
   <p>Includes {hours(t.legacy_estimated_seconds)} hours estimated from historical MLflow timestamps.</p>
   <p>Session time includes in-run validation, checkpoints and I/O. It does not measure GPU-busy time or your personal working hours.</p>
  </section>
  <div className="pw-hours__cards">
   {Object.entries(t.machines).map(([machine,v])=><section key={machine}><h2>{machine}</h2><strong>{hours(v.training_seconds+v.legacy_estimated_seconds)} h</strong>
    <p>{hours(v.training_seconds)} h from recorded elapsed counters</p>{v.legacy_estimated_seconds>0 && <p>{hours(v.legacy_estimated_seconds)} h from historical timestamp estimates, already included above</p>}</section>)}
   <section><h2>Teacher targets</h2><strong>{hours(t.teacher_seconds)} h</strong><p>Model inference to prepare training targets. Shown separately from weight training.</p></section>
  </div>
  <section className="pw-hours__notes"><h2>Mac KD comparison</h2><p><strong>{hours(kdControl+kdTreatment)} hours</strong> across the matched control ({hours(kdControl)} h) and distillation attempts ({hours(kdTreatment)} h). Already included in the Mac total.</p></section>
  <section className="pw-hours__notes"><h2>What is counted</h2><p>{data.policy}</p>
   <p>Each execution is counted once. MLflow copies of the same execution add no extra time. Paused periods between attempts are excluded; work repeated after recovery still counts as real compute.</p>
   <p>The early MLflow runs belong to the Mac total, rather than a third machine. This is the reconciled record we could verify, not a guarantee that every early experiment was retained.</p>
   <p>Training plus measured teacher-target work: <strong>{hours(t.recorded_model_work_seconds)} hours</strong>, including the historical estimates above.</p>
  </section>
  <section className="pw-hours__notes"><h2>Source freshness</h2>
   <p role="status">{loading?'Reading local counters…':data.refresh_state==='local_read'?'Local counters checked. Lenovo uses its verified export.':'Showing a retained snapshot.'}</p>
   {(error || data.refresh_note) && <p role="note">{error || data.refresh_note}</p>}
   <p>Snapshot generated: {stamp(data.generated_at)}. No time is added just because the page is open.</p>
   <ul>{data.sources.map(s=><li key={s.name}>{s.name}: {stamp(s.as_of_utc)} · {s.records} records</li>)}</ul>
  </section>
  <details className="pw-hours__notes"><summary>Accounting limits and excluded work</summary><ul>{data.issues.map(s=><li key={s}>{s}</li>)}</ul><p>Excluded: {data.excluded.join('; ')}.</p></details>
  <details className="pw-hours__notes"><summary>Per-execution breakdown ({data.entries.length})</summary>
   <div className="pw-hours__table"><table><thead><tr><th>Machine / period</th><th>Execution</th><th>Hours</th><th>Source</th></tr></thead><tbody>
    {data.entries.map(e=><tr key={e.execution_id}><td>{e.machine}<br/>{e.period}</td><td>{e.title}<br/><small>{e.execution_id}</small></td><td>{hours(e.seconds)}</td><td>{e.basis}</td></tr>)}
   </tbody></table></div>
  </details>
 </main>
}
