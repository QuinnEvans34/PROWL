"""Read-only batch integrity and exploratory summary; no source CT, labels or models."""
import json,hashlib,sys
from pathlib import Path
BASE=Path('E:/PROWL/readiness/week05-four-case-20261102-a01')
BACKUP=Path('C:/Users/quinn/PROWL-Backups/week05-four-case-20261102-a01')

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()

def main():
    if (BASE/'summary.json').exists():raise FileExistsError('Summary already exists')
    completion=json.loads((BASE/'completion.json').read_text());request=json.loads((BASE/'request.json').read_text())
    assert completion['status']=='COMPLETED_EXPLORATORY_EXCEPTION'
    assert completion['cases']==[c['case_id'] for c in request['cases']]
    pairs=[]
    for p in BASE.rglob('*'):
        if not p.is_file():continue
        h=sha(p);assert h==sha(BACKUP/p.relative_to(BASE));pairs.append(dict(path=str(p.relative_to(BASE)),sha256=h))
    rows=[];runtime=0
    for arm in completion['arms']:
        for name in completion['cases']:
            out=BASE/name/arm
            res=json.loads((out/'result.json').read_text());score=json.loads((out/'score.json').read_text());access=json.loads((out/'input-access.json').read_text())
            assert res['status']=='COMPLETED' and res['request_sha256']==sha(BASE/'request.json')
            assert access['ct_reads']>0 and not access['lesion_reference_loaded'] and access['pancreas_reference_loaded']==(arm=='provided_region')
            for suffix in ('','-score'):
                resource=json.loads((BASE/(name+'-'+arm+suffix+'.resources.json')).read_text())
                assert resource['success'] and resource['exit_code']==0 and resource['workers_reaped']
                runtime+=resource['seconds']
            m=score['metrics']['lesion'];comp=score['lesion_components']
            assert sum(x['voxels'] for x in comp['reference'])==m['reference_voxels']
            assert sum(x['overlap_voxels'] for x in comp['reference'])==m['true_positive']
            rows.append(dict(case_id=name,arm=arm,lesion_dice=m['dice'],voxel_recall=m['recall'],false_positive_ml=m['false_positive_ml'],
                lesion_components_hit=comp['reference_hit_count'],lesion_components_total=comp['reference_count'],false_positive_components=comp['false_positive_components'],
                pancreas_union_dice=score['metrics']['pancreas_lesion_union']['dice'],pancreas_parenchyma_dice=score['metrics']['pancreas_parenchyma']['dice'],
                lesion_contour=score['lesion_contour'],localization=score['localization'],seconds=res['seconds'],peak_gpu_reserved=res['peak_gpu_reserved']))
    aggregate={}
    for arm in completion['arms']:
        selected=[r for r in rows if r['arm']==arm];positive=[r['lesion_dice'] for r in selected if r['lesion_dice'] is not None]
        aggregate[arm]=dict(cases=len(selected),positive_dice_count=len(positive),mean_positive_lesion_dice=sum(positive)/len(positive) if positive else None,
            reference_components=sum(r['lesion_components_total'] for r in selected),hit_components=sum(r['lesion_components_hit'] for r in selected),false_positive_components=sum(r['false_positive_components'] for r in selected))
    result=dict(status='COMPLETE_EXPLORATORY_EXCEPTION_NOT_ACCEPTANCE',probability_equivalence='UNQUALIFIED',request_sha256=sha(BASE/'request.json'),rows=rows,
        aggregate=aggregate,backup_verified_files=len(pairs),backup_pairs=pairs,supervised_worker_seconds=runtime,training_hours_added=0,
        interpretation='Four exposed-development cases only; provided-region arm is reference-assisted and cannot be credited as autonomous performance')
    text=json.dumps(result,indent=2,allow_nan=False)
    with (BASE/'summary.json').open('x') as f:f.write(text)
    with (BACKUP/'summary.json').open('x') as f:f.write(text)
    assert sha(BASE/'summary.json')==sha(BACKUP/'summary.json')
    print(json.dumps({k:v for k,v in result.items() if k!='backup_pairs'}))

if __name__=='__main__':main()
