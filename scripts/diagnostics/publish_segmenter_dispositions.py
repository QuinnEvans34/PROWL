"""D-319 metadata-only, exact-input local publication/replay; no source-root access."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import resource
import signal
import sys
from scripts.diagnostics import segmenter_source_verification as source
from scripts.diagnostics.segmenter_content_pilot import package,write_bytes
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import manifest_validation_session
from src.data.source_inventory_records import content_hash,require
from src.data.segmenter_dispositions_v1 import derive
from src.data.segmenter_transition_v1 import build_transition
from src.data.localizer_expansion_v2 import evidence_ref

REPO=source.REPO
PRIOR='outputs/prowl/expansion-v2-candidate-6bc5c245-47b4-45ab-9616-cd75da986b74'
PRIOR_PIN='b0f1c625728603ce87841d5c0ce7ad5397574da04dd5e7ca4814c5ef462ca29f'
INPUT_PIN='2c6c723cf4658d8d4926d07b804f20abc10b1afd83485f36adab4d436a809785'
INVENTORY='outputs/prowl/STAGE2-METADATA-20261001/inventory.json'
INVENTORY_PIN='2f38464f4fd6efe8235b5471bf2f46466ab7ce13d17e1c7ccff2c7876997aab4'
LEDGER='outputs/prowl/SEGMENTER-CONTENT-CONTINUATION-REVIEW-20261001/candidate-ledger.json'
LEDGER_PIN='c471a6e2140cd40d9b471093d3a607d65c1c25c04c1cd9afb681f647f7e066b9'
USE='docs/capstone/data/SEGMENTER-PURPOSE-USE-2026-10-01.md'
USE_PIN='c50e47a262f7edeb8aa01bdfbc2f773e440e047032666ead1ecf62ec7cb2f57b'
SOURCE='docs/capstone/data/PANTS-SOURCE-USE-REVIEW-2026-09-28.md'
SOURCE_PIN='4da0024993134d17552fd999b4fd1f45c3e436d814f2f4ae7922abfc9b57e5b0'
CANDIDATE=REPO/'outputs/prowl/SEGMENTER-DISPOSITION-CANDIDATE-20261001'
DEST=REPO/'outputs/prowl/SEGMENTER-DISPOSITIONS-20261001'
PACKAGES={
 'outputs/prowl/SEGMENTER-SOURCE-M2-20261001':'bec0f3b3f292d187b3bc741be6fa38b8aa355f199c1cf3375657364705421108',
 'outputs/prowl/SEGMENTER-CONTENT-PILOT-20261001':'2f972c5c8136c60630ba3559b7435b84c79af0cec7689c190ebfd6b28ce26d7f',
 'outputs/prowl/SEGMENTER-CONTENT-CONTINUATION-20261001':'eeb5d3b01c71ed6cd7df09c3fa3e327cb2a2576a6defe60caf9020d688fd4036',
 'outputs/prowl/SEGMENTER-CONTENT-CONTINUATION-REVIEW-20261001':'fb483be6d1f6c34cdbbf26c88f3d48e95dfcb475025a63cf81b0b8b8c4ce7f9d'}
CODES=['src/data/segmenter_dispositions_v1.py','src/data/segmenter_transition_v1.py',
 'scripts/diagnostics/publish_segmenter_dispositions.py','src/data/segmenter_qualification_v1.py',
 'src/data/manifest_records_v3.py','src/data/annotation_contract_v2.py','src/data/source_inventory_records.py',
 'src/data/localizer_expansion_v2.py','src/data/binary_label_policy.py','scripts/diagnostics/segmenter_source_verification.py',
 'scripts/diagnostics/segmenter_content_pilot.py']
CASES={f'pants:study:PanTS_{n:08}':('annotation_relationship_unresolved' if n==5641 else 'empty_unknown' if n in [6110,4965,2727,7265] else 'positive')
       for n in [3,26,6110,2973,2232,6238,5821,4965,2514,5641,2727,7265]}


def read(name,pin=None,cap=96*1024**2):
    path=REPO/name
    require(path.resolve(strict=True)==path and path.is_file() and path.stat().st_size<=cap,'Unsafe retained input')
    raw=path.read_bytes();require(len(raw)<=cap and (pin is None or digest(raw)==pin),'Retained input changed')
    return raw


def verify_package(name,pin):
    path=REPO/name;rec=json.loads(read(name+'/receipt.json',pin,1024**2))
    require({p.name for p in path.iterdir()}==set(rec['files'])|{'receipt.json'},'Unexpected retained package member')
    for n,ref in rec['files'].items():
        require(Path(n).name==n,'Unsafe member');b=read(name+'/'+n)
        require(len(b)==ref['bytes'] and digest(b)==ref['sha256'],'Retained package changed')
    return rec


def pins():
    names=CODES+[str(p.relative_to(REPO)) for p in sorted((REPO/'docs/capstone/contracts').glob('*.schema.json'))]
    return {n:digest(read(n)) for n in names}


def capture():
    for name,pin in PACKAGES.items():verify_package(name,pin)
    prior=read(PRIOR+'/derived.json',PRIOR_PIN);old=json.loads(read(PRIOR+'/inputs.json',INPUT_PIN));bases=json.loads(old['prior_inputs'])['membership']
    ledger=read(LEDGER,LEDGER_PIN);inventory=read(INVENTORY,INVENTORY_PIN)
    rows=json.loads(ledger)['cases'];facts={}
    require({c['study_id'] for c in rows}==set(CASES),'Changed twelve-case scope')
    for c in rows:
        names=[name for name,pin in PACKAGES.items() if pin==c['source_receipt_sha256']];require(len(names)==1,'Unknown content receipt')
        sid=c['study_id'];facts[sid]=read(names[0]+'/'+sid.split(':')[-1]+'.json',c['case_report_sha256']).decode()
    return dict(recorded_at=datetime.now(timezone.utc).isoformat(),prior=prior.decode(),membership=bases,inventory=inventory.decode(),
                ledger=ledger.decode(),facts=facts,use=read(USE,USE_PIN).decode(),source=read(SOURCE,SOURCE_PIN).decode())


def rebuild(inputs):
    require(set(inputs)=={'recorded_at','prior','membership','inventory','ledger','facts','use','source'},'Unexpected input fields')
    for name,pin in [('prior',PRIOR_PIN),('inventory',INVENTORY_PIN),('ledger',LEDGER_PIN),('use',USE_PIN),('source',SOURCE_PIN)]:
        require(digest(inputs[name].encode())==pin,'Changed reviewed '+name)
    prior=json.loads(inputs['prior']);m=prior['manifest'];bases={k:v.encode() for k,v in inputs['membership'].items()}
    require(set(inputs['facts'])==set(CASES),'Case omission/substitution')
    inventory=json.loads(inputs['inventory']);require({c['study_id'] for c in inventory['proposed_candidates']}==set(CASES),'Metadata selection differs')
    evidence={h:b.encode() for h,b in prior['evidence'].items()}
    for key in ['source','use']:
        raw=inputs[key].encode();evidence[digest(raw)]=raw
    d=derive(prior=m,bases=bases,evidence=evidence,facts={k:v.encode() for k,v in inputs['facts'].items()},
        review_bytes=inputs['ledger'].encode(),trusted_review_sha256=LEDGER_PIN,decisions=CASES,
        use_ref=evidence_ref(Path(USE).name,inputs['use'].encode(),'text/markdown'),
        source_ref=evidence_ref(Path(SOURCE).name,inputs['source'].encode(),'text/markdown'),recorded_at=inputs['recorded_at'])
    reviewed=[]
    for row in d['selected']:
        pending=[]
        if row['prior_lesion_annotation_id'] and row['decision']=='positive':
            old=next(a for a in m['annotations'] if a['annotation_id']==row['prior_lesion_annotation_id'])
            pending=[dict(issue_id=i['issue_id'],sha256=content_hash(i)) for i in sorted(m['issues'],key=lambda i:i['issue_id']) if i['issue_id'] in old['issue_ids']]
        reviewed.append({k:row[k] for k in ['study_id','decision','pancreas_annotation_id','prior_lesion_annotation_id','lesion_annotation_id']}|dict(superseded_pending_use_issues=pending))
    review=canonical(dict(component='segmenter-transition-review-v1',prior_manifest_sha256=content_hash(m),manifest_sha256=content_hash(d['manifest']),cases=reviewed))
    transition=build_transition(prior_manifest=m,derived=d,trusted_prior_manifest_sha256=content_hash(m),trusted_manifest_sha256=content_hash(d['manifest']),
        review_bytes=review,trusted_review_sha256=digest(review),evidence_by_sha256={h:b.encode() for h,b in d['evidence'].items()},trusted_evidence_sha256=set(d['evidence']),base_membership_bytes=bases)
    accounting=dict(candidates=12,qualified_train=sum(q['outcome']=='qualified' and q['protected_role']=='train' for q in d['qualifications']),
        qualified_validation=sum(q['outcome']=='qualified' and q['protected_role']=='validation' for q in d['qualifications']),held=sum(q['outcome']=='held' for q in d['qualifications']),
        paired_inventories=len(d['lesion_inventories']),prior_annotations_preserved=len(m['annotations']),prior_issues_preserved=len(m['issues']),
        original_membership={'train':7200,'validation':1800,'test':901},localizer_members=153,localizer_holds=23,
        source_reads=0,cohorts_published=0,model_updates=0,validation_scope='one_visible_positive_engineering_reference_no_performance_claim')
    require(accounting['qualified_train']==6 and accounting['qualified_validation']==1 and accounting['held']==5,'Unexpected qualified/held outcomes')
    return d|dict(transition_review=json.loads(review),transition=transition,accounting=accounting)


def budget():
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    require(peak<=2*1024**3,'Metadata RSS ceiling');return peak


def validate_files(files,inputs_pin,manifest_pin,expected_codes):
    require(set(files)=={'inputs.json','derived.json','plan.json'},'Wrong package payload')
    require(digest(files['inputs.json'])==inputs_pin,'Independent inputs pin differs')
    plan=json.loads(files['plan.json']);require(plan['code_pins']==expected_codes==pins() and plan['runtime']==source.runtime(),'Code/runtime changed')
    require(plan['files']=={n:digest(files[n]) for n in ['inputs.json','derived.json']},'Changed derived files')
    expected=rebuild(json.loads(files['inputs.json']));require(canonical(expected)==files['derived.json'],'Derived transition/qualification changed')
    require(content_hash(expected['manifest'])==manifest_pin==plan['manifest_sha256'],'Independent manifest pin differs')
    budget();return expected


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--publish',action='store_true');ap.add_argument('--resolve',action='store_true')
    ap.add_argument('--plan-sha256');ap.add_argument('--receipt-sha256');ap.add_argument('--inputs-sha256');ap.add_argument('--manifest-sha256');args=ap.parse_args()
    require(sum([args.prepare,args.publish,args.resolve])==1,'Exactly one metadata operation required')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Metadata deadline')));signal.alarm(1800)
    with manifest_validation_session():
        if args.prepare:
            inputs=capture();d=rebuild(inputs);files={'inputs.json':canonical(inputs),'derived.json':canonical(d)}
            require(sum(map(len,files.values()))<=96*1024**2,'Metadata payload ceiling')
            plan=dict(component='segmenter-dispositions-v1',decision='D-319',code_pins=pins(),runtime=source.runtime(),files={n:digest(b) for n,b in files.items()},
                manifest_sha256=content_hash(d['manifest']),transition_sha256=content_hash(d['transition']),accounting=d['accounting'],source_access=False)
            CANDIDATE.mkdir()
            for n,b in (files|{'plan.json':canonical(plan)}).items():write_bytes(CANDIDATE/n,b)
            print(json.dumps(dict(plan_sha256=content_hash(plan),inputs_sha256=plan['files']['inputs.json'],manifest_sha256=plan['manifest_sha256'],peak_rss_bytes=budget(),accounting=d['accounting'])))
        elif args.publish:
            files={n:read(str(CANDIDATE.relative_to(REPO))+'/'+n) for n in ['inputs.json','derived.json','plan.json']}
            require(digest(files['plan.json'])==args.plan_sha256,'Independent publication plan differs')
            plan=json.loads(files['plan.json']);d=validate_files(files,plan['files']['inputs.json'],plan['manifest_sha256'],plan['code_pins'])
            DEST.mkdir()
            try:
                for n,b in files.items():write_bytes(DEST/n,b)
                source.put(DEST/'publication.json',dict(component='segmenter-dispositions-v1',source_access=False,plan_sha256=args.plan_sha256,peak_rss_bytes=budget()))
                print(json.dumps(dict(receipt_sha256=package(DEST),inputs_sha256=plan['files']['inputs.json'],manifest_sha256=plan['manifest_sha256'],accounting=d['accounting'])))
            except BaseException as e:source.put(DEST/'failure.json',dict(state='incomplete',error=str(e)));raise
        else:
            verify_package(str(DEST.relative_to(REPO)),args.receipt_sha256)
            files={n:read(str(DEST.relative_to(REPO))+'/'+n) for n in ['inputs.json','derived.json','plan.json']};plan=json.loads(files['plan.json'])
            d=validate_files(files,args.inputs_sha256,args.manifest_sha256,plan['code_pins'])
            print(json.dumps(dict(state='resolved',receipt_sha256=args.receipt_sha256,transition_sha256=content_hash(d['transition']),peak_rss_bytes=budget(),accounting=d['accounting'])))
    signal.alarm(0)

if __name__=='__main__':main()
