"""Read-only scientific retrospective and journal timing; no optimizer or inference."""
import json
from pathlib import Path
import sys
from collections import defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import sha256

RUN=Path('E:/PROWL/artifacts/pants_pancreas_region_24k_20261019')
CONTROL=Path('E:/PROWL/artifacts/pants_only_augmented_views_24k_win_20261017')
SETUP=Path('E:/PROWL/readiness/pancreas-region-20261019-a01')
OUT=Path('E:/PROWL/readiness/pancreas-region-review-20261022-a01')

def read(p):return json.loads(Path(p).read_text())
def events(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]

def summary(rows):
    m=[r['metrics'] for r in rows];pos=[r for r in m if r['reference_positive']];neg=[r for r in m if not r['reference_positive']]
    return dict(dice=float(np.mean([r['lesion']['dice'] for r in pos])),
        pancreas=float(np.mean([r['pancreas']['dice'] for r in m])),
        positive=len(pos),empty=len(neg),detected=sum(r['case_detected'] for r in pos),
        alarms=sum(r['false_alarm_any'] for r in neg),
        empty_voxels=sum(r['lesion']['predicted_voxels'] for r in neg),
        empty_mL=sum(r['predicted_volume_mm3'] for r in neg)/1000,
        positive_macro_recall=float(np.mean([r['lesion']['true_positive']/r['lesion']['target_voxels'] for r in pos])),
        components_detected=sum(r['detected_components'] for r in pos),components=sum(r['reference_components'] for r in pos))

def compare(control,treatment):
    a={r['case_id']:r['metrics'] for r in control};b={r['case_id']:r['metrics'] for r in treatment}
    if len(a)!=len(control) or len(b)!=len(treatment) or set(a)!=set(b):raise ValueError('Mismatched cases')
    for name in a:
        for key in ('reference_positive','reference_components','size_band','target_volume_mm3'):
            if a[name][key]!=b[name][key]:raise ValueError('Mismatched target semantics')
        for organ in ('lesion','pancreas'):
            if a[name][organ]['target_voxels']!=b[name][organ]['target_voxels']:raise ValueError('Mismatched native targets')
    pos=sorted(n for n in a if a[n]['reference_positive'])
    values=np.array([b[n]['lesion']['dice']-a[n]['lesion']['dice'] for n in pos])
    rng=np.random.default_rng(20261019)
    ci=np.quantile(values[rng.integers(len(pos),size=(10000,len(pos)))].mean(1),[.025,.975]).tolist()
    ca,cb=summary(control),summary(treatment)
    guards=dict(detection=(cb['detected']-ca['detected'])/36>=-.03,
        empty_alarm=(cb['alarms']-ca['alarms'])/34<=.03,
        pancreas=cb['pancreas']-ca['pancreas']>=-.02,empty_voxel_burden=cb['empty_voxels']<=ca['empty_voxels'])
    delta=float(values.mean());accepted=delta>=.02 and ci[0]>0 and all(guards.values())
    rejected=not all(guards.values()) or ci[1]<.02
    bands={}
    for band in sorted({a[n]['size_band'] for n in pos}):
        ns=[n for n in pos if a[n]['size_band']==band]
        bands[band]=dict(cases=len(ns),control=float(np.mean([a[n]['lesion']['dice'] for n in ns])),
                        treatment=float(np.mean([b[n]['lesion']['dice'] for n in ns])))
    return dict(delta=delta,ci95=ci,seed=20261019,bootstrap_replicates=10000,
        null='reject' if ci[0]>0 else 'fail_to_reject',
        practical='accept' if accepted else 'reject' if rejected else 'inconclusive',
        guards=guards,control=ca,treatment=cb,size_bands=bands,
        improved=int((values>0).sum()),worsened=int((values<0).sum()),unchanged=int((values==0).sum()))

def timing(rows):
    updates=[r for r in rows if r['event']=='update']
    last=rows[-1];total=last.get('elapsed_seconds',last.get('training_seconds',updates[-1]['elapsed_seconds']))
    duration_source='completed_event' if ('elapsed_seconds' in last or 'training_seconds' in last) else 'last_update_lower_bound'
    phases=[];native_start=None;last_update=None;training_end=None;tensor_seconds=0.
    for r in rows:
        if r['event']=='update':last_update=r
        elif r['event']=='native_started':native_start=r['elapsed_seconds']
        elif r['event']=='native_completed' and native_start is not None:
            phases.append(dict(step=r['step'],seconds=r['elapsed_seconds']-native_start));native_start=None
        elif r['event']=='validation' and 'utc_ms' in r and last_update and 'utc_ms' in last_update:
            tensor_seconds+=(r['utc_ms']-last_update['utc_ms'])/1000
        elif r['event']=='training_completed':training_end=r['elapsed_seconds']
    native_seconds=sum(r['seconds'] for r in phases)
    post_native=total-training_end if training_end is not None and not phases else 0.
    diffs=[];by_case=defaultdict(list);segments=defaultdict(list)
    for prev,nxt in zip(updates,updates[1:]):
        # Exclude checkpoint/validation boundaries; the remainder still includes IO,
        # CPU transforms, GPU work, logging and occasional resource checks.
        if prev['step']%500==0:continue
        delta=nxt['elapsed_seconds']-prev['elapsed_seconds'];diffs.append(delta)
        by_case[nxt['member_id']].append(delta);segments[(nxt['step']-1)//2000].append(delta)
    return dict(updates=len(updates),total_hours=total/3600,duration_source=duration_source,
        native_during_training_hours=native_seconds/3600,tensor_validation_hours=tensor_seconds/3600,
        post_training_native_hours=post_native/3600,
        outside_recorded_validation_hours=(total-native_seconds-tensor_seconds-post_native)/3600,
        native_blocks=phases,regular_update_interval_seconds=dict(mean=float(np.mean(diffs)),
            median=float(np.median(diffs)),p95=float(np.quantile(diffs,.95)),p99=float(np.quantile(diffs,.99)),maximum=max(diffs)),
        segment_medians=[dict(end_step=(i+1)*2000,median=float(np.median(v))) for i,v in sorted(segments.items())],
        case_mean_seconds={n:float(np.mean(v)) for n,v in by_case.items()})

def main():
    if OUT.exists():raise ValueError('Review output already exists; inspect it, no overwrite')
    current=events(RUN/'execution/history.jsonl');old=events(CONTROL/'execution/history.jsonl')
    if current[-1]['event']!='completed' or [r['step'] for r in current if r['event']=='update']!=list(range(1,24001)):
        raise ValueError('Incomplete scientific run')
    if not read(SETUP/'scientific-resources.json')['workers_reaped']:raise ValueError('Workers not reaped')
    pins=read(SETUP/'ready.json')['pins']
    changed=[p for p,h in pins.items() if sha256(p)!=h]
    if changed:raise ValueError('Parent producing pins changed: '+str(changed))
    next_pins=read('E:/PROWL/readiness/varied-focus-20261022-a01/setup.json')['pins']
    if any(sha256(p)!=h for p,h in next_pins.items()):raise ValueError('Successor producing pins changed')
    reports={e:read(RUN/f'execution/native-{e}.json') for e in ('selected','terminal')}
    controls={e:read(CONTROL/f'execution/native-{e}.json') for e in ('selected','terminal')}
    dev=set((RUN/'splits/development_ids.txt').read_text().split());curve=[]
    for step in range(2000,24001,2000):
        report=read(RUN/f'execution/native-{step:06d}.json')
        if len(report['cases'])!=70 or {r['case_id'] for r in report['cases']}!=dev:raise ValueError('Incomplete development')
        curve.append(dict(step=step,**summary(report['cases'])))
    if reports['selected']['step']!=max(curve,key=lambda r:r['dice'])['step']:raise ValueError('Wrong selection')
    backup=Path('C:/Users/quinn/PROWL-Backups')/RUN.name
    paths=sorted((RUN/'execution').glob('*.pt'))+sorted((RUN/'execution').glob('native-*.json'))
    mismatches=[p.name for p in paths if sha256(p)!=sha256(backup/p.name)]
    if mismatches:raise ValueError('Backup mismatch: '+str(mismatches))
    source_journal=RUN/'execution/history.jsonl';backup_journal=backup/'history.jsonl'
    backup_rows=events(backup_journal)
    journal_note=dict(exact_sha256_match=sha256(source_journal)==sha256(backup_journal),
        source_last_event=current[-1]['event'],backup_last_event=backup_rows[-1]['event'],
        backup_is_exact_byte_prefix=source_journal.read_bytes().startswith(backup_journal.read_bytes()),
        missing_tail_events=len(current)-len(backup_rows))
    counts=defaultdict(lambda:dict(updates=0,lesion_visible=0))
    for r in current:
        if r['event']=='update':
            kind=r['input_view']['window']['kind'];counts[kind]['updates']+=1
            counts[kind]['lesion_visible']+=r['input_view']['augmentation']['class_counts'][2]>0
    times={'current':timing(current),'augmented_control':timing(old)}
    for name in ('pants_course_reference_dicefocal_24k_20261011','pants_plus_expert_panorama_dicefocal_24k_20261012'):
        times[name]=timing(events(Path('E:/PROWL/artifacts')/name/'execution/history.jsonl'))
    result=dict(primary=compare(controls['selected']['cases'],reports['selected']['cases']),
        secondary=compare(controls['terminal']['cases'],reports['terminal']['cases']),native_curve=curve,timing=times,
        input_visibility=dict(counts),verified_parent_pins=len(pins),verified_successor_pins=len(next_pins),
        checkpoint_and_native_backups_match=True,backup_journal=journal_note,
        evidence_sha256={str(p):sha256(p) for p in [source_journal,SETUP/'ready.json',* [RUN/f'execution/native-{e}.json' for e in ('selected','terminal')]]},
        review_code_sha256=sha256(__file__),review_optimizer_updates=0,review_inference_calls=0,review_CT_reads=0)
    OUT.mkdir()
    with (OUT/'results.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    concise=dict(result);concise['timing']={k:{a:b for a,b in v.items() if a not in ('case_mean_seconds','native_blocks','segment_medians')} for k,v in times.items()}
    print(json.dumps(concise,indent=2),flush=True)

if __name__=='__main__':main()
