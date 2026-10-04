"""Prepare/publish/resolve the D-294 metadata-only expansion under pinned evidence."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import resource
import shutil
import signal
from uuid import uuid4
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import content_hash,require
from src.data.localizer_expansion_v2 import derive,evidence_ref,freeze_records,consume,BUNDLE_ID
from src.operations.storage_roots import cohort_store
from scripts.diagnostics.freeze_localizer_cohort import S3,S3_PIN,MANIFEST_PIN,CAP,CAP_PIN,read_s3

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
CONTENT='localizer-content-264c2d12-3367-40ae-805a-fe74b1ac3b72'
CONTENT_PIN='224795f966a25733c7c1198e22dfa34fc525ef56be4e023ebdaa48ef8af0e3a9'
REVIEW='localizer-candidate-review-65e9f44a-f597-43ef-b11b-d889aeeb6947'
REVIEW_PIN='cb556a1086d665cb8584f9a8f404c89953445401bb9afc7c958f4e498560b8a4'
USE='docs/capstone/data/LOCALIZER-EXPANSION-V2-QUALIFICATION-2026-09-29.md'
SOURCE='docs/capstone/data/LOCALIZER-SOURCE-AND-ALIGNMENT-REVIEW-2026-09-28.md'
SOURCE_PIN='f093ed893d9bc2a6f93dc03fa1a2593abe291ef7e6f6a7b5046e62a71aa927c8'
HELD='pants:study:PanTS_00006350'
CODE=['src/data/localizer_expansion.py','scripts/diagnostics/freeze_localizer_expansion.py','src/data/cohort_records_v3.py',
      'src/data/purpose_qualification_v2.py','src/data/manifest_records_v3.py','src/data/source_inventory_records.py',
      'src/data/manifest_records.py','src/data/annotation_contract_v2.py','src/data/protected_identity.py',
      'src/operations/artifact_store.py','src/operations/storage_roots.py','scripts/diagnostics/storage_setup.py',
      'scripts/diagnostics/freeze_localizer_cohort.py','src/data/binary_label_policy.py']


def bounded_read(path,cap=96*1024**2):
    require(path.resolve(strict=True)==path and path.is_file() and path.stat().st_size<=cap,'Unsafe/oversized retained file')
    data=path.read_bytes();require(len(data)<=cap,'Evidence read cap');return data


def read_review_package(name,pin):
    path=ROOT/name;receipt=bounded_read(path/'receipt.json',1024**2)
    require(digest(receipt)==pin,'Changed retained receipt');r=json.loads(receipt);files={}
    refs=receipt_refs(r)
    require(len(refs)<=400,'Oversized evidence inventory')
    for n,ref in refs.items():
        require(Path(n).name==n and n not in ('.','..'),'Unsafe member')
        b=bounded_read(path/n);require((ref.get('bytes') is None or len(b)==ref['bytes']) and digest(b)==ref['sha256'],'Changed retained member')
        if not n.endswith('.png'):files[n]=b.decode()
    return receipt.decode(),files


PRIOR_DIR='expansion-candidate-1e1e331d-c385-410b-97ee-a6e1478a1e70'
PRIOR_DERIVED='c4c0111bff1b22f7de463c3080ce80c188cd32b922fb10581eb27887e1f958ce'
PRIOR_INPUTS='65236e19a7a26bd43d7206010d5d1b029e45b556b6aa8408f63209dedbf6d4fb'
SELECTION_DIR='localizer-candidates-v2-0d91addc-1ef8-402b-b12a-611aa78f12f9'
SELECTION_PIN='aa9a77cbcb3848b194a2e1bcb5515174dbf4aa4efa22c18e0d0d7746ec7ab3a7'
RECON_DIR='content-continuation-review-20260929'
RECON_PIN='54c561165c1cf51a14114768050f1124116569a8566e8c7ce689963b3728ab23'
PILOT_DIR='localizer-content-v2-164a85ed-78aa-4a2e-99bd-33be442a7393'
PILOT_PIN='80baf3b1d63e1c8b2097f791f39b074e95d15b897425879f56812d9bfd281009'
PILOT_REVIEW='localizer-content-v2-pilot-review-20260929'
PILOT_REVIEW_PIN='341fd097a43259ed2eca388b5edbc2d469580e06db9467ad14393def4c9efe90'
CODE += ['src/data/localizer_expansion_v2.py','scripts/diagnostics/freeze_localizer_expansion_v2.py']


def receipt_refs(receipt):
    # Retained reviewed receipts use either direct hashes or explicit byte/hash references.
    refs=receipt.get('files',receipt)
    return {n:({'sha256':v} if isinstance(v,str) else v) for n,v in refs.items()}


def verified_package(receipt_text, files, pin):
    require(digest(receipt_text.encode())==pin,'Receipt pin mismatch')
    refs=receipt_refs(json.loads(receipt_text))
    require(set(files)=={n for n in refs if not n.endswith('.png')},'Evidence member omission')
    for n,text in files.items():
        require(digest(text.encode())==refs[n]['sha256'] and (refs[n].get('bytes') is None or len(text.encode())==refs[n]['bytes']),'Changed retained evidence')
    return refs


def capture_inputs():
    prior=bounded_read(ROOT/PRIOR_DIR/'derived.json');old=bounded_read(ROOT/PRIOR_DIR/'inputs.json')
    require(digest(prior)==PRIOR_DERIVED and digest(old)==PRIOR_INPUTS,'Prior expansion changed')
    rr,review=read_review_package(RECON_DIR,RECON_PIN)
    sr,selection=read_review_package(SELECTION_DIR,SELECTION_PIN)
    reconciliation=json.loads(review['reconciliation.json'])
    packages={}
    scopes=[(CONTENT,CONTENT_PIN),(PILOT_DIR,PILOT_PIN)] + [(Path(x['path']).name,x['receipt_sha256']) for x in reconciliation['batch_summaries']]
    for name,pin in scopes:
        receipt,files=read_review_package(name,pin);packages[pin]=dict(receipt=receipt,files=files)
    prior_reviews={}
    for name,pin in [(REVIEW,REVIEW_PIN),(PILOT_REVIEW,PILOT_REVIEW_PIN)]:
        receipt,files=read_review_package(name,pin);prior_reviews[pin]=dict(receipt=receipt,files=files)
    source=bounded_read(REPO/SOURCE);require(digest(source)==SOURCE_PIN,'Source changed')
    return dict(recorded_at=datetime.now(timezone.utc).isoformat(),prior_payload=prior.decode(),prior_inputs=old.decode(),
        selection_receipt=sr,selection_files=selection,review_receipt=rr,review_files=review,packages=packages,
        prior_reviews=prior_reviews,use=bounded_read(REPO/USE).decode(),source=source.decode())


def rebuild(inputs):
    require(digest(inputs['prior_payload'].encode())==PRIOR_DERIVED and digest(inputs['prior_inputs'].encode())==PRIOR_INPUTS,'Unreviewed predecessor')
    predecessor=json.loads(inputs['prior_payload']);old=json.loads(inputs['prior_inputs'])
    verified_package(inputs['selection_receipt'],inputs['selection_files'],SELECTION_PIN)
    verified_package(inputs['review_receipt'],inputs['review_files'],RECON_PIN)
    for pin in (REVIEW_PIN,PILOT_REVIEW_PIN):
        pkg=inputs['prior_reviews'][pin];verified_package(pkg['receipt'],pkg['files'],pin)
    selection=json.loads(inputs['selection_files']['selection.json'])
    require(selection['requested_counts']=={'train':128,'validation':48},'Candidate count changed')
    reconciliation=json.loads(inputs['review_files']['reconciliation.json'])
    require(not reconciliation['duplicate_compressed_ct_groups'],'Duplicate CT requires review')
    package_pins={CONTENT_PIN,PILOT_PIN}|{x['receipt_sha256'] for x in reconciliation['batch_summaries']}
    require(set(inputs['packages'])==package_pins,'Content package omission')
    refs={pin:verified_package(p['receipt'],p['files'],pin) for pin,p in inputs['packages'].items()}
    facts={};review_rows=[]
    for row in reconciliation['records']:
        sid=row['study_id'];require(sid not in facts,'Duplicate reviewed identity')
        stem=sid.split(':')[-1];pin=row['content_receipt_sha256']
        data=inputs['packages'][pin]['files'][stem+'.json'].encode()
        require(digest(data)==row['record_sha256'],'Reviewed facts changed')
        fact=json.loads(data);require(fact['study_id']==sid and fact['protected_role']==row['role'] and fact['holds']==row['holds'],'Reviewed role/holds changed')
        empty=fact['decode']['foreground_voxels']==0
        if not empty:
            require(refs[pin][stem+'.png']['sha256']==row['alignment_sheet_sha256'],'Reviewed sheet changed')
            require(row['visual_review'] in ('paired_five_plane_overview_reviewed','retained_prior_review'),'Alignment not reviewed')
        else:require(row['alignment_sheet_sha256'] is None,'Empty reference falsely reviewed')
        observations=[row['observation']]
        if row['boundary_contacts']:observations.append('Source-face contact: '+json.dumps(row['boundary_contacts'])+'; visible-reference containment only.')
        review_rows.append(dict(study_id=sid,protected_role=row['role'],facts_sha256=digest(data),
            assessment='not_reviewed_empty_reference' if empty else 'no_obvious_gross_displacement_in_sampled_views',
            reviewed_planes=fact.get('review_planes',[]),retained_automated_holds=fact['holds'],observations=observations))
        facts[sid]=data
    require(len(facts)==176,'Incomplete candidate reconciliation')
    rb=canonical(dict(parent_review_sha256=RECON_PIN,scope='visible_reference_development_only',cases=review_rows))
    evidence={k:v.encode() for k,v in predecessor['evidence'].items()}
    require(all(digest(v)==k for k,v in evidence.items()),'Prior evidence hash mismatch')
    source=inputs['source'].encode();require(digest(source)==SOURCE_PIN,'Source assessment changed')
    use=inputs['use'].encode();evidence[digest(use)]=use;evidence[digest(source)]=source
    # Retain original reconciliation and prior review records as provenance, alongside normalized checks.
    for text in [inputs['review_files']['reconciliation.json'],inputs['review_receipt']]:evidence[digest(text.encode())]=text.encode()
    bases={k:v.encode() for k,v in old['membership'].items()}
    mapping=next(a for a in predecessor['manifest']['annotations'] if a['study_id']=='pants:study:PanTS_00000003' and a['structure']=='pancreas')['label_encoding']['mapping']
    m,q,e=derive(prior=predecessor['manifest'],bases=bases,evidence=evidence,facts=facts,review_bytes=rb,selection=selection,
        use_ref=evidence_ref(Path(USE).name,use,'text/markdown'),source_ref=evidence_ref(Path(SOURCE).name,source,'text/markdown'),mapping=mapping,recorded_at=inputs['recorded_at'])
    expected={role:sorted(c['study_id'] for c in selection['candidates'][role] if not json.loads(facts[c['study_id']])['holds']) for role in ('train','validation')}
    require({r:len(v) for r,v in expected.items()}=={'train':113,'validation':40},'Unexpected supported subset')
    require({x['study_id'] for x in q if x['outcome']=='held'}=={sid for sid,data in facts.items() if json.loads(data)['holds']},'Unexpected qualification outcomes')
    parents,children=freeze_records(m,q,e,bases,expected_members=expected)
    coverage={}
    for role in expected:
        coverage[role]={}
        for c in selection['candidates'][role]:
            key=json.dumps(c['descriptive_stratum'],sort_keys=True)
            counts=coverage[role].setdefault(key,dict(candidates=0,qualified=0,held=0));counts['candidates']+=1
            counts['qualified' if c['study_id'] in expected[role] else 'held']+=1
    accounting=dict(candidate_counts=selection['requested_counts'],executable_counts={r:len(v) for r,v in expected.items()},
        candidate_ids={r:sorted(c['study_id'] for c in selection['candidates'][r]) for r in expected},executable_ids=expected,
        held=[dict(study_id=sid,reasons=json.loads(data)['holds']) for sid,data in sorted(facts.items()) if json.loads(data)['holds']],
        strata=coverage,replacement=False,training_started=False,source_integrity='staged_partial_integrity',
        biological_uniqueness='unverified_study_as_subject',target_scope='visible_reference_not_whole_organ',
        validation_limitation='Stratified development selection; no population estimate, final-test or whole-organ claim')
    output=dict(manifest=m,qualifications=q,evidence={k:v.decode() for k,v in e.items()},parents=parents,cohorts=children,accounting=accounting)
    report=dict(bundle_id=BUNDLE_ID,manifest_sha256=content_hash(m),qualified_count=153,held_count=23,
        executable_counts=accounting['executable_counts'],protected_counts={p['protected_role']:len(p['members']) for p in parents},
        prior_issues_preserved=len(predecessor['manifest']['issues']),source_arrays_opened=False)
    require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=2*1024**3,'Metadata RSS cap exceeded')
    return output,report


def validate(files,inputs_pin,current_manifest):
    require(set(files)=={'inputs.json','derived.json'},'Unexpected bundle inventory')
    require(digest(files['inputs.json'])==inputs_pin,'Independent input pin mismatch')
    expected,report=rebuild(json.loads(files['inputs.json']))
    require(canonical(expected)==files['derived.json'],'Derived evidence/cohort changed')
    require(report['manifest_sha256']==current_manifest,'Current manifest differs; requalification required')
    return report


def code_pins():
    names=CODE+[str(p.relative_to(REPO)) for p in sorted((REPO/'docs/capstone/contracts').glob('*.schema.json'))]
    return {n:digest((REPO/n).read_bytes()) for n in names}


def _main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--publish',type=Path);g.add_argument('--resolve')
    p.add_argument('--plan-sha256');p.add_argument('--inputs-sha256');p.add_argument('--manifest-sha256')
    a=p.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('D-294 deadline')));signal.alarm(1800)
    require(shutil.disk_usage(REPO).free>=100*1024**3,'Internal free floor')
    if a.prepare:
        inputs=capture_inputs();derived,report=rebuild(inputs);files={'inputs.json':canonical(inputs),'derived.json':canonical(derived)}
        require(sum(map(len,files.values()))<=96*1024**2,'Artifact cap')
        code=code_pins();metadata=dict(artifact_type='cohort_bundle',schema_version='1.0.0',component='localizer-expansion-v2',code_sha256=content_hash(code),code_files=code,
            parents=[dict(kind='prior_qualification',sha256=PRIOR_DERIVED),dict(kind='candidates',sha256=SELECTION_PIN),dict(kind='review',sha256=RECON_PIN)],
            retention='keeper_control',sensitivity='private_research_metadata_no_raw_arrays',run_id='expansion-freeze-0002',stage_id='freeze_cohorts')
        pins={n:digest(v) for n,v in files.items()};plan=dict(artifact_id=BUNDLE_ID,files=pins,metadata=metadata,validation=report,
            derivation_sha256=content_hash(dict(files=pins,metadata=metadata)),capability_sha256=CAP_PIN)
        out=ROOT/('expansion-v2-candidate-'+str(uuid4()));out.mkdir()
        for n,v in {**files,'plan.json':canonical(plan)}.items():
            with (out/n).open('xb') as f:f.write(v)
        print(json.dumps(dict(candidate=str(out),plan_sha256=content_hash(plan),inputs_sha256=pins['inputs.json'],**report),indent=2));return
    store=cohort_store(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=bool(a.publish))
    if a.publish:
        root=a.publish.resolve(strict=True);require(root.is_relative_to(ROOT),'Candidate outside staging')
        raw=bounded_read(root/'plan.json');require(digest(raw)==a.plan_sha256,'Independent plan pin mismatch');plan=json.loads(raw)
        require(plan['artifact_id']==BUNDLE_ID and plan['capability_sha256']==CAP_PIN and plan['metadata']['code_files']==code_pins(),'Publication controls changed')
        files={n:bounded_read(root/n) for n in ('inputs.json','derived.json')}
        require({n:digest(v) for n,v in files.items()}==plan['files'],'Candidate changed')
        pin,state=store.publish(BUNDLE_ID,derivation_sha256=plan['derivation_sha256'],files=files,metadata=plan['metadata'],
            validate=lambda f:validate(f,plan['files']['inputs.json'],plan['validation']['manifest_sha256']))
        print(json.dumps(dict(completion_sha256=pin,status=state,bundle_id=BUNDLE_ID)));return
    require(a.inputs_sha256 and a.manifest_sha256,'Independent inputs/current manifest pins required')
    files,receipt=store.resolve(BUNDLE_ID,receipt_sha256=a.resolve,validate=lambda f:validate(f,a.inputs_sha256,a.manifest_sha256))
    d=json.loads(files['derived.json']);i=json.loads(files['inputs.json']);e={k:v.encode() for k,v in d['evidence'].items()};bases={k:v.encode() for k,v in json.loads(i['prior_inputs'])['membership'].items()}
    members={op:consume(d['manifest'],d['qualifications'],e,bases,d['parents'],d['cohorts'],operation=op,current_manifest_sha256=a.manifest_sha256) for op in ('optimizer','evaluator')}
    print(json.dumps(dict(completion_sha256=a.resolve,verified_counts={op:len(v) for op,v in members.items()},source_arrays_opened=False,accounting=d['accounting']),indent=2))

def main():
    from src.data.manifest_records_v3 import manifest_validation_session
    with manifest_validation_session():
        _main()


if __name__=='__main__':main()
