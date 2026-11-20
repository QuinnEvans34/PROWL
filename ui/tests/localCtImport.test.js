// @vitest-environment node
import { expect, it, vi } from 'vitest'
import { NIFTI1 } from 'nifti-reader-js'
import { gzipSync } from 'node:zlib'
import { prepareLocalCt } from '../src/lib/localCtImport.js'

function syntheticVolume({ units = 2, shape = [3, 3, 4, 5, 1, 1, 1, 1], pixel = index => index - 10 } = {}) {
  const header = new NIFTI1()
  Object.assign(header, {
    magic: 'n+1', littleEndian: true, datatypeCode: 16, numBitsPerVoxel: 32,
    vox_offset: 352, scl_slope: 2, scl_inter: -20, sform_code: 1, xyzt_units: units,
    dims: shape, affine: [[0, -2, 0, 1], [1, 0, 0, -5], [0, 0, 3, 10], [0, 0, 0, 1]],
  })
  const bytes = new Uint8Array(352 + 60 * 4)
  bytes.set(new Uint8Array(header.toArrayBuffer()))
  const into = new DataView(bytes.buffer)
  for (let index = 0; index < 60; index++) into.setFloat32(352 + index * 4, pixel(index), true)
  return bytes
}

it.each([false, true])('opens a synthetic NIfTI locally with native geometry and no prediction, gzip=%s', async gzip => {
  const contents = syntheticVolume()
  const payload = gzip ? gzipSync(contents) : contents
  const file = new File([payload], gzip ? 'private.nii.gz' : 'private.nii')
  const create = vi.spyOn(URL, 'createObjectURL')
  const revoke = vi.spyOn(URL, 'revokeObjectURL')
  const open = await prepareLocalCt(file)
  try {
    expect(open.caseData).toMatchObject({ files: { ct: 'ct.nii.gz' }, spacing_mm: [1, 2, 3] })
    expect(open.caseData.files.pred).toBeUndefined()
    expect(open.caseData.case_id).toMatch(/^Local_CT_[a-f0-9]{32}$/)
    expect(JSON.stringify(open)).not.toContain('private')
    expect(open.geometry).toMatchObject({ shape: [3, 4, 5], units: 'mm' })
    expect(open.ctRange).toEqual([-38, 76])
    expect(open.ctSha256).toMatch(/^[a-f0-9]{64}$/)
    expect(open.imageSource.calibratedHu).toBe(false)
    expect(Buffer.from(await create.mock.calls[0][0].arrayBuffer())).toEqual(Buffer.from(payload))
    expect(create).toHaveBeenCalledOnce()
  } finally {
    open.release()
    expect(revoke).toHaveBeenCalledWith(open.assetUrls.ct)
    create.mockRestore()
    revoke.mockRestore()
  }
})

it('refuses invalid geometry and incomplete or unsupported files', async () => {
  await expect(prepareLocalCt(new File(['dicom'], 'file.dcm'))).rejects.toThrow(/ending/)
  await expect(prepareLocalCt(new File([gzipSync(gzipSync(syntheticVolume()))], 'double.nii.gz'))).rejects.toThrow(/complete NIfTI/)
  await expect(prepareLocalCt(new File([syntheticVolume({ units: 0 })], 'unknown.nii'))).rejects.toThrow(/millimeter/)
  await expect(prepareLocalCt(new File([syntheticVolume({ shape: [4, 3, 4, 5, 2, 1, 1, 1] })], 'series.nii'))).rejects.toThrow(/three-dimensional/)
  await expect(prepareLocalCt(new File([syntheticVolume().slice(0, -20)], 'truncated.nii'))).rejects.toThrow(/incomplete/)
  await expect(prepareLocalCt(new File([syntheticVolume({ pixel: () => NaN })], 'nan.nii'))).rejects.toThrow(/invalid voxel/)
})

it('releases the selection promptly when the consumer aborts', async () => {
  const control = new AbortController()
  const create = vi.spyOn(URL, 'createObjectURL')
  try {
    const opened = prepareLocalCt(new File([syntheticVolume()], 'scan.nii'), control.signal)
    control.abort()
    await expect(opened).rejects.toMatchObject({ name: 'AbortError' })
    expect(create).not.toHaveBeenCalled()
  } finally { create.mockRestore() }
})
