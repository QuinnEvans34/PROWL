"""Exact D-320 metadata prepare/publication/replay. Never opens source arrays."""
import argparse
import json
import resource
import shutil
import signal
import sys
from pathlib import Path
from scripts.diagnostics import publish_segmenter_dispositions as purpose
from scripts.diagnostics.freeze_localizer_cohort import CAP as PROVIDER, CAP_PIN as PROVIDER_PIN
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import manifest_validation_session
from src.data.source_inventory_records import content_hash,require
from src.data.segmenter_cohort_bundle_v1 import freeze,resolve
from src.operations.segmenter_cohort_storage import segmenter_store

REPO=purpose.REPO
BUNDLE_ID='segmenter-cohort-smoke-20261001-528ee3d0-8e4f-4c44-a4cb-c5b51649519c'
CAP=REPO/'docs/capstone/operations/SEGMENTER-COHORT-CAPABILITY-2026-10-01.json'
DEST=REPO/'outputs/prowl/SEGMENTER-COHORT-CANDIDATE-20261001'
PURPOSE_RECEIPT='7334b71e58eaed425ae4d73c2feffc35a7d9f8d9d3af52e90ae5869fdb17f442'
PURPOSE_INPUT='9f45cdf776a7bdbdd2441e61c7b94a25cd461b3435fe4b6b4d53b8ae31920401'
PURPOSE_MANIFEST='31c7239dab12f7e2072897426fd696c9cfafe214ad02682faefc1ed0fa462221'
PURPOSE_TRANSITION='62447d63b981fd6f7fecd1c800f11a2d84ee3dbd66b6e41e180d3938dc3c9eb4'
PURPOSE_CODES='063b885abc144855ff60e3850622024e6ce4045751c56024b1384ca51403e2fb'
PURPOSE_PLAN='a259c6b965dd7da4fb9eac2cd5bb7277af271966917d8f6f784f0e0f356dfabd'
EXPECTED={role:[f'pants:study:PanTS_{n:08}' for n in ns] for role,ns in
    [('train',[3,26,2973,2232,6238,5821]),('validation',[2514])]}
SOURCE_NAMES=('inputs.json','derived.json','plan.json','publication.json','receipt.json')
CODE=['scripts/diagnostics/freeze_segmenter_cohort.py','src/data/segmenter_cohort_bundle_v1.py',
      'src/data/segmenter_cohort_v1.py','src/data/cohort_records_v3.py',
      'src/operations/segmenter_cohort_storage.py','src/operations/storage_roots.py',
      'src/operations/artifact_store.py','scripts/diagnostics/storage_setup.py',
      'src/data/protected_identity.py','src/data/purpose_qualification_v2.py']


def code_pins():
    return purpose.pins()|{n:digest(purpose.read(n)) for n in CODE}


def budget():
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    require(peak<=2*1024**3,'Segmenter metadata RSS ceiling');return peak


def replay_purpose(files):
    require(set(files)==set(SOURCE_NAMES),'Complete purpose package required')
    require(digest(files['receipt.json'])==PURPOSE_RECEIPT,'Independent purpose completion pin differs')
    receipt=json.loads(files['receipt.json'])
    require(receipt['files']=={n:dict(bytes=len(files[n]),sha256=digest(files[n])) for n in SOURCE_NAMES if n!='receipt.json'},
        'Purpose package changed or omitted')
    require(digest(files['plan.json'])==PURPOSE_PLAN,'Independent purpose plan pin differs')
    plan=json.loads(files['plan.json'])
    require(content_hash(plan['code_pins'])==PURPOSE_CODES,'Independent purpose code pin differs')
    derived=purpose.validate_files({n:files[n] for n in ('inputs.json','derived.json','plan.json')},
        PURPOSE_INPUT,PURPOSE_MANIFEST,plan['code_pins'])
    require(content_hash(derived['transition'])==PURPOSE_TRANSITION==plan['transition_sha256'],
        'Independent transition certificate differs')
    return derived,{k:v.encode() for k,v in json.loads(files['inputs.json'])['membership'].items()}


def derive(files):
    d,bases=replay_purpose(files)
    cohorts=freeze(d,bases,EXPECTED,family=BUNDLE_ID)
    report,descriptors=resolve(d,bases,cohorts,EXPECTED)
    report.update(component='segmenter-cohort-bundle-v1',artifact_id=BUNDLE_ID,
        manifest_sha256=PURPOSE_MANIFEST,transition_sha256=PURPOSE_TRANSITION,
        protected_counts={p['protected_role']:len(p['members']) for p in cohorts['parents']},
        original_membership=d['accounting']['original_membership'],candidate_count=12,
        held=[r for r in d['selected'] if r['decision']!='positive'],replacement=False,
        descriptor_sha256=content_hash(descriptors),source_arrays_opened=False,model_updates=0,
        validation_scope=d['accounting']['validation_scope'],biological_uniqueness='unverified_study_as_subject')
    budget();return cohorts,report


def validate(files,code_sha256,cap_pin):
    require(set(files)=={'purpose-'+n for n in SOURCE_NAMES}|{'cohorts.json','controls.json'},'Wrong cohort bundle inventory')
    controls=json.loads(files['controls.json'])
    require(content_hash(controls['code_files'])==code_sha256 and controls['code_files']==code_pins(),
        'Independent producing code changed')
    require(controls==dict(code_files=code_pins(),capability_sha256=cap_pin,provider_capability_sha256=PROVIDER_PIN,
        registry_sha256=json.loads(CAP.read_bytes())['registry_sha256']), 'Changed producing controls')
    require(digest(CAP.read_bytes())==cap_pin,'Changed exact storage capability')
    cohorts,report=derive({n:files['purpose-'+n] for n in SOURCE_NAMES})
    require(canonical(cohorts)==files['cohorts.json'],'Frozen roots/children differ from exact replay')
    return report


def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--publish',action='store_true');g.add_argument('--resolve')
    ap.add_argument('--plan-sha256');ap.add_argument('--code-sha256');ap.add_argument('--capability-sha256',required=True)
    args=ap.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('D-320 metadata deadline')));signal.alarm(1800)
    require(shutil.disk_usage(REPO).free>=100*1024**3,'Internal free floor')
    cap=CAP.read_bytes();require(digest(cap)==args.capability_sha256,'Independent capability pin differs')
    with manifest_validation_session():
        if args.prepare:
            files={n:purpose.read(str(purpose.DEST.relative_to(REPO))+'/'+n) for n in SOURCE_NAMES}
            cohorts,report=derive(files);code=code_pins()
            files={'purpose-'+n:b for n,b in files.items()}|{'cohorts.json':canonical(cohorts),
                'controls.json':canonical(dict(code_files=code,capability_sha256=args.capability_sha256,
                    provider_capability_sha256=PROVIDER_PIN,registry_sha256=json.loads(cap)['registry_sha256']))}
            require(sum(map(len,files.values()))<=96*1024**2,'Metadata output ceiling')
            metadata=dict(artifact_type='cohort_bundle',schema_version='1.0.0',component='segmenter-cohort-bundle-v1',
                code_sha256=content_hash(code),code_files=code,parents=[dict(kind='purpose_completion',sha256=PURPOSE_RECEIPT),
                dict(kind='purpose_transition',sha256=PURPOSE_TRANSITION)],retention='keeper_control',
                sensitivity='private_research_metadata_no_raw_arrays',run_id='segmenter-cohort-freeze-0001',stage_id='freeze_cohorts')
            hashes={n:digest(b) for n,b in files.items()}
            plan=dict(artifact_id=BUNDLE_ID,files=hashes,metadata=metadata,validation=report,
                derivation_sha256=content_hash(dict(files=hashes,metadata=metadata)),capability_sha256=args.capability_sha256)
            DEST.mkdir()
            for n,b in (files|{'plan.json':canonical(plan)}).items():
                with (DEST/n).open('xb') as stream:stream.write(b)
            print(json.dumps(dict(candidate=str(DEST),plan_sha256=content_hash(plan),code_sha256=content_hash(code),
                output_bytes=sum(map(len,files.values())),peak_rss_bytes=budget(),validation=report)));return
        store=segmenter_store(REPO/'configs/local/roots.yaml',cap,trusted_capability_sha256=args.capability_sha256,
            artifact_id=BUNDLE_ID,provider_capability=PROVIDER.read_bytes(),trusted_provider_sha256=PROVIDER_PIN)
        if args.publish:
            require(args.plan_sha256 is not None,'Independent publication-plan pin required')
            raw=purpose.read(str(DEST.relative_to(REPO))+'/plan.json',args.plan_sha256);plan=json.loads(raw)
            require(plan['artifact_id']==BUNDLE_ID and plan['capability_sha256']==args.capability_sha256 and
                plan['metadata']['code_files']==code_pins(),'Wrong or stale publication plan')
            files={n:purpose.read(str(DEST.relative_to(REPO))+'/'+n,pin) for n,pin in plan['files'].items()}
            require(plan['derivation_sha256']==content_hash(dict(files=plan['files'],metadata=plan['metadata'])),
                'Wrong publication derivation')
            pin,state=store.publish(BUNDLE_ID,derivation_sha256=plan['derivation_sha256'],files=files,metadata=plan['metadata'],
                validate=lambda f:validate(f,plan['metadata']['code_sha256'],args.capability_sha256))
            print(json.dumps(dict(completion_sha256=pin,state=state,artifact_id=BUNDLE_ID,
                code_sha256=plan['metadata']['code_sha256'],peak_rss_bytes=budget())));return
        require(args.code_sha256 is not None,'Independent producing-code pin required')
        files,receipt=store.resolve(BUNDLE_ID,receipt_sha256=args.resolve,
            validate=lambda f:validate(f,args.code_sha256,args.capability_sha256))
        d=json.loads(files['purpose-derived.json']);bases={k:v.encode() for k,v in json.loads(files['purpose-inputs.json'])['membership'].items()}
        report,descriptors=resolve(d,bases,json.loads(files['cohorts.json']),EXPECTED)
        print(json.dumps(dict(state='resolved',completion_sha256=args.resolve,artifact_id=BUNDLE_ID,
            validation=receipt['validation'],descriptors=descriptors,peak_rss_bytes=budget())))
    signal.alarm(0)


if __name__=='__main__':main()
