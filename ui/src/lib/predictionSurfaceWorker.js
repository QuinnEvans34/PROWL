import { verifyNativeVolumes } from './nativeGeometry.js'
import { buildPredictionSurfaces } from './predictionSurfaces.js'
import { boundedStream, decodeMeasurementFile, labelsFrom } from './scanMeasurements.js'

self.onmessage = async ({ data: { url, bytes, geometry } }) => {
  try {
    const response = await fetch(url)
    if (!response.ok || !response.body) throw new Error('The verified prediction mask could not be read.')
    const raw = await boundedStream(response.body, null, bytes)
    if (raw.byteLength !== bytes) throw new Error('The verified prediction mask is incomplete.')
    const decoded = await decodeMeasurementFile(raw, null, { maxVoxels: 32_000_000, decodedLimit: 128 * 1024 * 1024 })
    const volume = { hdr: decoded.header }
    verifyNativeVolumes([volume, volume], geometry)
    const surfaces = buildPredictionSurfaces(labelsFrom(decoded), geometry)
    self.postMessage({ surfaces }, Object.values(surfaces))
  } catch (error) {
    self.postMessage({ error: error.message })
  }
}
