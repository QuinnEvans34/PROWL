const PLANES = {
  axial: { type: 0, axes: [0, 1, 2] },
  coronal: { type: 1, axes: [0, 2, 1] },
  sagittal: { type: 2, axes: [1, 2, 0] },
}

const cachedSlice = new WeakMap()
const near = (a, b) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) < 1e-4

function sameGrid(ct, mask) {
  if (!ct?.matRAS || !mask?.matRAS || ct.matRAS.length !== 16 || mask.matRAS.length !== 16
    || ct.dimsRAS?.length !== 4 || mask.dimsRAS?.length !== 4 || !mask.img) return false
  return ct.matRAS.every((value, index) => near(value, mask.matRAS[index]))
    && ct.dimsRAS.slice(1).every((value, index) => value > 0 && Number.isSafeInteger(value) && value === mask.dimsRAS[index + 1])
}

function boundaryRuns(across, rows, point, horizontal, paths) {
  // Each line separates neighboring voxel rows. Merge runs to keep the SVG
  // compact, including where a lesion is nested inside the pancreas.
  for (let line = 0; line <= rows; line += 1) {
    let previous = 0
    let pancreasStart = 0
    let lesionStart = 0
    const segment = (start, end) => horizontal ? `M${start} ${line}H${end}` : `M${line} ${start}V${end}`
    for (let at = 0; at <= across; at += 1) {
      const boundary = at === across ? 0 : point(at, line - 1) ^ point(at, line)
      const changed = previous ^ boundary
      if (changed & 1) {
        if (previous & 1) paths.pancreas.push(segment(pancreasStart, at))
        pancreasStart = at
      }
      if (changed & 2) {
        if (previous & 2) paths.lesion.push(segment(lesionStart, at))
        lesionStart = at
      }
      previous = boundary
    }
  }
}

function contourSlice(mask, plane, [horizontal, vertical, depth], index, width, height) {
  const cached = cachedSlice.get(mask)
  if (cached?.plane === plane && cached.index === index) return cached.paths

  // Read the displayed RAS volume using NiiVue's orientation strides.
  // A flipped or permuted native volume needs no full-volume copy.
  const strides = mask.img2RASstep
  const start = mask.img2RASstart
  if (strides?.length !== 3 || !strides.every(Number.isSafeInteger)
    || start?.length !== 3 || !start.every(Number.isSafeInteger)) return null
  const offset = start[0] + start[1] + start[2] + index * strides[depth]
  const du = strides[horizontal]
  const dv = strides[vertical]
  const offsets = [offset, offset + (width - 1) * du, offset + (height - 1) * dv, offset + (width - 1) * du + (height - 1) * dv]
  if (Math.min(...offsets) < 0 || Math.max(...offsets) >= mask.img.length) return null

  const point = (x, y) => {
    if (x < 0 || x >= width || y < 0 || y >= height) return 0
    const label = mask.img[offset + x * du + y * dv]
    // Lesion-labeled voxels are part of the predicted whole pancreas.
    return label === 2 ? 3 : label === 1 ? 1 : 0
  }
  const segments = { pancreas: [], lesion: [] }
  boundaryRuns(width, height, point, true, segments)
  boundaryRuns(height, width, (y, x) => point(x, y), false, segments)
  const paths = { pancreas: segments.pancreas.join(''), lesion: segments.lesion.join('') }
  cachedSlice.set(mask, { plane, index, paths })
  return paths
}

function screenProjection(nv, tile, [horizontal, vertical, depth], width, height) {
  const [left, top, tileWidth, tileHeight] = tile.leftTopWidthHeight || []
  const [mmX, mmY] = tile.leftTopMM || []
  const [fovX, fovY] = tile.fovMM || []
  const canvas = nv.canvas
  if (![left, top, tileWidth, tileHeight, mmX, mmY, fovX, fovY].every(Number.isFinite)
    || !tileWidth || tileHeight <= 0 || !fovX || !fovY || !canvas?.width || !canvas?.height
    || !canvas.clientWidth || !canvas.clientHeight) return null
  const scaleX = canvas.clientWidth / canvas.width
  const scaleY = canvas.clientHeight / canvas.height

  const at = (u, v) => {
    const frac = [0, 0, 0]
    frac[horizontal] = u
    frac[vertical] = v
    frac[depth] = tile.sliceFrac
    return nv.frac2mm(frac)
  }
  const origin = at(0, 0)
  const right = at(1, 0)
  const up = at(0, 1)
  if (![origin, right, up].every(point => point?.length >= 3 && [0, 1, 2].every(i => Number.isFinite(point[i])))
    || !near(origin[depth], right[depth]) || !near(origin[depth], up[depth])) return null

  const pixel = mm => [
    (left + tileWidth * (mm[horizontal] - mmX) / fovX) * scaleX,
    (top + tileHeight * (1 - (mm[vertical] - mmY) / fovY)) * scaleY,
  ]
  const [x, y] = pixel(origin)
  const [rightX, rightY] = pixel(right)
  const [upX, upY] = pixel(up)
  return {
    transform: `matrix(${(rightX - x) / width} ${(rightY - y) / width} ${(upX - x) / height} ${(upY - y) / height} ${x} ${y})`,
    bounds: { x: Math.min(left, left + tileWidth) * scaleX, y: top * scaleY,
      width: Math.abs(tileWidth) * scaleX, height: tileHeight * scaleY },
  }
}

function contourTile(nv, mask, plane) {
  const info = PLANES[plane]
  if (!info || !sameGrid(nv?.volumes?.[0], mask)) return null
  return nv.screenSlices?.find(slice => slice.axCorSag === info.type
    && Number.isFinite(slice.sliceFrac) && slice.sliceFrac >= 0 && slice.sliceFrac <= 1) ?? null
}

export function hasContourTile(nv, mask, plane) {
  return Boolean(contourTile(nv, mask, plane))
}

export function projectPredictedContours(nv, mask, plane) {
  const tile = contourTile(nv, mask, plane)
  const info = PLANES[plane]
  if (!tile) return null
  const [width, height, slices] = info.axes.map(axis => mask.dimsRAS[axis + 1])
  const index = Math.min(slices - 1, Math.floor(tile.sliceFrac * slices))
  const screen = screenProjection(nv, tile, info.axes, width, height)
  const paths = screen && contourSlice(mask, plane, info.axes, index, width, height)
  return paths ? { paths, ...screen } : null
}
