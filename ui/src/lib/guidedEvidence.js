import fixture from '../../../configs/evidence/guided-fixture-v1.json'

export const evidenceFixture = fixture
export const evidenceStates = {
  answered: 'Supported by the selected fixture',
  insufficient_evidence: 'Not enough evidence',
  out_of_scope: 'Outside PROWL’s scope',
}

// This adapter intentionally accepts only fixed question IDs, never patient context/free text.
export async function requestEvidence(request, signal) {
  const result = await fetch('/evidence-fixture/responses', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request), signal,
  })
  if (!result.ok) throw new Error('Evidence response unavailable')
  return validateEvidence(await result.json(), request)
}

export function validateEvidence(response, request) {
  const question = fixture.questions.find(q => q.id === request.question_id)
  const passages = question?.passage_ids.map(id => fixture.passages.find(p => p.id === id))
  const valid = question && response?.schema_version === 'prowl-guided-fixture-response-v1'
    && response.response_id === request.request_id
    && response.request?.request_id === request.request_id
    && response.request?.question_id === request.question_id
    && response.question === question.label && response.state === question.state
    && response.message === question.message
    && response.provenance?.corpus === fixture.version
    && response.provenance?.adapter === 'fixed-extractive-v1'
    && response.provenance?.model === null && response.provenance?.index === null
    && /^[a-f0-9]{64}$/.test(response.content_sha256)
    && response.claims?.length === passages.length && response.citations?.length === passages.length
    && passages.every((p, i) => response.claims[i].text === p.text
      && response.claims[i].passage_id === p.id
      && Object.entries(p).every(([key, value]) => response.citations[i][key] === value))
  if (!valid) throw new Error('Fixture response validation failed')
  return response
}
