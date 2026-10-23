"""Metadata-only preparation and a separately invoked, bounded training-case pilot.

No scientific launch, automatic handoff, retry or resume. --prepare does not read
CT voxels, acquire a GPU or create an MLflow run. --pilot requires normal parent
completion and verifies independent backups before acquiring the same GPU lock.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.manifest_records import canonical,digest

OUT=Path('E:/PROWL/readiness/distillation-preparation-20261023-a01')
PARENT=Path('E:/PROWL/artifacts/pants_varied_focus_24k_20261022')
PARENT_SETUP=Path('E:/PROWL/readiness/varied-deterministic-20261022-a02')
PARENT_BACKUP=Path('C:/Users/quinn/PROWL-Backups/pants_varied_focus_24k_20261022')
SOURCE_CACHE=Path('E:/PROWL/cache/varied-targets-20261022-a01')
PILOT_CACHE=Path('E:/PROWL/cache/distillation-teacher-pilot-20261023-a01')
MODEL_PROOF=Path('E:/PROWL/readiness/distillation-engineering-20261023-a01/model-01')
PRIOR_SELECTION=Path('E:/PROWL/readiness/varied-focus-20261022-a01/pilot-selection.json')
SPEC=ROOT/'docs/capstone/operations/PANTS-TEACHER-DISTILLATION-20261023.md'
LIMITS=dict(seconds=5400,rss_bytes=12*1024**3,gpu_reserved_bytes=6*1024**3,
    cache_cap_bytes=32*1024**3,free_bytes=100*1024**3,max_source_or_resampled_voxels=256000000,
    max_tiles_per_case=1500,max_total_tiles=10000,pilot_cache_bytes=2*1024**3)


def read(path):return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def write(path,value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value));stream.flush();os.fsync(stream.fileno())
def tree_bytes(path):return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


def storage_projection(native_voxels,existing_bytes,cap_bytes):
    if native_voxels<1 or not 0<=existing_bytes<=cap_bytes:raise ValueError('Cache storage inputs')
    raw=2*native_voxels;remaining=cap_bytes-existing_bytes
    return dict(native_voxels=native_voxels,raw_uint16_bytes=raw,existing_cache_bytes=existing_bytes,
        combined_cap_bytes=cap_bytes,available_bytes=remaining,raw_fits=raw<=remaining,
        required_compressed_to_raw_ratio=remaining/raw,compression_measured=False,
        full_cache_authorized=False)


def prepare():
    import numpy as np
    from src.data.segmenter_teacher_geometry_v1 import POLICY,plan
    from src.training.segmenter_distillation_v1 import DistillationConfig,POLICY as LOSS_POLICY
    from dataclasses import asdict
    if OUT.exists():raise ValueError('Preparation already exists; inspect, do not overwrite')
    if not read(MODEL_PROOF/'resources.json')['success'] or not read(MODEL_PROOF/'result.json')['success']:
        raise ValueError('CPU model proof absent')
    for path,pin in read(MODEL_PROOF/'request.json')['pins'].items():
        if sha(path)!=pin:raise ValueError('CPU-qualified teacher implementation changed')
    teacher=read(MODEL_PROOF/'teacher-bundle.json');receipt=read(PARENT_SETUP/'ready.json')
    manifest=read(SOURCE_CACHE/'manifest.json');selection=read(PRIOR_SELECTION)
    if len(manifest['members'])!=1333 or not manifest['complete']:raise ValueError('Source cache incomplete')
    if len(selection['cases'])!=12 or not set(selection['cases'])<=set(manifest['members']):
        raise ValueError('Pilot role/membership mismatch')
    total=0;pilot=[];metadata_pins={}
    for name,member in manifest['members'].items():
        path=SOURCE_CACHE/(name+'.json')
        if sha(path)!=member['metadata_sha256']:raise ValueError('Existing metadata changed')
        small=read(path);total+=math.prod(small['geometry']['shape']);metadata_pins[str(path)]=member['metadata_sha256']
        if name in selection['cases']:
            parent=small['parent_geometry'];spacing=np.linalg.norm(np.array(parent['affine'])[:3,:3],axis=0)
            estimated=tuple(int(round(n*s)) for n,s in zip(parent['shape'],spacing))[::-1]
            tiling=plan(estimated,max_voxels=LIMITS['max_source_or_resampled_voxels'],max_tiles=LIMITS['max_tiles_per_case'])
            pilot.append(dict(case_id=name,positive=small['positive'],lesion_voxels=small['lesion_voxels'],
                reasons=selection['reasons'][name],estimated_teacher_shape=list(estimated),estimated_tiles=tiling['tiles'],
                native_region_voxels=math.prod(small['geometry']['shape'])))
    if sum(r['estimated_tiles'] for r in pilot)>LIMITS['max_total_tiles']:raise ValueError('Pilot tile projection exceeds budget')
    projection=storage_projection(total,tree_bytes(SOURCE_CACHE.parent),LIMITS['cache_cap_bytes'])
    common=dict(teacher_sha256=teacher['weights']['sha256'],teacher_config_sha256=teacher['files'][teacher['config']],
        teacher_mapping_sha256=digest(canonical(dict(labels=teacher['labels'],lesion_channel=teacher['lesion_channel'],activation=teacher['activation']))),
        preprocessing_sha256=digest(canonical(POLICY)),control_sha256=receipt['control_sha256'])
    files=[Path(__file__),SPEC,MODEL_PROOF/'teacher-bundle.json',MODEL_PROOF/'result.json',MODEL_PROOF/'resources.json',
        PARENT_SETUP/'ready.json',PARENT_SETUP/'configuration.json',SOURCE_CACHE/'manifest.json',PRIOR_SELECTION]
    files+=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    files+=list((ROOT/'tests').glob('test_distillation_*v1.py'))
    files+=[ROOT/'tests/test_segmenter_distillation_v1.py',ROOT/'tests/test_segmenter_teacher_targets_v1.py']
    pins={str(p):sha(p) for p in files};pins.update(metadata_pins)
    OUT.mkdir(exist_ok=False)
    write(OUT/'preparation.json',dict(status='ENGINEERING_PREPARED_NOT_LAUNCH_READY',scientific_launch_authorized=False,
        evidence_scope='user-approved teacher-assisted exploratory; potential teacher development exposure',
        teacher=teacher,teacher_identity_sha256=digest(canonical(teacher)),common_identity=common,
        candidate_student_configuration=read(PARENT_SETUP/'configuration.json'),control_choice_frozen=False,
        loss=dict(policy=LOSS_POLICY,**asdict(DistillationConfig())),loss_recipe_frozen=False,
        teacher_policy=POLICY,pilot=pilot,pilot_order=selection['cases'],limits=LIMITS,storage=projection,pins=pins,
        completed=['safe_tensor_conversion','strict_teacher_CPU_forward','additive_engineering'],
        pending=['current_run_completion_and_review','real_teacher_pilot_and_visual_review','measured_cache_and_wall_budget',
            'complete_train_target_manifest','actual_student_CUDA_zero_KD_and_positive_KD_cold_restore',
            'matched_control_and_scientific_recipe_freeze','qualified_launch_receipt','explicit_scientific_launch'],
        real_teacher_CT_reads=0,scientific_updates=0,automatic_handoff=False))
    print(json.dumps(dict(output=str(OUT),pilot_cases=len(pilot),estimated_pilot_tiles=sum(r['estimated_tiles'] for r in pilot),storage=projection)))


def normal_parent_gate(names):
    from scripts.train_varied_region import completion_evidence
    summary=completion_evidence(PARENT,PARENT_SETUP,names)
    if not read(PARENT_SETUP/'scientific-resources.json').get('workers_reaped'):raise ValueError('Parent workers not reaped')
    connection=sqlite3.connect('file:C:/Users/quinn/PROWL-Tracking/mlflow.db?mode=ro',uri=True)
    try:status=connection.execute('SELECT status FROM runs WHERE run_uuid=?',('a84c0a6ae0cb424ca182350425adc7aa',)).fetchone()
    finally:connection.close()
    if status!=('FINISHED',):raise ValueError('Parent MLflow not FINISHED')
    files=list((PARENT/'execution').glob('*.pt'))+list((PARENT/'execution').glob('native-*.json'))
    files += [PARENT/'execution/history.jsonl',PARENT/'result.json']
    if len(list((PARENT/'execution').glob('*.pt')))!=15:raise ValueError('Parent checkpoint inventory')
    if PARENT.stat().st_dev==PARENT_BACKUP.stat().st_dev:raise ValueError('Independent backup device')
    for path in files:
        if sha(path)!=sha(PARENT_BACKUP/path.name):raise ValueError('Parent backup mismatch')
    return summary


def resources():
    from src.operations.full_training_platform import require_ac
    require_ac()
    if any(shutil.disk_usage(d).free<LIMITS['free_bytes'] for d in ('C:/','E:/')):raise ValueError('Free-space floor')
    if tree_bytes(SOURCE_CACHE.parent)>LIMITS['cache_cap_bytes']:raise ValueError('Combined cache cap')
    if PILOT_CACHE.exists() and tree_bytes(PILOT_CACHE)>LIMITS['pilot_cache_bytes']:raise ValueError('Pilot cache cap')


def check_preparation():
    setup=read(OUT/'preparation.json')
    for path,pin in setup['pins'].items():
        if sha(path)!=pin:raise ValueError('Prepared producing pin changed: '+path)
    for path,pin in read(PARENT_SETUP/'ready.json')['pins'].items():
        if sha(path)!=pin:raise ValueError('Preserved current producer changed: '+path)
    if setup['limits']!=LIMITS:raise ValueError('Resource policy changed')
    return setup


def pilot_worker():
    import numpy as np
    import SimpleITK as sitk
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scripts.diagnostics.setup_fast_varied import provider
    from src.data.segmenter_fast_varied_v1 import source_info,normalize_region
    from src.data.segmenter_teacher_geometry_v1 import grid,preprocess,predict,reconstruct,checked_shape
    from src.data.segmenter_teacher_cache_v1 import SCHEMA,identity_for,write_member
    from src.training.teacher_medformer_v1 import FrozenTeacher
    setup=check_preparation();root=OUT/'pilot-01'
    if read(root/'request.json')['preparation_sha256']!=sha(OUT/'preparation.json'):
        raise ValueError('Pilot request binding changed')
    p=provider(prefetch=False)
    torch.set_num_threads(2);sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    teacher=FrozenTeacher(setup['teacher'],setup['teacher_identity_sha256'],device='cuda')
    state_before={k:v.detach().cpu().clone() for k,v in teacher.model.state_dict().items()}
    torch.cuda.reset_peak_memory_stats();members={};reports=[];total_tiles=0
    PILOT_CACHE.mkdir(exist_ok=False)
    try:
        if p.pin!=setup['common_identity']['control_sha256']:raise ValueError('Candidate control changed')
        for name in setup['pilot_order']:
            p.check_role(name,'train','optimizer');resources();began=time.monotonic()
            meta,_,_=source_info(p,name,'train','optimizer');array,small=p.cache_member(name)
            checked_shape(small['parent_geometry']['source_shape'],LIMITS['max_source_or_resampled_voxels'])
            image=sitk.ReadImage(p.rows[name]['ct_path'])
            # Compare ITK and admitted NIfTI coordinates, including translations.
            source_grid=grid(image);reverse=np.eye(4)[:,[2,1,0,3]]
            if (list(image.GetSize())!=small['parent_geometry']['source_shape'] or not np.allclose(
                    np.asarray(source_grid['affine'])@reverse,small['parent_geometry']['source_affine'],rtol=0,atol=1e-4)):
                raise ValueError('ITK/NIfTI source identity or world geometry differs')
            values,teacher_grid,preprocessing=preprocess(image,max_voxels=LIMITS['max_source_or_resampled_voxels'])
            def tick(row):
                if torch.cuda.max_memory_reserved()>LIMITS['gpu_reserved_bytes']:raise ValueError('Teacher GPU reservation cap')
                if row['tile']%25==0 or row['tile']==row['total']:
                    resources()
                    with (root/'progress.jsonl').open('ab') as stream:stream.write(canonical(dict(case_id=name,**row)))
            remaining=min(LIMITS['max_tiles_per_case'],LIMITS['max_total_tiles']-total_tiles)
            probability,tiling=predict(values,teacher.lesion_probability,max_voxels=LIMITS['max_source_or_resampled_voxels'],max_tiles=remaining,tick=tick)
            total_tiles+=tiling['tiles'];del values
            native,mapping=reconstruct(probability,teacher_grid,small['geometry'],max_voxels=LIMITS['max_source_or_resampled_voxels']);del probability
            with np.load(array,allow_pickle=False) as data:target=data['target']
            if target.shape!=native.shape or target.dtype!=np.uint8:raise ValueError('Native target geometry')
            lesion=target==2;prediction=native>.5;intersection=int((lesion&prediction).sum())
            denominator=int(lesion.sum()+prediction.sum())
            record=write_member(PILOT_CACHE,name,native,identity_for(name,small,setup['common_identity']))
            members[name]=record
            # Labels choose only illustrative slices, never teacher inference tiles.
            display=normalize_region(np.transpose(sitk.GetArrayFromImage(image),(2,1,0)).astype(np.float32),
                small['parent_geometry'],small['region_low'],small['region_high']);del image
            support=lesion if lesion.any() else target>0
            anchor=[int(np.argmax(support.sum(axis=tuple(j for j in range(3) if j!=axis)))) for axis in range(3)]
            fig,axes=plt.subplots(2,3,figsize=(12,7))
            for axis in range(3):
                ct=np.take(display,anchor[axis],axis=axis).T;y=np.take(target,anchor[axis],axis=axis).T
                q=np.take(native,anchor[axis],axis=axis).T
                for ax in axes[:,axis]:ax.imshow(ct,cmap='gray',vmin=0,vmax=1,origin='lower');ax.axis('off')
                axes[0,axis].imshow(q,vmin=0,vmax=1,cmap='magma',alpha=.6,origin='lower')
                for mask,color in ((y>0,'cyan'),(y==2,'red'),(q>.5,'yellow')):
                    if mask.any() and not mask.all():axes[1,axis].contour(mask,levels=[.5],colors=[color],linewidths=.7)
                axes[0,axis].set_title(f'Probability, axis {axis}');axes[1,axis].set_title('GT pancreas cyan / lesion red / teacher yellow')
            fig.suptitle(name+' — TRAINING diagnostic, not independent validation');fig.tight_layout()
            figure=root/(name+'.png');fig.savefig(figure,dpi=110);plt.close(fig)
            report=dict(case_id=name,scope='training_teacher_diagnostic',seconds=time.monotonic()-began,
                target_lesion_voxels=int(lesion.sum()),teacher_positive_voxels=int(prediction.sum()),
                teacher_dice_at_half=None if denominator==0 else 2*intersection/denominator,
                teacher_recall_at_half=None if not lesion.any() else intersection/int(lesion.sum()),
                probability_strata={str(c):None if not (target==c).any() else float(native[target==c].mean()) for c in (0,1,2)},
                preprocessing=preprocessing,reconstruction=mapping,tiling=tiling,cache=record,
                figure=str(figure),figure_sha256=sha(figure),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved())
            write(root/(name+'.json'),report);reports.append(report);resources()
            del display,target,native,lesion,prediction,support
        if not all(torch.equal(state_before[k],v.detach().cpu()) for k,v in teacher.model.state_dict().items()):
            raise ValueError('Teacher weights mutated')
        write(PILOT_CACHE/'manifest.json',dict(schema=SCHEMA,complete=False,control_sha256=p.pin,members=members,qualification_only=True))
        write(root/'result.json',dict(completed=True,cases=reports,total_tiles=total_tiles,teacher_weights_unchanged=True,
            visual_review_required=True,quality_accepted=False,full_cache_authorized=False,scientific_updates=0,
            measured_pilot_cache_bytes=tree_bytes(PILOT_CACHE),full_cache_projection_not_a_guarantee=True))
    finally:p.close()


def pilot():
    from src.operations.full_training_platform import training_guard,watch_windows
    from scripts.diagnostics.setup_fast_varied import provider
    if (OUT/'pilot-01').exists() or PILOT_CACHE.exists():raise ValueError('Pilot already started; no retry/resume')
    check_preparation();resources();p=provider(prefetch=False)
    try:summary=normal_parent_gate(p.control['validation'])
    finally:p.close()
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        root=OUT/'pilot-01';root.mkdir(exist_ok=False)
        write(root/'request.json',dict(preparation_sha256=sha(OUT/'preparation.json'),limits=LIMITS,parent=summary,scientific=False))
        env=dict(os.environ,PROWL_DISTILLATION_PILOT='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
        env.pop('CUDA_VISIBLE_DEVICES',None)
        success=False;error=None
        with (root/'worker.log').open('x') as log:
            process=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            try:watch_windows(process,seconds=LIMITS['seconds'],rss_bytes=LIMITS['rss_bytes'],tick=resources);success=True
            except Exception as exc:error=repr(exc)
            finally:write(root/'resources.json',dict(getattr(process,'duration_resources',{}),success=success,exit_code=process.returncode,error=error))
        if not success:raise RuntimeError('Pilot failed; preserve evidence and request a decision')


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true');group.add_argument('--pilot',action='store_true');group.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.pilot:pilot()
    else:
        if os.environ.get('PROWL_DISTILLATION_PILOT')!='1':raise ValueError('Bounded supervisor required')
        pilot_worker()
