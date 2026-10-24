"""Bounded full-cohort offline teacher preparation; never starts student training."""
import csv,json,os,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.data.manifest_records import canonical,digest
OUT=BASE/'rsuper-full-targets-01';SOURCES=BASE/'rsuper-training-sources-01'
LIMITS=dict(seconds=96*3600,rss_bytes=12*1024**3,mps_driver_bytes=12*1024**3,output_bytes=31*1024**3,max_voxels=256000000,max_case_tiles=10000)

def worker():
    import numpy as np,torch,SimpleITK as sitk
    from src.training.teacher_medformer_v1 import FrozenTeacher
    from src.data.segmenter_teacher_geometry_v2 import preprocess,predict,reconstruct,metadata_grid
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
        if name in pilot_names:
            source=BASE/f'rsuper-merlin-pilot-01/{name}-probability.npz';assert sha(source)==req['pins'][str(source)]
            with np.load(source,allow_pickle=False) as z:assert z['probability'].dtype==np.uint16 and list(z['probability'].shape)==meta['geometry']['shape']
            shutil.copyfile(source,target);mapping=json.loads((BASE/f'rsuper-merlin-pilot-01/{name}.json').read_text())['reconstruction'];tiles=0
        else:
            image=sitk.ReadImage(str(p));values,grid,processing=preprocess(image,max_voxels=LIMITS['max_voxels'])
            expected=metadata_grid(meta['parent_geometry']);assert grid['shape']==expected['shape'] and np.allclose(grid['affine'],expected['affine'],atol=1e-4,rtol=0)
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
        row=dict(case_id=name,payload_sha256=sha(target),bytes=target.stat().st_size,source_ct_sha256=meta['source_sha256']['ct'],native_geometry=meta['geometry'],reconstruction=mapping,reused_pilot=name in pilot_names,tiles=tiles,seconds=time.monotonic()-start)
        write(OUT/(name+'.json'),row);members[name]=row
        with (OUT/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(completed=index+1,total=len(req['train']),case_id=name,seconds=time.monotonic()-began))+'\n')
        print(index+1,'/',len(req['train']),name,flush=True)
        if sum(r['bytes'] for r in members.values())>LIMITS['output_bytes']:raise ValueError('Target cache cap')
    assert all(torch.equal(before[k],v.detach().cpu()) for k,v in teacher.model.state_dict().items())
    write(OUT/'result.json',dict(success=True,complete=True,members=members,scientific_updates=0,training_manifest_admitted=False,scope='complete prediction payloads; final provider-bound manifest and launch qualification still required'))

if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        from src.operations.full_training_platform import training_guard,require_ac
        require_ac();storage_preflight()
        for folder in [SOURCES,BASE/'rsuper-real-kd-01/producer',BASE/'rsuper-real-kd-01/cold']:
            r=json.loads((folder/'resources.json').read_text());assert r['success'] and r['workers_reaped']
        assert json.loads((SOURCES/'result.json').read_text())['success']
        req=json.loads((BASE/'rsuper-merlin-pilot-01/request.json').read_text());req.update(scope='full training-cohort target preparation only',limits=LIMITS,train=(SOURCES/'train.txt').read_text().split())
        for p in [Path(__file__).resolve(),SOURCES/'manifest.csv',SOURCES/'metadata/control.json',SOURCES/'train.txt',BASE/'rsuper-real-kd-01/cold/result.json']+list((BASE/'rsuper-merlin-pilot-01').glob('*-probability.npz'))+list((BASE/'metadata-received-01/native-region/members').glob('*.json')):
            req['pins'][str(p)]=sha(p)
        from src.data.segmenter_teacher_geometry_v2 import metadata_grid,plan,checked_shape
        from scripts.diagnostics.review_mac_teacher_failure import coverage
        dev=set((SOURCES/'development.txt').read_text().split())
        assert len(req['train'])==len(set(req['train']))==1333 and not set(req['train'])&dev
        for name in req['train']:
            meta=json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
            grid=metadata_grid(meta['parent_geometry']);checked_shape(meta['geometry']['shape'],LIMITS['max_voxels'])
            plan(grid['shape'],max_voxels=LIMITS['max_voxels'],max_tiles=LIMITS['max_case_tiles'])
            assert coverage(grid,meta['geometry'])['covered'],name
        # Combined relevant probability/target caches must retain the32GiB design cap.
        existing=sum(p.stat().st_size for p in BASE.rglob('*.npz'))
        assert existing+LIMITS['output_bytes']<=32*1024**3,'Combined target cache budget'
        OUT.mkdir(exist_ok=False);write(OUT/'request.json',req)
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            def tick():
                if sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())>LIMITS['output_bytes']:raise ValueError('Output budget')
            ok=run(['caffeinate','-i',sys.executable,__file__,'--worker'],OUT,seconds=LIMITS['seconds'],rss_bytes=LIMITS['rss_bytes'],tick=tick,env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='2'))
            if not ok:raise SystemExit(1)
