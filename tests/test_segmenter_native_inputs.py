import csv
import json
import numpy as np
import nibabel as nib
import pytest
from src.data.segmenter_native_inputs_v1 import NativeInputs
from src.training.experiment_config import sha256


def make_inputs(tmp_path, *, bad_affine=False, lesion_code=1, nan_ct=False):
    shape=(20,22,18); affine=np.diag([-.7,.9,2.,1.])
    fields={}
    for kind in ('ct','pancreas','lesion'):
        x=np.zeros(shape,np.float32 if kind=='ct' else np.uint8)
        if kind=='ct':
            x.fill(20)
            if nan_ct:x[0,0,0]=np.nan
        elif kind=='pancreas':x[5:15,5:15,5:15]=1
        else:x[9,10,11]=lesion_code
        a=affine.copy()
        if bad_affine and kind=='lesion':a[0,3]+=1
        path=tmp_path/(kind+'.nii.gz');nib.save(nib.Nifti1Image(x,a),path)
        fields[kind+'_path']=str(path)
    manifest=tmp_path/'manifest.csv'
    with manifest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['case_id',*fields]);w.writeheader()
        for name in ('t','d'):w.writerow(dict(case_id=name,**fields))
    observations={}
    for kind in ('ct','pancreas','lesion'):
        path=tmp_path/(kind+'.nii.gz');s=path.stat()
        observations[kind]=dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
    # NIfTI float affine serialization is authoritative, not the pre-serialization double.
    real_affine=nib.load(fields['ct_path']).affine.tolist()
    metadata=dict(source_sha256={k:sha256(fields[k+'_path']) for k in ('ct','pancreas','lesion')},
                  transform=dict(source_shape=list(shape),source_affine=real_affine))
    members={}
    for name in ('t','d'):
        path=tmp_path/(name+'.json');path.write_text(json.dumps(metadata))
        members[name]=dict(metadata_sha256=sha256(path))
    (tmp_path/'control.json').write_text(json.dumps(dict(train=['t'],validation=['d'],
        observations={n:observations for n in ('t','d')},manifest_sha256=sha256(manifest))))
    review=tmp_path/'review.json';review.write_text(json.dumps(dict(prepared_cache=dict(root=str(tmp_path),members=members),
                                                                 target_states={'t':'positive','d':'positive'})))
    train=tmp_path/'train.txt';train.write_text('t')
    dev=tmp_path/'dev.txt';dev.write_text('d')
    return NativeInputs(manifest=manifest,review=review,train_file=train,dev_file=dev)


def test_real_nifti_loader_alignment_lossless_and_padding(tmp_path):
    p=make_inputs(tmp_path);c=p.load('t',role='train')
    assert c['image'].dtype==np.float32
    assert (c['target']==2).sum()==1
    x,y,transform,trace=p.window('t',role='train',operation='optimizer',visit=0,seed=42)
    assert x.shape==(1,144,144,144) and (y==2).sum()==1
    assert transform['normalized_shape']==[20,22,18]
    assert np.all(x[:,20:]==0)


@pytest.mark.parametrize('options',[dict(bad_affine=True),dict(lesion_code=2),dict(nan_ct=True)])
def test_bad_source_is_not_silently_admitted(tmp_path,options):
    p=make_inputs(tmp_path,**options)
    with pytest.raises((ValueError,RuntimeError)):p.load('t',role='train')


def test_mutated_source_and_evaluator_sampling_refused(tmp_path):
    p=make_inputs(tmp_path)
    with pytest.raises(ValueError):p.window('d',role='validation',operation='evaluator',visit=0,seed=42)
    with (tmp_path/'lesion.nii.gz').open('ab') as f:f.write(b'changed')
    with pytest.raises(ValueError,match='Source observation changed'):p.load('t',role='train')
