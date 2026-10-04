"""Prepare, publish, or independently resolve the approved first localizer cohort.

Only metadata artifacts are written. No raw source reads, model runs, or global alias changes.
Prepare writes a new ignored local candidate. Publish requires its externally retained plan pin.
"""
import argparse
import json
from pathlib import Path
from uuid import uuid4

from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data.cohort_registry import build_bundle,validate_bundle,resolve_inputs,COHORT_ID
from src.operations.storage_roots import cohort_store

REPO=Path(__file__).resolve().parents[2]
S3=REPO/'outputs/prowl/localizer-qualified-4123a108-7f14-453a-a741-e46d62344562'
S3_PIN='7018583fa42310a4a179efc0d5570eebb605a4b2d49c2f9883c33315b43872b2'
MANIFEST_PIN='12ba8fe0a7013db13d06b0e0ea87ea949f167896bee9d2712b2d1d0f18d83220'
CAP=REPO/'docs/capstone/operations/COHORT-PUBLICATION-CAPABILITY-2026-09-28.json'
CAP_PIN='b8be9d3e20d108eade87282e067f9f6f2fa4eeb87c39a681999f4534a64c0136'
CODE=['src/operations/artifact_store.py','src/operations/storage_roots.py','src/data/cohort_registry.py',
      'src/data/cohort_records.py','src/data/qualification_transition.py','src/data/localizer_qualification_records.py',
      'src/data/purpose_qualification.py','src/data/manifest_records_v3.py','src/data/source_inventory_records.py',
      'src/data/protected_identity.py','src/data/manifest_records.py','src/data/annotation_contract_v2.py',
      'scripts/diagnostics/freeze_localizer_cohort.py']


def code_pins():
    paths=CODE+[str(p.relative_to(REPO)) for p in sorted((REPO/'docs/capstone/contracts').glob('*.schema.json'))]
    return {n:digest((REPO/n).read_bytes()) for n in paths}


def validate(files):
    return validate_bundle(files,trusted_s3_receipt_sha256=S3_PIN,current_manifest_sha256=MANIFEST_PIN)


def read_s3():
    receipt=(S3/'verification.json').read_bytes();require(digest(receipt)==S3_PIN,'Changed S3 receipt')
    files={'verification.json':receipt}
    for n,pin in json.loads(receipt)['files'].items():
        p=S3/n;require(p.parent==S3 and p.resolve(strict=True)==p,'Unsafe S3 member')
        files[n]=p.read_bytes();require(digest(files[n])==pin,'Changed S3 member')
    return files


def main():
    p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true');mode.add_argument('--publish',type=Path);mode.add_argument('--resolve',metavar='RECEIPT_SHA256')
    p.add_argument('--plan-sha256');a=p.parse_args()
    if a.prepare:
        files=build_bundle(read_s3(),trusted_s3_receipt_sha256=S3_PIN,current_manifest_sha256=MANIFEST_PIN)
        report=validate(files)
        code=code_pins()
        metadata=dict(artifact_type='cohort_bundle',schema_version='1.0.0',component='cohort-registry-v1',
            code_sha256=digest(canonical(code)),code_files=code,parents=[dict(kind='s3_qualification',sha256=S3_PIN)],
            retention='keeper_control',sensitivity='private_research_metadata_no_raw_arrays',
            license_scope='private_noncommercial_smoke_only',run_id='cohort-freeze-0001',stage_id='freeze_cohort')
        derivation=digest(canonical(dict(cohort_id=COHORT_ID,metadata=metadata,
            member_hashes={n:digest(v) for n,v in files.items()})))
        plan=dict(artifact_id=COHORT_ID,derivation_sha256=derivation,metadata=metadata,validation=report,
                  files={n:digest(v) for n,v in files.items()},capability_sha256=CAP_PIN)
        candidate=REPO/'outputs/prowl'/('cohort-candidate-'+str(uuid4()));candidate.mkdir()
        for n,v in {**files,'plan.json':canonical(plan)}.items():
            with (candidate/n).open('xb') as f:f.write(v)
        print(candidate);print('plan_sha256='+digest(canonical(plan)));return
    store=cohort_store(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=bool(a.publish))
    if a.publish:
        candidate=a.publish.resolve(strict=True)
        require(candidate.is_relative_to(REPO/'outputs/prowl'),'Candidate outside reviewed staging root')
        payload=(candidate/'plan.json').read_bytes();require(digest(payload)==a.plan_sha256,'Candidate plan pin mismatch')
        plan=json.loads(payload)
        require(plan['artifact_id']==COHORT_ID and plan['capability_sha256']==CAP_PIN,'Wrong publication plan')
        require(plan['metadata']['code_files']==code_pins(),'Producing code changed after plan')
        files={}
        for n,pin in plan['files'].items():
            path=candidate/n;require(path.parent==candidate and path.resolve(strict=True)==path,'Unsafe candidate member')
            files[n]=path.read_bytes();require(digest(files[n])==pin,'Changed candidate bytes')
        pin,state=store.publish(COHORT_ID,derivation_sha256=plan['derivation_sha256'],files=files,
                                 metadata=plan['metadata'],validate=validate)
        print(json.dumps(dict(status=state,cohort_id=COHORT_ID,completion_sha256=pin,
                             relative_uri='cohorts/'+digest(COHORT_ID.encode()))));return
    inputs=resolve_inputs(store,receipt_sha256=a.resolve,trusted_s3_receipt_sha256=S3_PIN,current_manifest_sha256=MANIFEST_PIN)
    print(json.dumps(dict(cohort_id=COHORT_ID,verified_inputs=inputs,source_arrays_opened=False),indent=2))


if __name__=='__main__':main()
