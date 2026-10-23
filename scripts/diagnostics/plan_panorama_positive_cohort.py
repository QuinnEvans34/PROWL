"""Metadata-only prospective roster. Never grants admission or opens CT/label payloads."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

BASE = Path('E:/PROWL/readiness/data-setup-20261010-a01')


def plan(catalog, audit):
    index={r['study_id']:r for r in audit}
    if len(index)!=len(audit) or len({r['study_id'] for r in catalog})!=len(catalog):
        raise ValueError('Duplicate study identity')
    if {r['study_id'] for r in catalog}!=set(index):
        raise ValueError('Catalog/audit members differ')
    eligible=[]
    for row in catalog:
        if row['disposition']!='expert_pdac_candidate_pending_qc_and_duplicates':continue
        if index[row['study_id']]['status']!='ct_content_pass_not_admitted':continue
        if row['lesion_method']!='human_manual' or row['pdac']!='positive' or not row['subject_id']:
            raise ValueError('Expert candidate semantics differ')
        if row.get('training_ready') or row.get('protected_role')!='unassigned':
            raise ValueError('Unexpected existing admission/role requires review')
        if row['ct']['expected_sha256']!=index[row['study_id']]['ct_sha256'] or row['label']['expected_sha256']!=index[row['study_id']]['label_sha256']:
            raise ValueError('Source hash evidence differs')
        eligible.append(dict(study_id=row['study_id'],subject_id=row['subject_id'],
            publisher_study_id=row['publisher_study_id'],ct_sha256=row['ct']['expected_sha256'],
            label_sha256=row['label']['expected_sha256'],training_ready=False,
            disposition='candidate_only_pending_overlap_qc_and_production_binding'))
    groups=Counter(r['subject_id'] for r in eligible)
    return dict(status='candidates_only_not_training_admission',studies=len(eligible),
        subjects=len(groups),repeated_subject_groups=sum(v>1 for v in groups.values()),
        upper_bound_added_subjects=len(groups),admitted=0,ct_payload_reads=0,label_payload_reads=0,
        selection_rule='Retain all eligible studies, grouped by source subject (D-030); no model-score selection',
        candidates=sorted(eligible,key=lambda r:(r['subject_id'],r['publisher_study_id'])))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    paths=[BASE/'panorama-candidates.jsonl',BASE/'panorama-ct-union-a01/cases.jsonl']
    contents=[path.read_bytes() for path in paths]
    report=plan(*[[json.loads(line) for line in content.splitlines()] for content in contents])
    report['evidence_sha256']={str(path):hashlib.sha256(content).hexdigest() for path,content in zip(paths,contents)}
    if report['studies']!=345 or report['subjects']!=344:raise ValueError('Candidate count differs; revise design before proceeding')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k!='candidates'}))


if __name__=='__main__':main()
