import { useEffect, useState } from 'react'

const LOADING = { status: 'loading' }
const UNAVAILABLE = { status: 'unavailable', reason: 'The prediction mask is unavailable.' }

export function usePredictionSurfaces(url, bytes, geometry) {
  const [surface, setSurface] = useState(null)
  useEffect(() => {
    if (!url) return undefined
    let worker
    let active = true
    const mesh = {}
    const publish = result => { if (active) setSurface({ url, ...result }) }
    const unavailable = reason => publish({ status: 'unavailable', reason })
    try {
      worker = new Worker(new URL('./predictionSurfaceWorker.js', import.meta.url), { type: 'module' })
      worker.onmessage = ({ data }) => {
        worker.terminate()
        if (!active) return
        if (data.error) { unavailable(data.error); return }
        for (const [anatomy, buffer] of Object.entries(data.surfaces || {})) {
          mesh[anatomy] = URL.createObjectURL(new Blob([buffer], { type: 'application/octet-stream' }))
        }
        if (!Object.keys(mesh).length) { unavailable('The prediction has no 3D outline.'); return }
        publish({ status: 'ready', mesh })
      }
      worker.onerror = () => {
        worker.terminate()
        unavailable('The verified 3D outline could not be prepared.')
      }
      worker.postMessage({ url, bytes, geometry })
    } catch {
      unavailable('This browser could not prepare the verified 3D outline.')
    }
    return () => {
      active = false
      worker?.terminate()
      Object.values(mesh).forEach(meshUrl => URL.revokeObjectURL(meshUrl))
    }
  }, [url, bytes, geometry])

  if (!url) return UNAVAILABLE
  return surface?.url === url ? surface : LOADING
}
