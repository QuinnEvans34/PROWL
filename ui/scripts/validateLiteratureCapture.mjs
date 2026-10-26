// Offline adapter to the exact UI validators. No Vite app plugins, listener or model calls.
import { build } from 'vite'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'
import net from 'node:net'

net.Server.prototype.listen = function () { throw Error('Listeners disabled for capture validation') }
net.Socket.prototype.connect = function () { throw Error('Network connections disabled for capture validation') }

try {
  let input = ''
  for await (const chunk of process.stdin) {
    input += chunk.toString('utf8')
    if (Buffer.byteLength(input) > 1024 * 1024) throw Error('Capture exceeds 1 MiB')
  }
  const capture = JSON.parse(input)
  if (!capture || Object.keys(capture).sort().join(',') !== 'request,response') throw Error('Invalid capture envelope')
  const { request, response } = capture
  if (!request || Object.keys(request).sort().join(',') !== 'question,request_id'
      || typeof request.request_id !== 'string' || !request.request_id || request.request_id.length > 128
      || typeof request.question !== 'string' || !request.question.trim() || request.question.length > 500) throw Error('Invalid captured request')
  globalThis.fetch = () => { throw Error('Network is disabled for capture validation') }
  const built = await build({ configFile: false, envFile: false,
    root: fileURLToPath(new URL('../', import.meta.url)), logLevel: 'silent',
    build: { write: false, minify: false,
      lib: { entry: fileURLToPath(new URL('./literatureCaptureContract.js', import.meta.url)), formats: ['es'] },
    },
  })
  const result = Array.isArray(built) ? built[0] : built
  const entry = result.output.find(o => o.type === 'chunk' && o.isEntry)
  if (!entry || entry.imports.length || entry.dynamicImports.length) throw Error('Validator bundle must be self-contained')
  const { validateAnswer } = await import('data:text/javascript;base64,' + Buffer.from(entry.code).toString('base64'))
  validateAnswer(response, request)
  const evidence = response.evidence
  if (new Set(evidence.map(e => e.rank)).size !== evidence.length
      || new Set(evidence.map(e => e.record.passage.passage_id)).size !== evidence.length) throw Error('Duplicate evidence identity')
  process.stdout.write(JSON.stringify({ validation: 'existing-ui-response-and-citation-contract',
    semantic_support_reassessed: false, source_canonicality_rechecked: false,
    request_id: request.request_id, question_sha256: createHash('sha256').update(request.question).digest('hex'),
    response_schema: response.schema_version, state: response.state, generation: response.generation,
    answer_status: response.answer?.status ?? null, evidence_count: evidence.length,
    citation_count: (response.answer?.claims ?? []).reduce((n,c) => n + c.citations.length, 0),
  }) + '\n')
} catch (error) {
  process.stderr.write(`Capture rejected: ${error.message}\n`)
  process.exitCode = 1
}
