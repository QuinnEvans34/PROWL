"""Discrete native-grid export for the bounded inference pilot; no reference scoring."""
import os
from pathlib import Path
import time
import nibabel as nib
import numpy as np
import torch
from src.data.localizer_preprocessing_v4 import restore_to_source
from src.data.manifest_records import digest
from src.data.source_inventory_records import require


def verify_export(path,record,*,expected_sha256,expected_foreground):
    path=Path(path)
    require(path.is_file() and not path.is_symlink(),'Missing/unsafe export')
    require(digest(path.read_bytes())==expected_sha256,'Export bytes changed')
    image=nib.load(path)
    require(list(image.shape)==record['source_shape'] and image.get_data_dtype()==np.dtype('uint8'),
            'Native shape/dtype differs')
    # NIfTI1 sform stores float32: tolerate only that representation rounding.
    require(np.array_equal(image.affine,np.asarray(record['source_affine'],dtype=np.float32).astype(float)),
            'Native affine differs')
    require(image.header.get_xyzt_units()[0]=='mm','Export physical units differ')
    array=np.asanyarray(image.dataobj)
    require(np.isin(array,[0,1]).all() and int(array.sum())==expected_foreground,'Native mask differs')
    return dict(shape=list(image.shape),affine=image.affine.tolist(),foreground=int(array.sum()),
                bytes=path.stat().st_size,sha256=expected_sha256)


def export_prediction(path,probability,record):
    path=Path(path)
    require(path.suffixes[-2:]==['.nii','.gz'] and not path.exists() and not path.is_symlink(),
            'Fresh compressed export required')
    require(probability.device.type=='cpu' and probability.dtype==torch.float32 and
            list(probability.shape)==[2,*record['processed_shape']] and torch.isfinite(probability).all().item()
            and (probability>=0).all().item() and (probability<=1).all().item() and
            torch.allclose(probability.sum(0),torch.ones_like(probability[0]),atol=1e-5,rtol=0),
            'Invalid processed probabilities')
    started=time.monotonic();mask=probability.argmax(0,keepdim=True)
    processed_foreground=int(mask.sum())
    native=restore_to_source(mask,record,discrete=True)
    array=native.as_tensor()[0].numpy().astype(np.uint8)
    require(np.isin(array,[0,1]).all(),'Restored mask not binary')
    restored_seconds=time.monotonic()-started;started=time.monotonic()
    image=nib.Nifti1Image(array,np.asarray(record['source_affine']))
    image.set_sform(record['source_affine'],code=1);image.header.set_xyzt_units('mm')
    # Reserve the name exclusively; a failed write remains incomplete, never a passing receipt.
    with path.open('xb'):pass
    nib.save(image,path)
    with path.open('rb') as stream:os.fsync(stream.fileno())
    pin=digest(path.read_bytes());foreground=int(array.sum())
    checked=verify_export(path,record,expected_sha256=pin,expected_foreground=foreground)
    return dict(**checked,processed_foreground=processed_foreground,restoration_seconds=restored_seconds,
                export_verify_seconds=time.monotonic()-started)
