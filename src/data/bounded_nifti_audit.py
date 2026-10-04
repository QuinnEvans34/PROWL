"""Bounded whole-file NIfTI reading for qualification, not permission or model input."""
import gzip
import hashlib
import io
import math
import os
import nibabel as nib
import numpy as np
from scripts.diagnostics.localizer_content_verify import open_relative,signature


def decode_file(payload, *, expanded_cap, voxel_cap, tick=lambda:None):
    """Read to gzip EOF/CRC with a cap; reject header allocation claims before decoding."""
    with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
        header=stream.read(348)
        if len(header)!=348:raise ValueError('Truncated NIfTI header')
        h=nib.Nifti1Header.from_fileobj(io.BytesIO(header),check=True)
        shape=h.get_data_shape();dtype=h.get_data_dtype();offset=float(h['vox_offset'])
        if len(shape)!=3 or any(n<=0 for n in shape) or math.prod(shape)>voxel_cap or dtype.kind not in 'iuf' or dtype.itemsize>8:
            raise ValueError('Declared array cap/type')
        if not math.isfinite(offset) or offset!=int(offset) or not 352<=offset<=1024**2:
            raise ValueError('Invalid single-file voxel offset')
        expected=int(offset)+math.prod(shape)*dtype.itemsize
        if expected>expanded_cap:raise ValueError('Declared expanded cap')
        chunks=[header];used=len(header)
        while True:
            tick();part=stream.read(min(1024**2,expanded_cap-used+1))
            if not part:break
            used+=len(part)
            if used>expanded_cap:raise ValueError('Expanded byte cap')
            chunks.append(part)
    if used<expected:raise ValueError('Truncated voxel payload')
    raw=b''.join(chunks);tick();image=nib.Nifti1Image.from_bytes(raw)
    if image.shape!=shape or not np.isfinite(image.affine).all():raise ValueError('Invalid decoded geometry')
    return image,used


def read_file(root,row,*,compressed_cap,expanded_cap,voxel_cap,tick=lambda:None):
    if row['protected_role'] not in ('train','validation') or row['kind'] not in ('ct','pancreas'):
        raise ValueError('Unsupported role/kind')
    if not 0<row['bytes']<=compressed_cap:raise ValueError('Compressed byte cap')
    expected=dict(row['observation'],bytes=row['bytes']);fd=open_relative(root,row['uri'])
    try:
        if signature(os.fstat(fd))!=expected:raise ValueError('Changed inventory identity')
        parts=[];used=0;digest=hashlib.sha256()
        while used<row['bytes']:
            tick();part=os.read(fd,min(1024**2,row['bytes']-used))
            if not part:raise ValueError('Truncated source')
            parts.append(part);digest.update(part);used+=len(part)
        if signature(os.fstat(fd))!=expected:raise ValueError('Source mutated')
        other=open_relative(root,row['uri'])
        try:
            if signature(os.fstat(other))!=expected:raise ValueError('Source replaced')
        finally:os.close(other)
    finally:os.close(fd)
    image,expanded=decode_file(b''.join(parts),expanded_cap=expanded_cap,voxel_cap=voxel_cap,tick=tick)
    return image,dict(content_sha256=digest.hexdigest(),compressed_bytes=used,expanded_bytes=expanded,gzip_eof_crc_verified=True)
