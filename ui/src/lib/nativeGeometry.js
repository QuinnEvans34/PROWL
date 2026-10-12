export function verifyNativeVolumes(volumes, geometry) {
  if (volumes.length !== 2) throw new Error('CT or prediction failed to load.')
  for (const volume of volumes) {
    const h = volume?.hdr
    if (!h || geometry.shape.some((n, i) => Number(h.dims[i + 1]) !== n)
      || (Number(h.xyzt_units) & 7) !== 2
      || geometry.affine.some((row, i) => row.some((n, j) => !Number.isFinite(h.affine?.[i]?.[j]) || Math.abs(h.affine[i][j] - n) > 1e-4))) {
      throw new Error('Native CT/prediction geometry mismatch. Overlay refused.')
    }
  }
}
