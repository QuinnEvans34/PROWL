// Isolated transport test: retain the production review proxy options and headers.
import { createServer } from 'vite'
import config from '../vite.config.js'
const target = process.argv[2]
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(target)) throw new Error('Loopback fixture required')
const original = config.server.proxy['/review-records']
const proxy = typeof original === 'string' ? target : { ...original, target }
const server = await createServer({
  configFile: false, root: import.meta.dirname, publicDir: false,
  logLevel: 'error', appType: 'custom',
  server: { host: '127.0.0.1', port: 0, strictPort: true, open: false,
    proxy: { '/review-records': proxy } },
})
await server.listen()
console.log(JSON.stringify({ port: server.httpServer.address().port }))
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, async () => {
  await server.close()
  process.exit(0)
})
