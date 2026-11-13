import { readFileSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { acceptTrainingProgress, MAX_PROGRESS_BYTES } from './src/lib/trainingProgress.js'

const retained = fileURLToPath(new URL('../configs/training-progress/current.json', import.meta.url))
function readSnapshot(path) {
  if (statSync(path).size > MAX_PROGRESS_BYTES) throw new Error('Export too large')
  const data = readFileSync(path, 'utf8')
  if (Buffer.byteLength(data) > MAX_PROGRESS_BYTES) throw new Error('Export too large')
  return JSON.parse(data)
}

export function trainingProgressPlugin({ retainedPath = retained } = {}) {
  let last = null
  let readState = 'retained_snapshot'
  return { name: 'readonly-training-progress', configureServer(server) {
    server.middlewares.use('/training-progress', (req, res) => {
      if (!['/', ''].includes(req.url) || !['GET', 'HEAD'].includes(req.method)) { res.statusCode = 404; res.end(); return }
      try {
        let note = 'Saved metadata export; this page does not connect to Lenovo.'
        try {
          last = acceptTrainingProgress(last, readSnapshot(retainedPath))
          readState = 'retained_snapshot'
        } catch {
          note = 'The retained export is unavailable or inconsistent. Keeping the last verified results.'
        }
        const selected = process.env.PROWL_TRAINING_PROGRESS_FILE
        if (selected) {
          try {
            last = acceptTrainingProgress(last, readSnapshot(selected))
            readState = 'local_snapshot'; note = 'Local export read successfully; host status is recorded at the observation time.'
          } catch { note = 'The configured export is unavailable or inconsistent. Keeping the last verified results.' }
        }
        if (!last) throw new Error('No verified training progress export')
        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Cache-Control', 'no-store')
        res.setHeader('X-Content-Type-Options', 'nosniff')
        res.end(req.method === 'HEAD' ? '' : JSON.stringify({ snapshot: last, read_state: readState, note }))
      } catch { res.statusCode = 503; res.end('Training progress unavailable') }
    })
  } }
}
