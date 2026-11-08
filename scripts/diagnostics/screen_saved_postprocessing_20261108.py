"""CPU-only follow-up; all candidates use fixed saved masks, no model execution."""
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from statistics import mean
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
DEPS='/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies'
sys.path[:0]=[str(ROOT),DEPS]
BASE=Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-confidence-mac-20261108')
SOURCE=BASE/'screen-03';AUDIT=BASE/'component-audit-02'
OUT=BASE/'postprocess-screen-01'
BACKUP=Path.home()/'PROWL-Backups/stunet-postprocess-screen-20261108-01'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def safety():
    from src.operations.full_training_platform import require_ac
    require_ac()
    if shutil.disk_usage(Path.home()).free<50_000_000_000 or shutil.disk_usage(BASE).free<100*1024**3:
        raise ValueError('Existing free-space floor')
    if sum(p.stat().st_size for p in (Path.home()/'PROWL-Backups').rglob('*') if p.is_file())>26*1024**3:
        raise ValueError('Existing total backup cap')
    output=subprocess.check_output(['memory_pressure','-Q'],text=True)
    if int(re.search(r'free percentage: (\d+)%',output).group(1))<10:raise ValueError('Memory-pressure floor')


def summarize(rows,names):
    if len(rows)!=70 or len({r['case_id'] for r in rows})!=70:raise ValueError('Incomplete/duplicate cohort')
    result={}
    for name in names:
        m=[r['policies'][name] for r in rows];pos=[x for x in m if x['reference_positive']]
        empty=[x for x in m if not x['reference_positive']];small=[x for x in pos if x['target_volume_mm3']<1000]
        if (len(pos),len(empty),len(small),sum(x['reference_components'] for x in m))!=(36,34,5,45):
            raise ValueError('Reference denominator drift')
        precision=[x['lesion']['true_positive']/x['lesion']['predicted_voxels'] for x in pos if x['lesion']['predicted_voxels']]
        result[name]=dict(positive_macro_dice=mean(x['lesion']['dice'] for x in pos),
            positive_macro_recall=mean(x['lesion']['true_positive']/x['lesion']['target_voxels'] for x in pos),
            small_case_macro_recall=mean(x['lesion']['true_positive']/x['lesion']['target_voxels'] for x in small),
            positive_macro_precision_defined=mean(precision) if precision else None,precision_defined_cases=len(precision),
            pancreas_macro_dice=mean(x['pancreas']['dice'] for x in m),
            detected_cases=sum(x['case_detected'] for x in pos),detected_components=sum(x['detected_components'] for x in pos),
            empty_alarm_cases=sum(x['false_alarm_any'] for x in empty),
            false_positive_voxels=sum(x['lesion']['predicted_voxels']-x['lesion']['true_positive'] for x in m),
            false_positive_mL=sum((x['lesion']['predicted_voxels']-x['lesion']['true_positive'])*x['voxel_mm3']/1000 for x in m),
            false_negative_voxels=sum(x['lesion']['target_voxels']-x['lesion']['true_positive'] for x in pos))
    guards={}
    for name in names[1:]:
        a,b=result['raw'],result[name]
        lost_cases=[r['case_id'] for r in rows if r['policies']['raw']['case_detected'] and not r['policies'][name]['case_detected']]
        lost_components=[dict(case_id=r['case_id'],component_id=i) for r in rows for i in sorted(set(r['policies']['raw']['hit_component_ids'])-set(r['policies'][name]['hit_component_ids']))]
        checks=dict(dice_gain_at_least_02=b['positive_macro_dice']-a['positive_macro_dice']>=.02-1e-12,
            no_lost_cases=not lost_cases,no_lost_components=not lost_components,
            small_recall_unchanged=b['small_case_macro_recall']>=a['small_case_macro_recall']-1e-12,
            overall_recall_within_01=b['positive_macro_recall']>=a['positive_macro_recall']-.01-1e-12,
            pancreas_dice_within_01=b['pancreas_macro_dice']>=a['pancreas_macro_dice']-.01-1e-12,
            empty_alarms_nonincrease=b['empty_alarm_cases']<=a['empty_alarm_cases'],
            fp_volume_nonincrease=b['false_positive_mL']<=a['false_positive_mL']+1e-12)
        incumbent=result['near10']
        extra=dict(dice_delta_from_near10=b['positive_macro_dice']-incumbent['positive_macro_dice'],
            recall_delta_from_near10=b['positive_macro_recall']-incumbent['positive_macro_recall'],
            small_recall_delta_from_near10=b['small_case_macro_recall']-incumbent['small_case_macro_recall'],
            fp_mL_delta_from_near10=b['false_positive_mL']-incumbent['false_positive_mL'])
        guards[name]=dict(passes_raw_guards=all(checks.values()),checks=checks,lost_cases=lost_cases,lost_components=lost_components,**extra)
    eligible=[n for n in names[1:] if guards[n]['passes_raw_guards']]
    leader=max(eligible,key=lambda n:result[n]['positive_macro_dice']) if eligible else 'raw'
    return dict(policies=result,guards=guards,development_screen_leader=leader,
                interpretation='All nine policies reported; exploratory reused development cohort, no deployment or independent confirmation')


def worker():
    import nibabel as nib
    import numpy as np
    from scipy import ndimage
    from src.data.segmenter_content_v1 import target_content
    from src.inference.saved_postprocess_screen_v1 import predictions,POLICIES
    from src.inference.lesion_confidence_screen_v2 import unpack
    request=json.loads((OUT/'request.json').read_text())
    for p,h in request['pins'].items():
        if sha(p)!=h:raise ValueError('Source pin drift')
    original=json.loads((SOURCE/'result.json').read_text());old={x['case_id']:x for x in original['cases']}
    audit=json.loads((AUDIT/'result.json').read_text());components={x['case_id']:x for x in audit['cases']}
    rows=[]
    for index,case in enumerate(request['cases']):
        name=case['case_id'];source_row=old[name];masks={}
        for kind in ('lesion','pancreas'):
            source=case['sources'][kind]
            if sha(source['path'])!=source['sha256']:raise ValueError('Reference source drift')
            obj=nib.load(source['path'])
            if list(obj.shape)!=case['native_shape'] or not np.allclose(obj.affine,case['native_affine'],atol=1e-5,rtol=0):raise ValueError('Reference geometry drift')
            masks[kind],_=target_content(obj.dataobj.get_unscaled(),dict(slope=float(obj.dataobj.slope),intercept=float(obj.dataobj.inter)))
        lesion=masks['lesion'];pancreas=(masks['pancreas']!=0)&(lesion==0)
        ref_components,nref=ndimage.label(lesion,structure=np.ones((3,3,3)))
        nlesion=int(lesion.sum());npancreas=int(pancreas.sum());volume=abs(float(np.linalg.det(np.asarray(case['native_affine'])[:3,:3])))
        if sha(SOURCE/(name+'.npz'))!=source_row['artifact']['sha256']:raise ValueError('Mask artifact drift')
        with np.load(SOURCE/(name+'.npz'),allow_pickle=False) as f:code=unpack(f['packed'],[int(x) for x in f['shape']])
        row=dict(case_id=name,policies={},mask_sha256={})
        for policy,prediction in predictions(code,case['native_affine'],components[name]['components']):
            guess=prediction==2;p=int(guess.sum());t=int(np.count_nonzero(guess&lesion));hit=np.unique(ref_components[guess]);hit=hit[hit!=0]
            pg=prediction==1;pp=int(pg.sum());pt=int(np.count_nonzero(pg&pancreas))
            m=dict(lesion=dict(target_voxels=nlesion,predicted_voxels=p,true_positive=t,dice=2*t/(nlesion+p) if nlesion+p else None),
                pancreas=dict(target_voxels=npancreas,predicted_voxels=pp,true_positive=pt,dice=2*pt/(npancreas+pp) if npancreas+pp else None),
                reference_positive=bool(nlesion),reference_components=int(nref),case_detected=bool(len(hit)),
                detected_components=len(hit),hit_component_ids=hit.tolist(),false_alarm_any=not nlesion and p>0,
                voxel_mm3=volume,target_volume_mm3=nlesion*volume)
            row['policies'][policy]=m;row['mask_sha256'][policy]=hashlib.sha256(prediction.tobytes()).hexdigest()
            if policy=='raw':
                if m['lesion']!=source_row['policies']['0.0']['lesion'] or m['pancreas']!=source_row['policies']['0.0']['pancreas'] or row['mask_sha256'][policy]!=source_row['mask_sha256']['0.0']:raise ValueError('Raw replay/count drift')
            if policy=='near10' and m['lesion']!=components[name]['policies']['near_predicted_pancreas_10mm']['lesion']:raise ValueError('Incumbent drift')
            del prediction,guess,pg
        if tuple(row['policies'])!=POLICIES:raise ValueError('Incomplete fixed policy grid')
        write(OUT/(name+'.json'),row);rows.append(row)
        del masks,lesion,pancreas,ref_components,code;gc.collect()
        print(json.dumps(dict(completed=index+1,total=70,case_id=name)),flush=True)
    report=summarize(rows,POLICIES)
    for p,h in request['pins'].items():
        if sha(p)!=h:raise ValueError('Source pin changed')
    report.update(schema='prowl.saved-postprocess-screen.20261108.v1',request_sha256=sha(OUT/'request.json'),cases=rows,
                  no_model_forwards=True,no_optimizer_updates=True,no_ct_reads=True)
    write(OUT/'result.json',report)


def main():
    if '--worker' in sys.argv:return worker()
    from src.inference.saved_postprocess_screen_v1 import POLICIES
    safety();OUT.mkdir(exist_ok=False);BACKUP.mkdir(exist_ok=False)
    source=json.loads((SOURCE/'request.json').read_text())
    pinpaths=[Path(__file__),ROOT/'src/inference/saved_postprocess_screen_v1.py',ROOT/'tests/test_saved_postprocess_screen_v1.py',
        ROOT/'docs/capstone/operations/STUNET-POSTPROCESS-SCREEN-20261108.md',ROOT/'src/inference/lesion_confidence_screen_v2.py',
        ROOT/'src/data/segmenter_content_v1.py',SOURCE/'request.json',SOURCE/'result.json',AUDIT/'result.json']
    write(OUT/'request.json',dict(cases=source['cases'],policies=POLICIES,pins={str(p):sha(p) for p in pinpaths},
        seconds=1800,rss_bytes=8*1024**3,threads=1,prior_studies_seen=True,scope='New user-authorized exploratory fixed nine-policy CPU study; no model/CT/training'))
    from src.operations.mac_teacher_supervision_v3 import run
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONPATH=str(ROOT)+':'+DEPS)
    ok=run([sys.executable,str(Path(__file__).resolve()),'--worker'],OUT,seconds=1800,rss_bytes=8*1024**3,tick=safety,env=env)
    for path in OUT.glob('*.json'):
        safety();shutil.copyfile(path,BACKUP/path.name)
        if sha(path)!=sha(BACKUP/path.name):raise ValueError('Independent backup mismatch')
    if not ok:raise SystemExit('Preserve failure; no automatic retry')
    print('COMPLETE',OUT)


if __name__=='__main__':main()
