"""Prepare/publish/resolve the D-282 metadata-only expansion under pinned evidence."""
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
from src.data.localizer_expansion import derive,evidence_ref,freeze_records,consume,BUNDLE_ID
from src.operations.storage_roots import cohort_store
from scripts.diagnostics.freeze_localizer_cohort import S3,S3_PIN,MANIFEST_PIN,CAP,CAP_PIN,read_s3

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
CONTENT='localizer-content-264c2d12-3367-40ae-805a-fe74b1ac3b72'
CONTENT_PIN='224795f966a25733c7c1198e22dfa34fc525ef56be4e023ebdaa48ef8af0e3a9'
REVIEW='localizer-candidate-review-65e9f44a-f597-43ef-b11b-d889aeeb6947'
REVIEW_PIN='cb556a1086d665cb8584f9a8f404c89953445401bb9afc7c958f4e498560b8a4'
USE='docs/capstone/data/LOCALIZER-EXPANSION-QUALIFICATION-2026-09-29.md'
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
    require(r['state']=='complete' and len(r['files'])<=100,'Incomplete evidence')
    for n,ref in r['files'].items():
        require(Path(n).name==n and n not in ('.','..'),'Unsafe member')
        b=bounded_read(path/n);require(len(b)==ref['bytes'] and digest(b)==ref['sha256'],'Changed retained member')
        if not n.endswith('.png'):files[n]=b.decode()
    return receipt.decode(),files


def capture_inputs():
    old=read_s3();prior=json.loads(old['manifests.json'])[-1]
    require(content_hash(prior)==MANIFEST_PIN,'Prior manifest changed')
    cr,content=read_review_package(CONTENT,CONTENT_PIN);rr,review=read_review_package(REVIEW,REVIEW_PIN)
    source=bounded_read(REPO/SOURCE);require(digest(source)==SOURCE_PIN,'Source assessment changed')
    use=bounded_read(REPO/USE)
    return dict(recorded_at=datetime.now(timezone.utc).isoformat(),prior=prior,prior_evidence=json.loads(old['evidence.json']),membership=json.loads(old['membership.json']),
        content_receipt=cr,content=content,review_receipt=rr,review=review['review.json'],use=use.decode(),source=source.decode(),
        prior_receipt_sha256=S3_PIN,prior_manifest_sha256=MANIFEST_PIN)


def rebuild(inputs):
    require(content_hash(inputs['prior'])==MANIFEST_PIN and inputs['prior_receipt_sha256']==S3_PIN,'Unreviewed predecessor')
    require(digest(inputs['content_receipt'].encode())==CONTENT_PIN and digest(inputs['review_receipt'].encode())==REVIEW_PIN,'Unreviewed audit/review')
    content=inputs['content'];refs=json.loads(inputs['content_receipt'])['files']
    require(set(content)=={n for n in refs if not n.endswith('.png')},'Evidence member omission')
    for n,text in content.items():require(digest(text.encode())==refs[n]['sha256'],'Changed content evidence')
    rref=json.loads(inputs['review_receipt'])['files']['review.json'];rb=inputs['review'].encode()
    require(digest(rb)==rref['sha256'] and len(rb)==rref['bytes'],'Changed review')
    review=json.loads(rb);require(review['content_receipt_sha256']==CONTENT_PIN,'Review parent changed')
    for row in review['cases']:
        stem=row['study_id'].split(':')[-1]
        require(row['sheet_sha256']==refs[stem+'.png']['sha256'] and row['facts_sha256']==refs[stem+'.json']['sha256'],'Review artifact binding changed')
    source=inputs['source'].encode();require(digest(source)==SOURCE_PIN,'Source assessment changed')
    result=json.loads(content['result.json']);require(result['state']=='content_evidence_complete_not_qualification' and result['case_count']==28 and not result['duplicate_ct_groups'],'Unexpected content result')
    selection=json.loads(content['selection.json']);require(selection['requested_counts']=={'train':16,'validation':12},'Changed requested count')
    evidence={k:v.encode() for k,v in inputs['prior_evidence'].items()}
    require(all(digest(v)==k for k,v in evidence.items()),'Prior evidence hash mismatch')
    use=inputs['use'].encode();evidence[digest(use)]=use;evidence[digest(source)]=source
    bases={k:v.encode() for k,v in inputs['membership'].items()}
    facts={row['study_id']:content[row['study_id'].split(':')[-1]+'.json'].encode() for row in review['cases']}
    mapping=next(a for a in inputs['prior']['annotations'] if a['study_id']=='pants:study:PanTS_00000003' and a['structure']=='pancreas')['label_encoding']['mapping']
    m,q,e=derive(prior=inputs['prior'],bases=bases,evidence=evidence,facts=facts,review_bytes=rb,selection=selection,
        use_ref=evidence_ref(Path(USE).name,use,'text/markdown'),source_ref=evidence_ref(Path(SOURCE).name,source,'text/markdown'),mapping=mapping,recorded_at=inputs['recorded_at'])
    expected={role:sorted(c['study_id'] for c in selection['candidates'][role] if c['study_id']!=HELD) for role in ('train','validation')}
    require([(x['study_id'],x['outcome']) for x in q if x['outcome']!='qualified']==[(HELD,'held')],'Unexpected qualification outcome')
    parents,children=freeze_records(m,q,e,bases,expected_members=expected)
    accounting=dict(candidate_counts=selection['requested_counts'],executable_counts={r:len(ids) for r,ids in expected.items()},
        candidate_ids={r:sorted(c['study_id'] for c in selection['candidates'][r]) for r in expected},executable_ids=expected,
        held=[dict(study_id=HELD,reason='physical_units_unresolved',descriptive_stratum=next(c['descriptive_stratum'] for c in selection['candidates']['validation'] if c['study_id']==HELD))],
        replacement=False,training_started=False,source_integrity='staged_partial_integrity',biological_uniqueness='unverified_study_as_subject',
        validation_limitation='11 development cases; no population generalization or final-test claim')
    output=dict(manifest=m,qualifications=q,evidence={k:v.decode() for k,v in e.items()},parents=parents,cohorts=children,accounting=accounting)
    report=dict(bundle_id=BUNDLE_ID,manifest_sha256=content_hash(m),qualified_count=27,held_count=1,
        executable_counts=accounting['executable_counts'],protected_counts={p['protected_role']:len(p['members']) for p in parents},
        prior_issues_preserved=len(inputs['prior']['issues']),source_arrays_opened=False)
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


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--publish',type=Path);g.add_argument('--resolve')
    p.add_argument('--plan-sha256');p.add_argument('--inputs-sha256');p.add_argument('--manifest-sha256')
    a=p.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('D-282 deadline')));signal.alarm(1800)
    require(shutil.disk_usage(REPO).free>=100*1024**3,'Internal free floor')
    if a.prepare:
        inputs=capture_inputs();derived,report=rebuild(inputs);files={'inputs.json':canonical(inputs),'derived.json':canonical(derived)}
        require(sum(map(len,files.values()))<=96*1024**2,'Artifact cap')
        code=code_pins();metadata=dict(artifact_type='cohort_bundle',schema_version='1.0.0',component='localizer-expansion-v1',code_sha256=content_hash(code),code_files=code,
            parents=[dict(kind='prior_qualification',sha256=S3_PIN),dict(kind='content',sha256=CONTENT_PIN),dict(kind='review',sha256=REVIEW_PIN)],
            retention='keeper_control',sensitivity='private_research_metadata_no_raw_arrays',run_id='expansion-freeze-0001',stage_id='freeze_cohorts')
        pins={n:digest(v) for n,v in files.items()};plan=dict(artifact_id=BUNDLE_ID,files=pins,metadata=metadata,validation=report,
            derivation_sha256=content_hash(dict(files=pins,metadata=metadata)),capability_sha256=CAP_PIN)
        out=ROOT/('expansion-candidate-'+str(uuid4()));out.mkdir()
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
    d=json.loads(files['derived.json']);i=json.loads(files['inputs.json']);e={k:v.encode() for k,v in d['evidence'].items()};bases={k:v.encode() for k,v in i['membership'].items()}
    members={op:consume(d['manifest'],d['qualifications'],e,bases,d['parents'],d['cohorts'],operation=op,current_manifest_sha256=a.manifest_sha256) for op in ('optimizer','evaluator')}
    print(json.dumps(dict(completion_sha256=a.resolve,verified_counts={op:len(v) for op,v in members.items()},source_arrays_opened=False,accounting=d['accounting']),indent=2))

if __name__=='__main__':main()
