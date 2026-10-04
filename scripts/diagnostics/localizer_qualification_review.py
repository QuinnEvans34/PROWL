"""Review retained qualification inputs only; no arrays, permissions or hold removals."""
from copy import deepcopy
import json
from pathlib import Path
from uuid import uuid4

from scripts.diagnostics.followup_voxel_audit import Package
from src.data.annotation_contract_v2 import validate_approved_binary_lineage
from src.data.binary_label_policy import APPROVED_POLICY
from src.data.manifest_records import digest, canonical

REPO = Path(__file__).resolve().parents[2]
PARENT = REPO/'outputs/prowl/purpose-disposition-b515fd42-29b1-4203-9c62-424856fd523c'
CURRENT = REPO/'outputs/prowl/localizer-content-75d83d2d-cdca-4d57-be29-e7801a8b6b36'
PINS = {PARENT:'6ca6afc88ae7bdcf02458350908bf5a074c46d7c1f384f7f19d07666c759fd1e',
        CURRENT:'fe33fa752a49941b512919105528dd9e27a92e5b6da7a6ded15b90de8c2e8ccc'}


def run():
    checked={}
    for root,pin in PINS.items():
        receipt=(root/'verification.json').read_bytes()
        if digest(receipt)!=pin:raise ValueError('Receipt pin changed')
        refs=json.loads(receipt)['files']
        for name,sha in refs.items():
            p=root/name
            if not p.is_relative_to(root) or p.resolve(strict=True)!=p or digest(p.read_bytes())!=sha:
                raise ValueError('Unsafe or changed retained evidence')
        checked[str(root.relative_to(REPO))]=dict(receipt_sha256=pin,covered_files=len(refs))
    load=lambda name:[json.loads(line) for line in (PARENT/name).read_text().splitlines()]
    subjects=load('subjects.jsonl');studies=load('studies.jsonl');annotations=load('annotations.jsonl');issues=load('issues.jsonl')
    current={json.loads(p.read_text())['uri']:json.loads(p.read_text()) for p in CURRENT.glob('file-*.json')}
    approval_path=REPO/'docs/capstone/data/BINARY-DECODING-APPROVAL-2026-09-28.md'
    implementation_path=REPO/'src/data/binary_label_policy.py'
    approval=approval_path.read_bytes();implementation=implementation_path.read_bytes()
    approval_pin='3929e0e359d1aa1d4a5cc5a0066285699821ed648bbe87bfdcbc2bc2bead6de3'
    implementation_pin='ecdbe3e887c4b791f1079e81dcb22d804fda2e8c4b661c341ae422d90e6f4407'
    mapping=dict(status='approved',policy_id=APPROVED_POLICY,policy_sha256=implementation_pin,
        input_basis="nifti_scaled_semantic",kind="binary_zero_one_endpoints",
        canonical_foreground=1,absolute_tolerance=1e-6,relative_tolerance=0,
        approval_file=dict(root_alias='qualification_evidence',uri=approval_path.name,bytes=len(approval),
                           content_sha256=approval_pin,media_type='text/markdown'))
    results=[]
    for raw in ['PanTS_00000003','PanTS_00000026','PanTS_00000031']:
        sid='pants:study:'+raw
        study=next(s for s in studies if s['study_id']==sid)
        subject=next(s for s in subjects if s['subject_id']==study['subject_id'])
        annotation=next(a for a in annotations if a['study_id']==sid and a['structure']=='pancreas')
        for ref in [study['image'],annotation['file']]:
            if current[ref['uri']]['sha256']!=ref['content_sha256']:raise ValueError('Current file binding mismatch')
        audit_ref=annotation['label_encoding']['audit_file'];audit_bytes=(PARENT/audit_ref['uri']).read_bytes()
        if digest(audit_bytes)!=audit_ref['content_sha256']:raise ValueError('Audit pin mismatch')
        audit=json.loads(audit_bytes)
        if audit['ct']['file']!=study['image'] or audit['mask']['file']!=annotation['file']:
            raise ValueError('Audit source mismatch')
        values=annotation['label_encoding']['value_counts']
        if (audit['mask']['mask']['distinct_values_truncated'] or
            [[r['value'],r['count']] for r in values]!=audit['mask']['mask']['value_counts'] or
            annotation['label_encoding']['voxel_count']!=audit['mask']['voxels']['count']):
            raise ValueError('Incomplete or inconsistent value evidence')
        candidate=deepcopy(annotation);candidate['label_encoding']['mapping']=mapping
        validate_approved_binary_lineage(candidate,approval_bytes=approval,implementation_bytes=implementation,
            trusted_approval_sha256=approval_pin,trusted_implementation_sha256=implementation_pin)
        relevant={*subject['issue_ids'],*study['issue_ids'],*annotation['issue_ids']}
        holds=[i for i in issues if i['issue_id'] in relevant]
        if len(holds)!=3:raise ValueError('Unexpected candidate hold inventory')
        results.append(dict(study_id=sid,subject_sha256=digest(canonical(subject)),study_sha256=digest(canonical(study)),
            annotation_id=annotation['annotation_id'],annotation_sha256=digest(canonical(annotation)),
            holds=[dict(issue_id=i['issue_id'],rule_code=i['rule_code'],sha256=digest(canonical(i))) for i in holds],
            mapping_lineage='verified_against_retained_complete_counts',mapping_proposal=mapping,
            audit_sha256=digest(audit_bytes),retained_geometry=study['geometry'],
            retained_unit_interpretation=audit['unit_interpretation'],foreground_voxels=audit['mask']['mask']['nonzero_voxels'],
            alignment_review='pending',release_applicability='pending',purpose_use_decision='pending',
            source_readiness_assessment='pending',eligibility='not_granted',holds_removed=0))
    package=Package(REPO/'outputs/prowl'/('localizer-qualification-review-'+str(uuid4())),max_bytes=4*1024**2)
    package.write('inputs.json',checked)
    package.write('review.json',dict(status='partial_evidence_review_not_qualification',cases=results))
    package.write('implementation.json',dict(path=str(Path(__file__).relative_to(REPO)),text=Path(__file__).read_text()))
    package.write('verification.json',dict(status='review_complete',files=package.hashes.copy(),eligibility_granted=0,
                                           source_read=False,holds_removed=0))
    print(package.path)
    print('Receipt SHA256: '+digest((package.path/'verification.json').read_bytes()))


if __name__=='__main__':run()
