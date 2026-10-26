// General-literature snapshot only: never adds case identifiers or scan measurements.
export function serializeLiteratureCapture(request, response) {
  const capture = { request: { request_id: request.request_id, question: request.question }, response }
  const text = JSON.stringify(capture, null, 2) + '\n'
  if (new TextEncoder().encode(text).length > 1024 * 1024) throw new Error('This response is too large to export.')
  return text
}

export function downloadLiteratureCapture(text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'prowl-literature-capture.json'
  try {
    document.body.appendChild(link)
    link.click()
  } finally {
    link.remove()
    // Allow the browser to start the download before releasing its URL.
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}
