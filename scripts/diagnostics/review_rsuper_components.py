"""Bounded paired component audit on saved probabilities; no CT or model runs."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
OUT=BASE/'rsuper-merlin-components-01'


def worker():
    if os.environ.get('PROWL_RSUPER_REVIEW')!='1':raise ValueError('Supervisor required')
    import numpy as np
    import nibabel as nib
    from scipy import ndimage
    from src.data.segmenter_native_windows_v1 import orient
    from src.data.segmenter_content_v1 import target_content
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():assert sha(Path(p))==h
    bindings=json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot']
    rows=[]
    for binding in bindings:
        name=binding['case_id']; meta=json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
        p=Path(binding['files']['lesion']['path']);assert sha(p)==binding['files']['lesion']['sha256']
        obj=nib.load(p);assert list(obj.shape)==meta['parent_geometry']['source_shape']
        assert np.allclose(obj.affine,meta['parent_geometry']['source_affine'],atol=1e-4,rtol=0)
        mask,_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        sl=tuple(slice(l,h) for l,h in zip(meta['region_low'],meta['region_high']))
        target=orient(mask,meta['parent_geometry'])[sl].astype(bool);del mask
        assert int(target.sum())==meta['lesion_voxels']
        if name=='PanTS_00003059':target[:]=False
        labels,count=ndimage.label(target,structure=np.ones((3,3,3)))
        voxel_ml=abs(np.linalg.det(np.asarray(meta['geometry']['affine'])[:3,:3]))/1000
        probs={}
        for label,folder in [('baseline','patient-pilot-02'),('candidate','rsuper-merlin-pilot-01')]:
            with np.load(BASE/f'{folder}/{name}-probability.npz',allow_pickle=False) as z:
                raw=z['probability'];assert raw.dtype==np.uint16 and raw.shape==target.shape
                probs[label]=raw.astype(np.float32)/65535
        parts=[]
        for i in range(1,count+1):
            region=labels==i;n=int(region.sum())
            parts.append(dict(index=i,voxels=n,volume_ml=n*voxel_ml,
                **{label:dict(detected=bool((q[region]>.5).any()),recall=float((q[region]>.5).mean()),
                    suppressed_at_point1=int((q[region]<=.1).sum())) for label,q in probs.items()}))
        rows.append(dict(case_id=name,components=parts,
            **{label:dict(high_confidence_false_voxels=int(((q>=.9)&~target).sum()),
                false_positive_volume_ml=float(((q>.5)&~target).sum()*voxel_ml)) for label,q in probs.items()}))
        print(name,'components',count,flush=True)
    allparts=[c for r in rows for c in r['components']]
    small=[c for c in allparts if c['volume_ml']<1]
    summary={label:dict(detected_components=sum(c[label]['detected'] for c in allparts),
        detected_small_components=sum(c[label]['detected'] for c in small),
        high_confidence_false_voxels=sum(r[label]['high_confidence_false_voxels'] for r in rows)) for label in ['baseline','candidate']}
    write(OUT/'result.json',dict(cases=rows,summary=summary,components=len(allparts),small_components=len(small),
        ct_reads=0,model_runs=0,scope='corrected provided annotations, exposed cases; components not clinical lesion counts',
        quantization='uint16 cached probabilities; half-step uncertainty near thresholds'))


if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        storage_preflight()
        overlay=BASE/'annotation-errata-02/overlay.json'
        assert sha(overlay)=='033f8f5cb7533031412a04f8daff62e5f95786123d0a21fc3c32c711ef5b06bc'
        files=[Path(__file__).resolve(),BASE/'pilot-local-bindings-01.json',overlay]
        for folder in ['patient-pilot-02','rsuper-merlin-pilot-01']:
            resources=json.loads((BASE/folder/'resources.json').read_text())
            assert resources['success'] and resources['workers_reaped']
            files.extend([BASE/folder/'result.json',*sorted((BASE/folder).glob('*-probability.npz'))])
        bindings=json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot']
        files.extend(BASE/f'metadata-received-01/native-region/members/{r["case_id"]}.json' for r in bindings)
        OUT.mkdir(exist_ok=False)
        write(OUT/'request.json',dict(pins={str(p):sha(p) for p in files},seconds=600,rss_bytes=12*1024**3))
        ok=run([sys.executable,__file__,'--worker'],OUT,seconds=600,rss_bytes=12*1024**3,
            env={**os.environ,'PROWL_RSUPER_REVIEW':'1','OMP_NUM_THREADS':'2'})
        if not ok:raise SystemExit(1)
