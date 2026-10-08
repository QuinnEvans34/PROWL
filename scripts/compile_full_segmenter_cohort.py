#!/usr/bin/env python3
"""Freeze the technically accepted development cohort after a complete preprocessing pass.

Empty annotation files remain reference_empty, never verified healthy. Failed cases are
listed explicitly and excluded; original protected split files are never modified.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.training import experiment_config as E
from src.data.source_inventory_records import require


def compile_cohort(config, audit, output):
    cfg=E.load_experiment(config);cohort=cfg['_experiment']['cohort'];audit=Path(audit);output=Path(output)
    summary=json.loads((audit/'summary.json').read_text())
    resources=json.loads((audit/'resources.json').read_text())
    require(summary['completed'] and resources['workers_reaped'] and summary['optimizer_updates']==0
        and summary['model_forwards']==0 and summary['cohort_accepted'] is False, 'Completed preparation required')
    source=json.loads((audit/'input-control.json').read_text());cache=Path(summary['cache'])
    require(source['domain']=='candidate_audit_only' and (cache/'control.json').read_bytes()==
        (audit/'input-control.json').read_bytes(), 'Cache/control mismatch')
    require(source['geometry']==cfg['full_segmenter']['geometry'] and
        source['manifest_sha256']==E.sha256(E.resolve(cohort['manifest'])), 'Preparation configuration differs')
    records=[json.loads(s) for s in (audit/'cases.jsonl').read_text().splitlines()]
    expected=source['train']+source['validation'];by_id={r['case_id']:r for r in records}
    require(len(records)==len(by_id)==len(expected) and set(by_id)==set(expected), 'Incomplete/duplicate content ledger')
    require(all(r['status'] in ('technical_pass','technical_failure') for r in records) and
        sum(r['status']=='technical_pass' for r in records)==summary['passed'] and
        sum(r['status']=='technical_failure' for r in records)==summary['failed'], 'Content summary mismatch')
    require(all(by_id[n]['role']==('train' if n in source['train'] else 'validation') for n in expected), 'Role drift')
    selected={role:[n for n in source[role] if by_id[n]['status']=='technical_pass'] for role in ('train','validation')}
    require(selected['train'] and selected['validation'] and
        any(source['target_states'][n]=='positive' for n in selected['validation']), 'Useful train/development cohort required')
    names=selected['train']+selected['validation'];members={}
    for name in names:
        path=cache/(name+'.json');meta=json.loads(path.read_text())
        require(meta['case_id']==name and meta['control_sha256']==E.sha256(cache/'control.json') and
            meta['fidelity']['mechanical_survival_pass'], 'Content/fidelity record mismatch')
        members[name]=dict(cache_sha256=meta['cache_sha256'],metadata_sha256=E.sha256(path))
    output.mkdir(parents=True,exist_ok=False)
    for role,filename in [('train','train.txt'),('validation','development.txt')]:
        (output/filename).write_text('\n'.join(selected[role])+'\n')
    # Keep the original candidate manifest; selected role files explicitly determine consumption.
    cohort.update(train_ids=str(output/'train.txt'),development_ids=str(output/'development.txt'))
    pins={k:E.sha256(E.resolve(cohort[k])) for k in ('manifest','train_ids','development_ids',
          'original_train_ids','original_development_ids','test_ids')}
    review=dict(decision='accepted',scope='development_experiment_using_published_reference_annotations',
        input_sha256=pins,target_states={n:source['target_states'][n] for n in names},
        empty_reference_policy='annotation_background_not_verified_healthy',
        prepared_cache=dict(root=str(cache),control_sha256=E.sha256(cache/'control.json'),members=members),
        evidence=[str(audit/'summary.json'),str(audit/'input-control.json'),str(audit/'cases.jsonl')],
        evidence_sha256={str(audit/n):E.sha256(audit/n) for n in ('summary.json','input-control.json','cases.jsonl')},
        exclusions=[by_id[n] for n in expected if by_id[n]['status']!='technical_pass'],
        limitations=['Technical data/geometry acceptance is not expert annotation adjudication.',
                     'Empty references are annotation-background targets, not confirmed healthy patients.',
                     'Provided-pancreas ROI and tensor-grid development selection are not the full PanTS benchmark.'])
    review_path=output/'cohort-review.json';review_path.write_text(json.dumps(review,indent=2)+'\n')
    import yaml
    spec=cfg['_experiment'];spec['cohort']['review']=str(review_path)
    (output/'experiment.yaml').write_text(yaml.safe_dump(spec,sort_keys=False))
    result=dict(train_cases=len(selected['train']),development_cases=len(selected['validation']),
        excluded=len(review['exclusions']),experiment=str(output/'experiment.yaml'))
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True);p.add_argument('--audit',required=True);p.add_argument('--output',required=True)
    print(json.dumps(compile_cohort(**vars(p.parse_args())),indent=2))
