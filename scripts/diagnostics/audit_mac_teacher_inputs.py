"""Bounded CPU input audit of five exposed pilot cases; no model or training."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE, storage_preflight, write
OUT=BASE/'input-audit-02'
CASES=['PanTS_00002720','PanTS_00003059','PanTS_00000691','PanTS_00006222','PanTS_00008658']


def extract(path,names,scope):
    nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)


def worker():
    import numpy as np
    import nibabel as nib
    import SimpleITK as sitk
    import torch
    import torch.nn.functional as F
    from scipy import ndimage
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.data.segmenter_teacher_geometry_v1 import preprocess as old_preprocess
    from src.data.segmenter_teacher_geometry_v2 import preprocess, grid, plan
    from src.data.segmenter_content_v1 import target_content
    from src.data.segmenter_native_windows_v1 import orient
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    source=BASE/'teacher/source/rsuper_train'
    scope=dict(np=np,sitk=sitk,torch=torch,F=F)
    extract(source/'dataset_conversion/utils.py',['ResampleXYZAxis','reorient_image'],scope)
    extract(source/'predict_abdomenatlas.py',['pad_to_training_size'],scope)
    extract(source/'inference/inference3d.py',['make_gaussian_kernel'],scope)
    extract(source/'inference/utils.py',['split_idx'],scope)
    # Execute actual resampling/reorientation helpers. CPU reductions below mirror
    # upstream explicitly; no claim of CUDA reduction or complete executor parity.
    bindings=json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot']
    pins=json.loads((BASE/'patient-pilot-02/request.json').read_text())['pins']
    for path,sha in pins.items():
        with open(path,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha,path
    rows=[]
    for name in CASES:
        b=next(r for r in bindings if r['case_id']==name)
        meta=json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
        for f in b['files'].values():
            with open(f['path'],'rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==f['sha256']
        obj=nib.load(b['files']['ct']['path']);image=sitk.ReadImage(b['files']['ct']['path'])
        assert np.prod(obj.shape)<=256000000
        decoded=np.asarray(obj.dataobj,dtype=np.float32)
        itk=sitk.GetArrayFromImage(image).transpose(2,1,0).astype(np.float32)
        assert np.isfinite(decoded).all() and np.array_equal(decoded,itk)
        assert np.allclose(obj.affine,np.asarray(grid(image)['affine'])@np.eye(4)[:,[2,1,0,3]],rtol=0,atol=1e-4)
        row=dict(case_id=name,reader_voxels_exact=True,reader_world_geometry_matches=True,
                 source_shape=list(obj.shape),source_spacing=list(image.GetSpacing()),
                 ct_min=float(decoded.min()),ct_max=float(decoded.max()))
        del itk
        ref=scope['reorient_image'](image,'RAI');spacing=ref.GetSpacing()
        if spacing!=(1.,1.,1.):
            ref=scope['ResampleXYZAxis'](ref,(1.,1.,spacing[2]),sitk.sitkBSpline)
            ref=scope['ResampleXYZAxis'](ref,(1.,1.,1.),sitk.sitkNearestNeighbor)
        t=torch.from_numpy(sitk.GetArrayFromImage(ref).astype(np.float32)).clamp_(-991,500)
        mean=t.mean();std=t.std();t.sub_(mean).div_(std)
        old,_,_=old_preprocess(image,max_voxels=256000000)
        row['legacy_cpu_preprocessing_exact']=bool(np.array_equal(t.numpy(),old))
        assert row['legacy_cpu_preprocessing_exact']
        new,tgrid,stats=preprocess(image,max_voxels=256000000)
        common=tuple(slice(0,min(a,b)) for a,b in zip(old.shape,new.shape))
        row.update(legacy_shape=list(old.shape),revised_shape=list(new.shape),
                   revised_common_max_abs=float(np.max(np.abs(old[common]-new[common]))))
        padded,indices=scope['pad_to_training_size'](t,SimpleNamespace(dimension='3d',training_size=[128]*3))
        row['upstream_padded_shape']=list(padded.shape)
        row['candidate_padded_shape']=plan(new.shape,max_voxels=256000000,max_tiles=1500)['padded']
        del t,old,new,padded,ref,image
        masks={};reports={}
        for role in ('pancreas','lesion'):
            m=nib.load(b['files'][role]['path']);assert m.shape==obj.shape and np.allclose(m.affine,obj.affine,rtol=0,atol=1e-4)
            masks[role],reports[role]=target_content(m.dataobj.get_unscaled(),dict(slope=float(m.dataobj.slope),intercept=float(m.dataobj.inter)))
        row['label_decoding']=reports
        lesion=masks['lesion']!=0;lab,count=ndimage.label(lesion,np.ones((3,3,3)))
        row['lesion_components']=count
        row['lesion_outside_pancreas_voxels']=int((lesion & (masks['pancreas']==0)).sum())
        row['lesion_touches_source_boundary']=bool(any(np.take(lesion,i,axis=a).any() for a in range(3) for i in (0,-1)))
        sl=tuple(slice(a,b) for a,b in zip(meta['region_low'],meta['region_high']))
        display=orient(decoded,meta['parent_geometry'])[sl];target=orient(lesion,meta['parent_geometry'])[sl]
        with np.load(BASE/f'patient-pilot-02/{name}-probability.npz') as z:pred=z['probability']>32767.5
        labels,n=ndimage.label(target,np.ones((3,3,3)))
        anchors=[]
        for k in range(1,n+1):
            indices=np.flatnonzero((labels==k).any(axis=(0,1)))
            for z in sorted(set([int(indices[0]),int(indices[len(indices)//2]),int(indices[-1])])):anchors.append((k,z))
        if not anchors:
            indices=np.flatnonzero(pred.any(axis=(0,1)))
            anchors=[(0,int(z)) for z in indices[::max(1,len(indices)//6)][:6]]
        fig,axes=plt.subplots(len(anchors),1,figsize=(7,3*len(anchors)),squeeze=False)
        sp=np.linalg.norm(np.asarray(meta['geometry']['affine'])[:3,:3],axis=0)
        for ax,(k,z) in zip(axes.flat,anchors):
            ax.imshow(display[:,:,z].T,cmap='gray',vmin=-150,vmax=250,origin='lower',aspect=sp[1]/sp[0])
            if target[:,:,z].any():ax.contour(target[:,:,z].T,levels=[.5],colors='red',linewidths=.7)
            if pred[:,:,z].any():ax.contour(pred[:,:,z].T,levels=[.5],colors='yellow',linewidths=.7)
            ax.set_title(f'{name} component {k} axial {z}: red annotation / yellow prediction');ax.axis('off')
        fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=100);plt.close(fig)
        rows.append(row);write(OUT/(name+'.json'),row)
        print(name, 'reader and legacy CPU parity PASS',row['revised_common_max_abs'],flush=True)
        del decoded,display,target,lesion,masks,lab,labels,pred
    synth=torch.zeros((65,130,140))
    padded,_=scope['pad_to_training_size'](synth,SimpleNamespace(dimension='3d',training_size=[128]*3))
    write(OUT/'result.json',dict(cases=rows,model_runs=0,training_updates=0,
        upstream_padding_probe=dict(input_shape=list(synth.shape),output_shape=list(padded.shape)),
        source_hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'predict_abdomenatlas.py',source/'dataset_conversion/utils.py',source/'inference/inference3d.py',source/'inference/utils.py']},
        scope='Five exposed training cases; CPU preprocessing parity only, no clinical annotation adjudication'))


if __name__=='__main__':
    if '--worker' in sys.argv:
        if os.environ.get('PROWL_INPUT_AUDIT')!='1':raise ValueError('Supervisor required')
        worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight();OUT.mkdir(exist_ok=False)
        write(OUT/'request.json',dict(cases=CASES,seconds=600,rss_bytes=12*1024**3,model_runs=0,
            script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
        ok=run([sys.executable,__file__,'--worker'],OUT,seconds=600,rss_bytes=12*1024**3,
               env={**os.environ,'PROWL_INPUT_AUDIT':'1','OMP_NUM_THREADS':'2'})
        raise SystemExit(0 if ok else 1)
