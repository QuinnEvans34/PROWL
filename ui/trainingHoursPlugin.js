import { spawn } from 'node:child_process'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
const repo=fileURLToPath(new URL('../',import.meta.url))
const snapshot=fileURLToPath(new URL('../configs/training-hours/recorded-hours-v1.json',import.meta.url))
const config=fileURLToPath(new URL('../outputs/prowl/training-hours/source-config.json',import.meta.url))
export function trainingHoursPlugin(){
 let cached=null,pending=null,checked=0
 function fallback(){return {...JSON.parse(readFileSync(snapshot,'utf8')),refresh_state:'saved_snapshot'}}
 async function refresh(){
  if(pending)return pending
  if(cached && Date.now()-checked<60000)return cached
  pending=new Promise(resolve=>{
   const selected=process.env.PROWL_TRAINING_HOURS_CONFIG || config
   if(!existsSync(selected)){resolve({...fallback(),refresh_note:'Local accounting sources are not configured. Showing the saved snapshot.'});return}
   let done=false
   const child=spawn(repo+'.venv312/bin/python',[repo+'scripts/collect_training_hours.py','--config',selected],
    {cwd:repo,stdio:['ignore','pipe','ignore'],env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}})
   let out=''
   const finish=value=>{if(done)return;done=true;clearTimeout(timer);resolve(value)}
   const stale=()=>({...cached || fallback(),refresh_state:'saved_snapshot',refresh_note:'Some accounting sources are unavailable. Retaining the last verified snapshot.'})
   const timer=setTimeout(()=>{child.kill('SIGTERM');finish(stale())},10000)
   child.stdout.on('data',chunk=>{out+=chunk;if(out.length>512*1024){child.kill('SIGTERM');finish(stale())}})
   child.on('error',()=>finish(stale()))
   child.on('close',code=>{
    try{const d=JSON.parse(out);if(code!==0 || d.schema!=='prowl-combined-training-hours-v1')throw Error();finish({...d,refresh_state:'local_read'})}
    catch{finish(stale())}
   })
  }).then(value=>{cached=value;checked=Date.now();return value}).finally(()=>{pending=null})
  return pending
 }
 return {name:'readonly-training-hours',configureServer(server){
  server.middlewares.use('/training-hours',async(req,res,next)=>{
   if(!['/','', '/?refresh=1'].includes(req.url) || !['GET','HEAD'].includes(req.method)){res.statusCode=404;res.end();return}
   try{
    const value=await refresh();const body=JSON.stringify(value)
    res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff')
    res.end(req.method==='HEAD'?'':body)
   }catch{res.statusCode=503;res.end('Accounting snapshot unavailable')}
  })
 }}
}
