"""Unchanged v2 teacher computation with validated header-derived geometry checks."""
import csv,json,os,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.data.manifest_records import canonical,digest
OLD=BASE/'rsuper-full-targets-01'
OUT=BASE/'rsuper-full-targets-02';SOURCES=BASE/'rsuper-training-sources-01'
LIMITS=dict(seconds=96*3600-600,rss_bytes=12*1024**3,mps_driver_bytes=12*1024**3,output_bytes=31*1024**3,max_voxels=256000000,max_case_tiles=10000)

def worker():
    import numpy as np,torch,SimpleITK as sitk
    from src.training.teacher_medformer_v1 import FrozenTeacher
    from src.data.segmenter_teacher_geometry_v2 import preprocess,predict,reconstruct
    from src.data.teacher_header_geometry_v1 import checked_header_grid
    from src.operations.full_training_platform import require_ac
    req=json.loads((OUT/'request.json').read_text())
    for p,h in req['pins'].items():assert sha(Path(p))==h,p
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    teacher=FrozenTeacher(req['teacher'],digest(canonical(req['teacher'])),device='mps')
    before={k:v.detach().cpu().clone() for k,v in teacher.model.state_dict().items()}
    with (SOURCES/'manifest.csv').open() as f:rows={r['case_id']:r for r in csv.DictReader(f)}
    old=json.loads((SOURCES/'metadata/control.json').read_text());members={};began=time.monotonic()
    pilot_names={r['case_id'] for r in json.loads((BASE/'rsuper-merlin-pilot-01/result.json').read_text())['cases']}
    for index,name in enumerate(req['train']):
        storage_preflight();require_ac();meta=json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
        p=Path(rows[name]['ct_path']);s=p.stat();obs=dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
        assert obs==old['observations'][name]['ct'],'CT source observation changed'
        target=OUT/(name+'.npz');start=time.monotonic()
        if name in req['reused_completed']:
            record=req['reused_completed'][name];source=OLD/(name+'.npz')
            assert sha(source)==record['payload_sha256']
            assert record['source_ct_sha256']==meta['source_sha256']['ct'] and record['native_geometry']==meta['geometry']
            with np.load(source,allow_pickle=False) as z:assert z['probability'].dtype==np.uint16 and list(z['probability'].shape)==meta['geometry']['shape']
            shutil.copyfile(source,target);mapping=record['reconstruction'];tiles=0
        elif name in pilot_names:
            source=BASE/f'rsuper-merlin-pilot-01/{name}-probability.npz';assert sha(source)==req['pins'][str(source)]
            with np.load(source,allow_pickle=False) as z:assert z['probability'].dtype==np.uint16 and list(z['probability'].shape)==meta['geometry']['shape']
            shutil.copyfile(source,target);mapping=json.loads((BASE/f'rsuper-merlin-pilot-01/{name}.json').read_text())['reconstruction'];tiles=0
        else:
            image=sitk.ReadImage(str(p));values,grid,processing=preprocess(image,max_voxels=LIMITS['max_voxels'])
            expected=checked_header_grid(image,meta);assert grid['shape']==expected['shape'] and np.allclose(grid['affine'],expected['affine'],atol=1e-4,rtol=0)
            def tick(info):
                torch.mps.synchronize()
                if torch.mps.driver_allocated_memory()>LIMITS['mps_driver_bytes']:raise ValueError('MPS resource limit')
                if info['tile']%25==0:
                    with (OUT/'tiles.jsonl').open('a') as f:f.write(json.dumps(dict(case_id=name,**info))+'\n')
            q,tiling=predict(values,teacher.lesion_probability,max_voxels=LIMITS['max_voxels'],max_tiles=LIMITS['max_case_tiles'],tick=tick)
            native,mapping=reconstruct(q,grid,meta['geometry'],max_voxels=LIMITS['max_voxels']);assert np.isfinite(native).all() and native.min()>=0 and native.max()<=1
            encoded=np.rint(native*65535).astype(np.uint16)
            assert np.max(np.abs(encoded.astype(np.float32)/65535-native))<=.5/65535+np.finfo(np.float32).eps
            with target.open('xb') as f:np.savez_compressed(f,probability=encoded)
            tiles=tiling['tiles'];del image,values,q,native,encoded;torch.mps.empty_cache()
        row=dict(case_id=name,payload_sha256=sha(target),bytes=target.stat().st_size,source_ct_sha256=meta['source_sha256']['ct'],native_geometry=meta['geometry'],reconstruction=mapping,reused_pilot=name in pilot_names,reused_completed=name in req['reused_completed'],tiles=tiles,seconds=time.monotonic()-start)
        write(OUT/(name+'.json'),row);members[name]=row
        with (OUT/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(completed=index+1,total=len(req['train']),case_id=name,seconds=time.monotonic()-began))+'\n')
        print(index+1,'/',len(req['train']),name,flush=True)
        if sum(r['bytes'] for r in members.values())>LIMITS['output_bytes']:raise ValueError('Target cache cap')
    assert all(torch.equal(before[k],v.detach().cpu()) for k,v in teacher.model.state_dict().items())
    write(OUT/'result.json',dict(success=True,complete=True,members=members,scientific_updates=0,training_manifest_admitted=False,scope='complete prediction payloads; final provider-bound manifest and launch qualification still required'))

