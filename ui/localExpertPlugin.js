import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { fileURLToPath } from 'node:url'
const exec = promisify(execFile)
const root = fileURLToPath(new URL('..', import.meta.url))
export function localRequest(req) {
  return ['127.0.0.1:5180', 'localhost:5180'].includes(req.headers.host)
    && (!req.headers.origin || ['http://127.0.0.1:5180', 'http://localhost:5180'].includes(req.headers.origin))
    && req.headers['sec-fetch-site'] !== 'cross-site'
}
export function localExpertPlugin() {
  let preparing = null
  const run = async action => {
    const { stdout } = await exec(`${root}/.venv-retrieval/bin/python`,
      [`${root}/scripts/retrieval/prepare_local_expert.py`, action], { cwd: root, timeout: 240000, maxBuffer: 65536 })
    return JSON.parse(stdout)
  }
  return { name: 'local-expert-preparation', configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      const path = req.url?.split('?')[0]
      const lifecycle = ['/local-expert/status', '/local-expert/prepare'].includes(path)
      const answer = ['/literature-search/answer', '/literature-search/interpret'].includes(path)
      if (!lifecycle && !answer) return next()
      const reply = (code, data) => { res.statusCode = code; res.setHeader('Content-Type', 'application/json'); res.setHeader('Cache-Control', 'no-store'); res.end(JSON.stringify(data)) }
      if (!localRequest(req)) return reply(403, { error: 'Local access required.' })
      try {
        if (answer) {
          if ((await run('gpu')).gpu_busy) return reply(409, { error: 'Teacher is using the GPU. Find sources is available; pause the teacher before asking the model.' })
          return next()
        }
        if ((path.endsWith('/prepare') && req.method !== 'POST') || (path.endsWith('/status') && req.method !== 'GET')) return reply(405, { error: 'Method not allowed.' })
        if (path.endsWith('/status')) return reply(200, await run('status'))
        if (!preparing) preparing = run('prepare').finally(() => { preparing = null })
        reply(200, await preparing)
      } catch { reply(503, { error: 'Local preparation timed out or is unavailable. Check services before retrying.' }) }
    })
  } }
}
