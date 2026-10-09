"""Bind a verified private Mac handoff to local Windows paths; no source decoding."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import yaml

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import load_experiment


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--handoff',type=Path,required=True)
    p.add_argument('--verification',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); h=args.handoff; out=args.output
    summary=json.loads((args.verification/'summary.json').read_text())
    assert summary['passed'] and summary['cases']==1408
    assert summary['source_inventory_sha256']==hashlib.sha256((h/'metadata/source-file-hashes.json').read_bytes()).hexdigest()
    verified=[json.loads(s) for s in (args.verification/'ct-verification.jsonl').read_text().splitlines()]
    by_id={r['case_id']:r for r in verified}
    assert len(verified)==len(by_id)==1408 and all(r['passed'] and r['sha256']==r['expected_sha256'] for r in verified)
    with (h/'metadata/admitted-portable-manifest.csv').open(newline='') as stream: original=list(csv.DictReader(stream))
    assert len(original)==1408 and {r['case_id'] for r in original}==set(by_id)
    rows=[]
    for r in original:
        rows.append(dict(case_id=r['case_id'],protected_role=r['protected_role'],
            ct_path=by_id[r['case_id']]['path'],pancreas_path=str(h/r['pancreas_relative']),
            lesion_path=str(h/r['lesion_relative']),historical_has_lesion=str(r['target_state']=='positive'),
            target_state=r['target_state']))
    out.mkdir(parents=True,exist_ok=False)
    with (out/'manifest.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    spec=yaml.safe_load((h/'configs/mac-original.yaml').read_text())
    spec['name']='full_segmenter_suprem_lenovo_8h_01'
    spec['base_config']=str(ROOT/'configs/level45.yaml')
    spec['recipe']['device']='cuda'; full=spec['recipe']['full_segmenter']
    full.update(output_dir='E:/PROWL/artifacts/'+spec['name'],cache_dir='E:/PROWL/cache/lenovo-8h-01',
        backup_dir='C:/Users/quinn/PROWL-Backups',backup_cap_bytes=26*1024**3)
    full['session']['lr_horizon_steps']=24000
    spec['run'].update(max_updates=1000000,target_seconds=28800,max_seconds=32400)
    spec['cohort']=dict(manifest=str(out/'manifest.csv'),train_ids=str(h/'splits/admitted/train.txt'),
        development_ids=str(h/'splits/admitted/development.txt'),original_train_ids=str(h/'splits/original/train.txt'),
        original_development_ids=str(h/'splits/original/val.txt'),test_ids=str(h/'splits/original/test.txt'),review=None)
    spec['initialization'].update(checkpoint=str(h/'weights/supervised_suprem_segresnet_2100.pth'),
        source_review=str(h/'metadata/suprem-development-source-review.json'))
    cfg=out/'candidate.yaml';cfg.write_text(yaml.safe_dump(spec,sort_keys=False))
    load_experiment(cfg)
    (out/'ancestry.json').write_text(json.dumps(dict(handoff=str(h),verification=str(args.verification),
        original_manifest_sha256=hashlib.sha256((h/'metadata/admitted-portable-manifest.csv').read_bytes()).hexdigest(),
        purpose='new_windows_observations_required_not_training_admission'),indent=2)+'\n')
    print(cfg)


if __name__=='__main__': main()
