// @vitest-environment node
import {it,expect,vi,afterEach} from 'vitest'
import {trainingHoursPlugin} from '../trainingHoursPlugin.js'
import snapshot from '../../configs/training-hours/recorded-hours-v1.json'
afterEach(()=>vi.unstubAllEnvs())
function middleware(){let h;trainingHoursPlugin().configureServer({middlewares:{use:(_,handler)=>{h=handler}}});return h}
async function call(h,url='/',method='GET'){
 let body='';const res={statusCode:200,setHeader:vi.fn(),end:v=>{body=v||''}}
 await h({url,method},res,vi.fn());return{status:res.statusCode,body}
}
it('keeps an identified retained snapshot when local source configuration is absent',async()=>{
 vi.stubEnv('PROWL_TRAINING_HOURS_CONFIG','/nonexistent/explicit-training-config.json')
 const r=await call(middleware());const d=JSON.parse(r.body)
 expect(r.status).toBe(200);expect(d.refresh_state).toBe('saved_snapshot')
 expect(d.totals.recorded_training_seconds).toBe(snapshot.totals.recorded_training_seconds)
 expect(d.generated_at).toBe(snapshot.generated_at)
})
it('does not accept request paths or methods as source configuration',async()=>{
 const h=middleware()
 expect((await call(h,'/../../etc/passwd')).status).toBe(404)
 expect((await call(h,'/','POST')).status).toBe(404)
})
