import { createReadStream, realpathSync, statSync } from 'node:fs'
import { resolve, sep } from 'node:path'
// Development only: explicitly selected private files, never copied into a build.
export function savedPredictionPlugin() {
  return { name: 'private-saved-prediction', configureServer(server) {
    server.middlewares.use('/saved-prediction', (req, res, next) => {
      const directory = process.env.PROWL_SAVED_PREDICTION_DIR
      if (!directory) { res.statusCode = 404; res.end('No saved package configured'); return }
      const name = req.url?.split('?')[0]
      if (!['/manifest.json', '/ct.nii.gz', '/prediction.nii.gz'].includes(name) || !['GET', 'HEAD'].includes(req.method)) { res.statusCode = 404; res.end(); return }
      try {
        const root = realpathSync(directory)
        const path = realpathSync(resolve(root, name.slice(1)))
        if (!path.startsWith(root + sep)) throw new Error('Outside package')
        const stat = statSync(path)
        if (!stat.isFile()) throw new Error('Not a file')
        res.setHeader('Content-Type', name.endsWith('.json') ? 'application/json' : 'application/gzip')
        res.setHeader('Cache-Control', 'no-store')
        res.setHeader('Content-Length', stat.size)
        if (req.method === 'HEAD') { res.end(); return }
        createReadStream(path).on('error', () => res.destroy()).pipe(res)
      } catch { res.statusCode = 404; res.end('Saved package file unavailable') }
    })
  } }
}
