"""Bounded retained-evidence S3 qualification; not a production cohort publisher.

No raw arrays, external mount, training or registry writes. --check verifies/replays
without an output. --run preserves a new diagnostic package through the existing writer.
Budget: 10 minutes, 2 GiB observed process RSS, 96 MiB output, 100 GiB free floor.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import signal
from uuid import uuid4

from scripts.diagnostics.followup_voxel_audit import Package
from scripts.diagnostics.localizer_content_verify import load_spec, check_memory
from src.data.manifest_records import canonical, digest
from src.data.protected_identity import accepted_pants_members
from src.data.source_inventory_records import build_source_snapshot_v2, content_hash, require
from src.data.localizer_qualification_records import migrate_context, qualify_successor
from src.data.purpose_qualification import POLICY_SHA256, validate_qualification

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO/'outputs/prowl'
PACKAGES={
 'parent':('purpose-disposition-b515fd42-29b1-4203-9c62-424856fd523c','6ca6afc88ae7bdcf02458350908bf5a074c46d7c1f384f7f19d07666c759fd1e'),
 'metadata':('localizer-metadata-4c93efaa-f102-4bef-bae6-8966b3446d91','201342b56dd420783136a25c6faf278a224b68f904b1b56dd39278e458c1131b'),
 'content':('localizer-content-75d83d2d-cdca-4d57-be29-e7801a8b6b36','fe33fa752a49941b512919105528dd9e27a92e5b6da7a6ded15b90de8c2e8ccc'),
 'review':('localizer-qualification-review-8074e048-1340-44d7-8d60-51ab151641bd','d495032119c701e9ff3c709293426a110ccc5a2d07c5be004b973fe00d837b28'),
 'alignment':('localizer-alignment-8ae22f7e-f845-4865-aa8f-8219662f46c4','bc66dafbfc7e72ec4a259bc42416c6bcb16bfc83008153687e7cc3f07efca04f')}
CONTROLS={
 'docs/capstone/data/LOCALIZER-SOURCE-AND-ALIGNMENT-REVIEW-2026-09-28.md':'f093ed893d9bc2a6f93dc03fa1a2593abe291ef7e6f6a7b5046e62a71aa927c8',
 'docs/capstone/data/LOCALIZER-SOURCE-AND-ALIGNMENT-REVIEW-2026-09-28.json':'1306e768a2dc66c84fd920dfec46e75c8dc5747b89dd66f487991616b8a76755',
 'docs/capstone/data/SOURCE-VERIFICATION-SCOPE-2026-09-28.json':'8e1efd2ac3cc2c77fee4f4cf58f93ec69dcc61b2ab45341659b8744c8ddb8db6',
 'docs/capstone/data/BINARY-DECODING-APPROVAL-2026-09-28.md':'3929e0e359d1aa1d4a5cc5a0066285699821ed648bbe87bfdcbc2bc2bead6de3',
 'src/data/binary_label_policy.py':'ecdbe3e887c4b791f1079e81dcb22d804fda2e8c4b661c341ae422d90e6f4407'}
REVIEWED_MANIFESTS=[
 '8d2ab5715f949f98ce5c99a00b271dae1c375d2f3007b213f4f044a9814dd560',
 '031f62f2d7309a2afc63f550540a51b53f541175a429c3221fa941fd51927822',
 '9d4efefef4afc277fb813effa0346998c37d9bb6befb39d4e547b21b0ac3d9ee',
 '12ba8fe0a7013db13d06b0e0ea87ea949f167896bee9d2712b2d1d0f18d83220']
CASES=['pants:study:PanTS_00000003','pants:study:PanTS_00000026','pants:study:PanTS_00000031']


def read_pinned(path, sha):
    require(path.is_relative_to(REPO) and path.resolve(strict=True)==path and path.is_file(), 'Unsafe evidence path')
    require(path.stat().st_size<=8*1024**2, 'Evidence file exceeds read bound')
    payload=path.read_bytes()
    require(digest(payload)==sha, 'Evidence pin changed: '+path.name)
    return payload


def load_inputs():
    load_spec()  # Exact source-job controls, without opening any raw source.
    packages={}; pins={}; evidence={}
    for key,(name,sha) in PACKAGES.items():
        root=ROOT/name
        receipt=read_pinned(root/'verification.json',sha)
        refs=json.loads(receipt)['files']; files={}
        require(len(refs)<=100, 'Unexpected evidence inventory size')
        for name,pin in refs.items():
            require(not Path(name).is_absolute() and all(p not in ('', '.', '..') for p in name.split('/')), 'Unsafe package member')
            files[name]=read_pinned(root/name,pin)
        packages[key]=files
        pins[str((root/'verification.json').relative_to(REPO))]=sha
    for name,sha in CONTROLS.items():
        evidence[sha]=read_pinned(REPO/name,sha);pins[name]=sha
    scope=json.loads(evidence[CONTROLS['docs/capstone/data/SOURCE-VERIFICATION-SCOPE-2026-09-28.json']])
    for ref in scope['input_pins']:
        read_pinned(REPO/ref['path'],ref['sha256']);pins[ref['path']]=ref['sha256']
    bases={role:(REPO/'outputs/splits'/name).read_bytes() for role,name in
           [('train','train.txt'),('validation','val.txt'),('test','test.txt')]}
    protection=[]
    for role,payload in bases.items():
        for i in accepted_pants_members(payload,role):
            protection.append(dict(study_id=i.study_id,subject_id=i.subject_id,source_study_id=i.study_id.split(':')[-1],
                                   protected_role=role,protection_group_id=None))
    return packages,pins,evidence,bases,protection


def build():
    packages,pins,evidence,bases,protection=load_inputs()
    parent=packages['parent']
    prior={c:[json.loads(line) for line in parent[c+'.jsonl'].splitlines()]
           for c in ('subjects','studies','annotations','issues')}
    prior['snapshot']=json.loads(parent['source-snapshot.json'])
    metadata=json.loads(packages['metadata']['files.json'])
    require(len(metadata)==18000 and len(prior['issues'])==22, 'Unexpected retained inventory')
    content={v['uri']:v for name,data in packages['content'].items() if name.startswith('file-')
             for v in [json.loads(data)]}
    require(len(content)==10, 'Incomplete consumed-file verification')
    roles={r['study_id']:r['protected_role'] for r in protection}
    expected=[];observed=[]
    for row in metadata:
        require(roles[row['study_id']]==row['protected_role'] and row['protected_role']!='test', 'Inventory role mismatch')
        ref={k:row[k] for k in ('study_id','kind','uri')}; expected.append(ref)
        c=content.get(row['uri'])
        if c:require(c['bytes']==row['bytes'], 'Metadata/content size mismatch')
        observed.append(dict(**ref,state=row['state'],bytes=row['bytes'],sha256=None if c is None else c['sha256']))
    require({r['uri'] for r in metadata}>=set(content), 'Content evidence outside inventory')
    snapshot=build_source_snapshot_v2(source_version=prior['snapshot']['source_version'],license=prior['snapshot']['license'],
        root_alias=prior['snapshot']['root_alias'],study_ids=list(roles),expected_files=expected,observed_files=observed,
        control_sha256=content_hash(dict(pins=pins,assurance='staged_partial_integrity',test_scope='identity_only_no_payload')))
    stages=[migrate_context(prior=prior,snapshot=snapshot,protection=protection,base_membership_bytes=bases)]
    reviews=json.loads(packages['review']['review.json'])['cases']
    assessment=json.loads(evidence[CONTROLS['docs/capstone/data/LOCALIZER-SOURCE-AND-ALIGNMENT-REVIEW-2026-09-28.json']])
    require([r['study_id'] for r in reviews]==CASES==[r['study_id'] for r in assessment['cases']], 'Review scope changed')
    use_path='docs/capstone/data/LOCALIZER-SOURCE-AND-ALIGNMENT-REVIEW-2026-09-28.md'
    use_sha=CONTROLS[use_path]
    use_ref=dict(root_alias='qualification_evidence',uri=Path(use_path).name,bytes=len(evidence[use_sha]),
                 content_sha256=use_sha,media_type='text/markdown')
    provenance=dict(scope='publisher_protocol',release_applicability='confirmed',evidence_files=[use_ref],
                    allowed_use_decision_file=use_ref)
    qualifications=[];transitions=[]
    for review,assessment_case in zip(reviews,assessment['cases']):
        sid=review['study_id']
        s=next(s for s in prior['studies'] if s['study_id']==sid)
        a=next(a for a in prior['annotations'] if a['annotation_id']==review['annotation_id'])
        require(content_hash(a)==review['annotation_sha256'] and content_hash(s)==review['study_sha256'], 'Review binding changed')
        for kind,ref in [('ct',s['image']),('pancreas',a['file'])]:
            require(content[ref['uri']]['sha256']==ref['content_sha256']==assessment_case['source_files'][kind], 'Reviewed raw identity changed')
        audit_ref=a['label_encoding']['audit_file'];payload=parent[audit_ref['uri']]
        require(digest(payload)==audit_ref['content_sha256']==review['audit_sha256'], 'Mask audit changed')
        evidence[digest(payload)]=payload
        successor,q,certificate,evidence=qualify_successor(prior=stages[-1],study_id=sid,
            mapping=review['mapping_proposal'],provenance=provenance,evidence=evidence,base_membership_bytes=bases)
        stages.append(successor);qualifications.append(q);transitions.append(certificate)
        check_memory(2*1024**3)
    for q in qualifications:
        validate_qualification(q,trusted_qualification_sha256=content_hash(q),manifest=stages[-1],
            trusted_manifest_sha256=content_hash(stages[-1]),trusted_policy_sha256=POLICY_SHA256,
            evidence_by_sha256=evidence,trusted_evidence_sha256=set(evidence),base_membership_bytes=bases)
    require(len(stages[-1]['issues'])==13, 'Unexpected remaining hold count')
    return dict(inputs=pins,history=prior,manifests=stages,qualifications=qualifications,transitions=transitions,
        evidence={sha:data.decode('utf-8') for sha,data in evidence.items()},
        membership={role:data.decode() for role,data in bases.items()},
        scope=dict(status='s3_reviewed_qualification_not_production_cohort',qualified_studies=CASES,
                   remaining_active_holds=13,source_integrity='staged_partial_integrity',
                   test_scope='901 protected identities; no test payload observation',
                   purpose='private_noncommercial_pancreas_present_smoke',production_consumer_enabled=False,
                   proposed_two_case_members=CASES[:2],proposed_membership_frozen=False))


def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true');mode.add_argument('--run',action='store_true');args=parser.parse_args()
    def deadline(*_):raise TimeoutError('Qualification deadline exceeded')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(600)
    require(shutil.disk_usage(REPO).free>=100*1024**3, 'Internal free-space floor')
    result=build()
    if args.check:
        print(json.dumps(dict(manifest_sha256=[content_hash(m) for m in result['manifests']],scope=result['scope']),indent=2));return
    require([content_hash(m) for m in result['manifests']]==REVIEWED_MANIFESTS, 'Dry-run reviewed result changed')
    package=Package(ROOT/('localizer-qualified-'+str(uuid4())),max_bytes=96*1024**2)
    for name,value in result.items():package.write(name+'.json',value)
    package.write('implementation.json',{str(p.relative_to(REPO)):p.read_text() for p in
        [Path(__file__).resolve(),REPO/'src/data/localizer_qualification_records.py']})
    package.write('verification.json',dict(status='s3_qualification_complete_not_cohort_publication',files=package.hashes.copy(),
        qualified_count=3,training_started=False,production_consumer_enabled=False))
    print(package.path);print('receipt_sha256='+digest((package.path/'verification.json').read_bytes()))
    print('bytes='+str(package.used))


if __name__=='__main__':main()
