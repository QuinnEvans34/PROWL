import { isNIFTI, NIFTI2, readHeader } from 'nifti-reader-js'
import { boundedStream, sha } from './scanMeasurements.js'

const INPUT_LIMIT = 64 * 1024 ** 2
const DECODED_LIMIT = 128 * 1024 ** 2
const VOXEL_LIMIT = 32_000_000
const SCALAR_TYPES = {
  2: ['getUint8', 1], 4: ['getInt16', 2], 8: ['getInt32', 4],
  16: ['getFloat32', 4], 64: ['getFloat64', 8], 256: ['getInt8', 1],
  512: ['getUint16', 2], 768: ['getUint32', 4],
}

function initialWindow(header, data, count) {
  const type = SCALAR_TYPES[header.datatypeCode]
  if (!type || header.numBitsPerVoxel !== type[1] * 8)
    throw new Error('This NIfTI uses an unsupported pixel type. Select a scalar CT volume.')
  const [method, stride] = type
  if (!Number.isSafeInteger(header.vox_offset) || header.vox_offset < (header instanceof NIFTI2 ? 544 : 352)
    || header.vox_offset + count * stride > data.byteLength)
    throw new Error('This NIfTI voxel payload is incomplete.')
  const raw = new DataView(data)
  const read = raw[method].bind(raw)
  // A zero slope is NIfTI's identity mapping. Parsed undefined scaling is
  // also identity. The transform is unrelated to whether the values are HU.
  const unscaled = header.scl_slope === 0 || Number.isNaN(header.scl_slope)
  const slope = unscaled ? 1 : header.scl_slope
  const intercept = unscaled ? 0 : header.scl_inter
  const samples = []
  const interval = Math.max(1, Math.floor(count / 2048))
  let min = Infinity, max = -Infinity
  for (let index = 0; index < count; index++) {
    const pixel = read(header.vox_offset + index * stride, header.littleEndian)
    const value = pixel * slope + intercept
    if (!Number.isFinite(Math.fround(value))) throw new Error('This NIfTI contains invalid voxel intensities.')
    min = Math.min(min, value)
    max = Math.max(max, value)
    if (index % interval === 0) samples.push(value)
  }
  samples.sort((a, b) => a - b)
  const low = samples[Math.floor((samples.length - 1) * .02)]
  const high = samples[Math.ceil((samples.length - 1) * .98)]
  if (low < high) return [low, high]
  if (min < max) return [min, max]
  const margin = Math.max(1, Math.abs(min) * .01)
  return [min - margin, max + margin]
}

function volumeGeometry(header) {
  const { dims, affine, xyzt_units: units } = header
  const shape = dims.slice(1, 4)
  if (dims[0] !== 3 || shape.some(length => !Number.isSafeInteger(length) || length < 2)
    || dims.slice(4).some(length => length > 1))
    throw new Error('Choose one three-dimensional CT volume.')
  if (shape.reduce((a, b) => a * b, 1) > VOXEL_LIMIT)
    throw new Error('This NIfTI exceeds the local review size budget.')
  if ((units & 7) !== 2) throw new Error('The CT header must declare millimeter spatial units.')
  const [[a, b, c], [d, e, f], [g, h, i], lastRow] = affine
  const determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
  if (!(header.sform_code > 0 || header.qform_code > 0)
    || !affine.every(row => row.every(Number.isFinite))
    || lastRow.some((value, axis) => Math.abs(value - (axis === 3 ? 1 : 0)) > 1e-6)
    || !Number.isFinite(determinant) || Math.abs(determinant) < 1e-9)
    throw new Error('The CT requires a valid spatial transform.')
  return { shape, affine, units: 'mm' }
}

/** Inspect and open one local, de-identified file without a network request. */
export async function prepareLocalCt(file, signal) {
  if (!file || !/\.nii(?:\.gz)?$/i.test(file.name))
    throw new Error('Choose one NIfTI CT file ending in .nii or .nii.gz.')
  if (!Number.isSafeInteger(file.size) || file.size <= 0 || file.size > INPUT_LIMIT)
    throw new Error('Choose a nonempty NIfTI file up to 64 MB.')
  if (typeof file.stream !== 'function') throw new Error('This browser could not open the local file.')
  signal?.throwIfAborted()
  const raw = await boundedStream(file.stream(), signal, INPUT_LIMIT)
  const prefix = new Uint8Array(raw, 0, Math.min(2, raw.byteLength))
  let data = raw
  try {
    if (prefix[0] === 31 && prefix[1] === 139)
      data = await boundedStream(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip')), signal, DECODED_LIMIT)
  } catch (error) {
    signal?.throwIfAborted()
    if (/exceeds/i.test(error.message)) throw new Error('This NIfTI exceeds the local review size budget.')
    throw new Error('This gzip file could not be decoded.')
  }
  // Reject other formats including nested gzip before the NIfTI reader can
  // try to decompress a second time internally without our byte limit.
  let header
  try { if (isNIFTI(data)) header = readHeader(data) } catch { /* invalid file header */ }
  if (!header) throw new Error('This file must contain one complete NIfTI volume.')
  const geometry = volumeGeometry(header)
  const { shape, affine } = geometry
  const ctRange = initialWindow(header, data, shape.reduce((a, b) => a * b, 1))
  const ctSha256 = await sha(raw)
  signal?.throwIfAborted()
  const ct = URL.createObjectURL(new Blob([raw], { type: 'application/octet-stream' }))
  return {
    caseData: {
      case_id: `Local_CT_${crypto.randomUUID().replaceAll('-', '')}`,
      files: { ct: 'ct.nii.gz' },
      spacing_mm: [0, 1, 2].map(axis => Math.hypot(affine[0][axis], affine[1][axis], affine[2][axis])),
    },
    assetUrls: { ct },
    geometry,
    ctRange,
    ctSha256,
    imageSource: { kind: 'source', series: 'Locally opened NIfTI', calibratedHu: false },
    release: () => URL.revokeObjectURL(ct),
  }
}
