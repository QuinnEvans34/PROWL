"""Two exposed real cases: actual SuPreM/MPS KD updates and independent cold recovery.
Qualification only: never a scientific comparison or a shortened 24k experiment.
"""
import json,os,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight,check_storage_budget
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.data.manifest_records import canonical,digest
OUT=BASE/'rsuper-real-kd-01';NAMES=['PanTS_00002720','PanTS_00006222']
BACKUP=Path.home()/'PROWL-Backups/rsuper-real-kd-20261023-01.pt'

class Provider:
    def __init__(self):
        import numpy as np
        import nibabel as nib
        from src.data.segmenter_content_v1 import target_content
        from src.data.segmenter_native_windows_v1 import geometry,orient
        from src.data.segmenter_pancreas_region_v1 import crop_case
        from src.data.segmenter_varied_region_v1 import planned_visits
        b=json.loads((BASE/'pilot-local-bindings-01.json').read_text());self.rows={r['case_id']:r for r in b['pilot']}
        train=(BASE/'metadata-received-01/membership/train.txt').read_text().split();counts,_=planned_visits(train)
        self.control=dict(train=NAMES,validation=(BASE/'metadata-received-01/membership/development.txt').read_text().split(),planned_focused_counts={n:counts[n] for n in NAMES},qualification_only=True,source_bindings_sha256=sha(BASE/'pilot-local-bindings-01.json'),sampler='existing_varied_full_schedule_counts_two_case_engineering_only')
        self.pin=digest(canonical(self.control));self.planned_counts=counts;self.component_cache={};self.cases={};self.small={}
        for name in NAMES:
            files=self.rows[name]['files'];objects={}
            for kind,f in files.items():
                assert sha(Path(f['path']))==f['sha256'];objects[kind]=nib.load(f['path'])
            ct=objects['ct'];parent=geometry(ct.shape,ct.affine);masks={}
            for kind in ('pancreas','lesion'):
                obj=objects[kind];assert obj.shape==ct.shape and np.allclose(obj.affine,ct.affine,atol=1e-5,rtol=0)
                masks[kind],_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
            image=orient(ct.get_fdata(dtype=np.float32,caching='unchanged'),parent);assert np.isfinite(image).all()
            np.clip(image,-100,250,out=image);image+=100;image/=350
            target=orient(masks['pancreas'],parent).astype(np.uint8);target[orient(masks['lesion'],parent)!=0]=2
            small=json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
            case=crop_case(dict(name=name,image=image,target=target,geometry=parent,original_pancreas=masks['pancreas'],source_sha256=small['source_sha256']))
            assert case['geometry']==small['geometry'] and case['region_low']==small['region_low'] and case['region_high']==small['region_high']
            assert int((case['target']==2).sum())==small['lesion_voxels']
            self.cases[name]=case;self.small[name]=small
    def check_role(self,name,role,operation):
        if name not in NAMES or role!='train' or operation!='optimizer':raise ValueError('Fixed engineering cases only')
    def plan_next(self,request):pass
    def cache_member(self,name):return None,self.small[name]
    def training_window(self,name,**kwargs):
        from src.data.segmenter_varied_region_v1 import VariedInputs
        return VariedInputs.from_case(self,self.cases[name],**kwargs)

def worker(stage):
    import torch,numpy as np
    from src.data.segmenter_teacher_cache_v1 import SCHEMA,QUANTIZATION_ERROR,identity_for,TeacherTargetStore
    from src.training.segmenter_full_session_v1 import Session
    from src.training.segmenter_fast_varied_session_v1 import FastVariedSession
    from src.training.segmenter_distillation_session_v1 import DistillationSession
    from src.training.segmenter_distillation_v1 import DistillationConfig
    from scripts.diagnostics.mac_kd_synthetic import compare
    torch.set_num_threads(1);request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():assert sha(Path(p))==h,p
    p=Provider();teacher=request['teacher'];dest=OUT/stage
    common=dict(teacher_sha256=teacher['weights']['sha256'],teacher_config_sha256=digest(canonical(teacher['config'])),teacher_mapping_sha256=digest(canonical(teacher['labels'])),preprocessing_sha256=digest(canonical(request['preprocessing_policy'])),control_sha256=p.pin)
    target_root=OUT/'targets'
    if stage=='producer':
        target_root.mkdir();members={}
        for name in NAMES:
            origin=BASE/f'rsuper-merlin-pilot-01/{name}-probability.npz';shutil.copyfile(origin,target_root/(name+'.npz'))
            with np.load(origin,allow_pickle=False) as z:
                values=z['probability'];assert values.dtype==np.uint16 and values.shape==tuple(p.small[name]['geometry']['shape'])
            members[name]=dict(schema=SCHEMA,identity=identity_for(name,p.small[name],common),shape=list(values.shape),storage='uint16_probability_round_to_nearest_div65535',support='entire_native_region',payload_sha256=sha(origin),bytes=origin.stat().st_size,max_quantization_error=QUANTIZATION_ERROR)
        write(target_root/'manifest.json',dict(schema=SCHEMA,control_sha256=p.pin,members=members,complete=False,qualification_only=True,provenance='Saved pinned pilot uint16 output, original round-to-nearest encoder; no new inference'))
    targets=TeacherTargetStore(target_root,sha(target_root/'manifest.json'),control=p.control,common_identity=common,qualification_only=True)
    def student():return FastVariedSession(Session(request['student_configuration']['session'],p.control,device='mps',initialization=request['student_configuration']['initialization']))
    def kd(weight):return DistillationSession(student(),teacher_identity=teacher,loss_config=DistillationConfig(max_weight=weight),target_manifest_sha256=targets.pin)
    if stage=='producer':
        control=student();zero=kd(0);a=control.update(p);b=zero.update(p)
        compare(control.state(),zero.student.state());assert not b['teacher_accessed'] and a['batch_sha256']==b['batch_sha256']
        del control,zero;torch.mps.empty_cache()
        s=kd(.1);rows=[s.update(p,targets)];torch.save(s.state(),dest/'saved.pt')
        rows.append(s.update(p,targets));torch.save(s.state(),dest/'expected.pt')
        assert all(r['teacher_accessed'] and r['kd_weight']>0 and r['eligible_voxels']>0 for r in rows)
        write(dest/'updates.json',rows);write(dest/'identity.json',s.identity)
    else:
        receipt=json.loads((OUT/'backup.json').read_text());assert sha(BACKUP)==receipt['sha256']
        state=torch.load(BACKUP,weights_only=True,map_location='cpu');s=DistillationSession.restore(state,json.loads((OUT/'producer/identity.json').read_text()))
        row=s.update(p,targets);compare(s.state(),torch.load(OUT/'producer/expected.pt',weights_only=True,map_location='cpu'));write(dest/'updates.json',[row])
    torch.mps.synchronize();allocation=torch.mps.driver_allocated_memory();assert allocation<=12*1024**3
    write(dest/'result.json',dict(success=True,stage=stage,real_cases=NAMES,scientific_updates=0,engineering_updates=4 if stage=='producer' else 1,qualified_scope='two real cases only; full cohort/provider/executor not qualified',mps_driver_bytes=allocation,rtol=1.3e-6,atol=1e-5))

if __name__=='__main__':
    if '--worker' in sys.argv:worker(sys.argv[-1])
    else:
        from src.operations.mac_pilot_supervision_v1 import run
        from src.operations.full_training_platform import training_guard,require_ac
        require_ac();storage_preflight();OUT.mkdir(exist_ok=False)
        request=json.loads((BASE/'rsuper-merlin-pilot-01/request.json').read_text());request['pins'][str(Path(__file__).resolve())]=sha(Path(__file__))
        cfg=json.loads((ROOT/'configs/experiments/mac-kd-comparison-20261023/treatment.json').read_text())['student_configuration']
        init=cfg['initialization'];init['checkpoint']=str((ROOT/init['checkpoint']).resolve());assert sha(Path(init['checkpoint']))==init['sha256']
        request.update(student_configuration=cfg,scope='two-case actual-MPS engineering, not scientific training',seconds_per_stage=1200,rss_bytes=12*1024**3)
        for name in NAMES:
            f=BASE/f'rsuper-merlin-pilot-01/{name}-probability.npz';request['pins'][str(f)]=sha(f)
        write(OUT/'request.json',request)
        env=dict(os.environ,PYTORCH_ENABLE_MPS_FALLBACK='0',OMP_NUM_THREADS='1')
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            for stage in ('producer','cold'):
                dest=OUT/stage;dest.mkdir()
                if stage=='cold':
                    src=OUT/'producer/saved.pt';storage=storage_preflight();size=src.stat().st_size
                    check_storage_budget(storage['internal_free_bytes'],storage['external_free_bytes'],storage['existing_backup_bytes'],new_backup_bytes=size)
                    with src.open('rb') as a,BACKUP.open('xb') as b:shutil.copyfileobj(a,b)
                    assert sha(src)==sha(BACKUP);write(OUT/'backup.json',dict(path=str(BACKUP),sha256=sha(BACKUP),bytes=size))
                if not run(['caffeinate','-i',sys.executable,__file__,'--worker',stage],dest,seconds=1200,rss_bytes=12*1024**3,env=env):raise SystemExit(1)
