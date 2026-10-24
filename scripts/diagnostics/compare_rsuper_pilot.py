"""Matched descriptive comparison; exposed cases cannot establish independent accuracy."""
import json
from pathlib import Path


def paired_summary(baseline,candidate):
    if [r['case_id'] for r in baseline] != [r['case_id'] for r in candidate]:
        raise ValueError('Matched case order required')
    if len({r['case_id'] for r in baseline})!=len(baseline):raise ValueError('Duplicate cases')
    rows=[]
    for old,new in zip(baseline,candidate):
        if old['lesion_voxels']!=new['lesion_voxels']:raise ValueError('Original annotations differ')
        corrected=old['case_id']=='PanTS_00003059'
        n=0 if corrected else old['lesion_voxels']
        row=dict(case_id=old['case_id'],reference_voxels=n,corrected_negative=corrected)
        for label,r in [('baseline',old),('candidate',new)]:
            p=r['prediction_voxels']
            inter=0 if not n else round(r['recall']*n)
            if min(n,p,inter)<0 or inter>min(n,p):raise ValueError('Invalid voxel counts')
            row[label]=dict(dice=None if not n else 2*inter/(n+p),
                recall=None if not n else inter/n,predicted_voxels=p,
                false_positive_voxels=p-inter,false_negative_voxels=n-inter)
        rows.append(row)
    positive=[r for r in rows if r['reference_voxels']]
    if not positive:raise ValueError('Positive cases required')
    totals={label:dict(positive_macro_dice=sum(r[label]['dice'] for r in positive)/len(positive),
        positive_macro_recall=sum(r[label]['recall'] for r in positive)/len(positive),
        positive_cases_missed=sum(r[label]['recall']==0 for r in positive),
        negative_false_positive_voxels=sum(r[label]['false_positive_voxels'] for r in rows if not r['reference_voxels']))
        for label in ['baseline','candidate']}
    return dict(cases=rows,summary=totals,positive_cases=len(positive),negative_cases=len(rows)-len(positive),
        scope='fixed exposed training pilot with same local errata interpretation; not independent evaluation',
        teacher_qualified=False)


if __name__=='__main__':
    from scripts.diagnostics.qualify_distillation_mac import BASE,write
    from scripts.diagnostics.bind_mac_distillation_metadata import sha
    paths=[BASE/'patient-pilot-02',BASE/'rsuper-merlin-pilot-01']
    inputs=[]
    for path in paths:
        r=json.loads((path/'resources.json').read_text())
        assert r['success'] and r['workers_reaped']
        v=json.loads((path/'result.json').read_text());assert v['success'];inputs.append(v['cases'])
    result=paired_summary(*inputs)
    result['source_results']={str(p/'result.json'):sha(p/'result.json') for p in paths}
    write(paths[1]/'paired-comparison.json',result)
    print(json.dumps(result,indent=2))
