"""D-315 retained metadata only. Legacy paths/reports are not emitted or resolved."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import resource
import signal
import sys
import time
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import validate_manifest_v3
from src.data.source_inventory_records import content_hash,require,unique

REPO=Path(__file__).resolve().parents[2]
OUT=REPO/'outputs/prowl/STAGE2-METADATA-20261001'
CANDIDATE='outputs/prowl/expansion-v2-candidate-6bc5c245-47b4-45ab-9616-cd75da986b74'
SELECTION='outputs/prowl/localizer-candidates-v2-0d91addc-1ef8-402b-b12a-611aa78f12f9'
PLAN_PIN='e6bda831b66966b3a93f4cdb9c0eab5f7fa86b49313e9141215fd51132e58ab7'
SELECTION_PIN='aa9a77cbcb3848b194a2e1bcb5515174dbf4aa4efa22c18e0d0d7746ec7ab3a7'
MANIFEST_PIN='3f1a54f202773dd2ed7fe8c274385b52f53e8ececedd5c1fe2ec4a07d5065558'
MAX_INPUT_BYTES=64*1024**2
METHOD='stage2-metadata-v1-6positivehint2other-train-2positivehint2other-validation'


def safe_read(root,name,pin):
    rel=PurePosixPath(name)
    require(not rel.is_absolute() and '..' not in rel.parts and bool(rel.parts), 'Unsafe metadata member')
    p=Path(root)/name
    require(p.is_file() and p.resolve(strict=True)==p.absolute() and not any(x.is_symlink() for x in [p,*p.parents]) and p.stat().st_size<=MAX_INPUT_BYTES,'Unsafe/oversized retained metadata')
    b=p.read_bytes();require(digest(b)==pin,'Retained metadata pin changed');return b


def inputs():
    plan=json.loads(safe_read(REPO,CANDIDATE+'/plan.json',PLAN_PIN))
    receipt=json.loads(safe_read(REPO,SELECTION+'/receipt.json',SELECTION_PIN))
    selection_raw=safe_read(REPO,SELECTION+'/selection.json',receipt['files']['selection.json'])
    selection=json.loads(selection_raw);pins=selection['input_pins']
    refs={CANDIDATE+'/plan.json':PLAN_PIN,CANDIDATE+'/derived.json':plan['files']['derived.json'],
          SELECTION+'/receipt.json':SELECTION_PIN,SELECTION+'/selection.json':digest(selection_raw),
          'outputs/manifest.csv':pins['manifest_sha256']}
    refs.update({'outputs/splits/'+filename:pins['membership'][role] for role,filename in [('train','train.txt'),('validation','val.txt'),('test','test.txt')]})
    payload={n:safe_read(REPO,n,p) for n,p in refs.items()}
    require(sum(map(len,payload.values()))<=MAX_INPUT_BYTES,'Metadata total read budget exceeded')
    return refs,payload


def legacy_hints(raw):
    result={}
    for r in csv.DictReader(io.StringIO(raw.decode())):
        sid=r['case_id'];require(sid and sid not in result,'Duplicate legacy metadata study')
        # Deliberate allowlist: do not copy reports, patient identifiers, old absolute paths or clinical assertions.
        flag=r.get('has_lesion','').strip().lower();n=r.get('lesion_voxel_count','').strip()
        count=int(n) if n.isdigit() else None
        hint=True if flag=='true' else False if flag=='false' else None
        result['pants:study:'+sid]=dict(has_lesion_hint=hint,lesion_voxel_count_hint=count,
                                     assurance='legacy_unverified_not_target_status')
    return result


def propose(rows):
    eligible={r['study_id']:r for r in rows if r['localizer_state']=='qualified'}
    picks={'train':[],'validation':[]};reasons={}
    def add(sid,role,reason):
        require(sid in eligible and eligible[sid]['protected_role']==role,'Required proposal anchor unavailable; no refill')
        require(sid not in picks[role],'Duplicate proposal anchor');picks[role].append(sid);reasons[sid]=reason
    def by_code(n):return 'pants:study:PanTS_'+f'{n:08d}'
    for n in [3,26]:add(by_code(n),'train','retained_nonempty_lesion_audit_candidate_not_qualified')
    add(by_code(6110),'train','retained_short_coverage_tiny_pancreas_challenge_no_negative_inference')
    positive=lambda r:r['legacy_hint']['has_lesion_hint'] is True and (r['legacy_hint']['lesion_voxel_count_hint'] or 0)>0
    train=[r for r in eligible.values() if r['protected_role']=='train' and positive(r)]
    require(len(train)>=6,'Positive-hint candidate shortage; do not refill')
    remaining=[r for r in train if r['study_id'] not in picks['train']]
    tiny=min(remaining,key=lambda r:(r['legacy_hint']['lesion_voxel_count_hint'],r['study_id']))
    add(tiny['study_id'],'train','smallest_legacy_positive_count_hint_target_fidelity_candidate')
    for phase in ['arterial','venous']:
        pool=[r for r in train if r['study_id'] not in picks['train'] and r['descriptive_stratum'].startswith(phase+'|')]
        require(pool,'Requested positive-hint phase missing')
        chosen=min(pool,key=lambda r:(0 if r['descriptive_stratum'].endswith('thin_le2mm') else 1,r['study_id']))
        add(chosen['study_id'],'train','positive_hint_'+phase+'_protocol_diversity')
    remaining=[r for r in train if r['study_id'] not in picks['train']]
    largest=max(remaining,key=lambda r:(r['source_voxels'],r['study_id']))
    add(largest['study_id'],'train','largest_remaining_positive_hint_native_grid_resource_candidate')
    for role in ['train','validation']:
        if role=='validation':
            pos=sorted([r for r in eligible.values() if r['protected_role']==role and positive(r)],key=lambda r:r['study_id'])
            require(len(pos)==2,'Validation positive-hint count changed; review selection before new proposal')
            for r in pos:add(r['study_id'],role,'all_current_validation_positive_hints_not_verified')
            add(by_code(2727),role,'retained_single_boundary_slice_tiny_pancreas_challenge_no_negative_inference')
        pool=[r for r in eligible.values() if r['protected_role']==role and r['study_id'] not in picks[role] and
              not positive(r) and r['descriptive_stratum']=='delay|thin_le2mm']
        require(pool,'Delayed/thin candidate missing; no automatic substitution')
        add(min(pool,key=lambda r:r['study_id'])['study_id'],role,'delayed_thin_protocol_candidate_unverified_lesion_status')
    return [dict(**eligible[sid],proposal_reason=reasons[sid],selection_order=i)
            for role in ['train','validation'] for i,sid in enumerate(picks[role])]


def build(payload):
    d=json.loads(payload[CANDIDATE+'/derived.json']);m=d['manifest'];selection=json.loads(payload[SELECTION+'/selection.json'])
    require(content_hash(m)==MANIFEST_PIN,'Retained manifest content changed')
    base={role:payload['outputs/splits/'+name] for role,name in [('train','train.txt'),('validation','val.txt'),('test','test.txt')]}
    validate_manifest_v3(m,base_membership_bytes=base)
    hints=legacy_hints(payload['outputs/manifest.csv']);studies={r['study_id']:r for r in m['studies']};annotations={a['annotation_id']:a for a in m['annotations']}
    holds={r['study_id']:r['reasons'] for r in d['accounting']['held']};qualified={sid for ids in d['accounting']['executable_ids'].values() for sid in ids};rows=[]
    for role in ['train','validation']:
        candidates=selection['candidates'][role]
        require({c['study_id'] for c in candidates}==set(d['accounting']['candidate_ids'][role]),'Candidate membership differs')
        for c in candidates:
            sid=c['study_id'];s=studies[sid];anns=[annotations[aid] for aid in s['annotation_ids']]
            pancreas=[a for a in anns if a['structure']=='pancreas' and a['status']=='eligible']
            current_pancreas=pancreas[0] if len(pancreas)==1 else next(a for a in anns if a['structure']=='pancreas')
            lesion=[a for a in anns if a['structure']=='lesion'];require(len(lesion)<=1,'Ambiguous retained lesion records')
            expected_lesion=dict(root_alias=current_pancreas['file']['root_alias'],uri=str(PurePosixPath(current_pancreas['file']['uri']).with_name('pancreatic_lesion.nii.gz')),
                state='expected_path_only_not_observed',bytes=None,content_sha256=None)
            rows.append(dict(study_id=sid,protected_role=role,descriptive_stratum=c['descriptive_stratum'],
                source_voxels=math.prod(s['geometry']['shape_xyz']) if s['geometry'] else None,
                localizer_state='qualified' if sid in qualified else 'held',localizer_hold_reasons=holds.get(sid,[]),
                segmenter_state='pending_qualification_no_permission',image=s['image'],pancreas=current_pancreas['file'],expected_lesion=expected_lesion,
                legacy_hint=hints[sid],retained_lesion_annotation=lesion[0] if lesion else None,
                difficulty_issues=[i for i in m['issues'] if i['rule_code']=='DIFFICULTY_OBSERVATION' and i['entity_id'] in [sid,*s['annotation_ids']]],
                missing_evidence=['paired_lesion_inventory','current_lesion_geometry_content_and_encoding_review','stage2_dual_target_use_decision',
                    'lesion_target_status_reference_standard_if_empty','new_segmenter_qualification','roi_target_fidelity']))
    require(len(rows)==176 and len(qualified)==153 and len(holds)==23 and qualified|set(holds)=={r['study_id'] for r in rows},'Permanent accounting differs')
    proposal=propose(rows)
    return dict(component='segmenter-candidate-inventory-v1',selection_method=METHOD,
        accounting=dict(original_roles={role:sum(p['protected_role']==role for p in m['protection']) for role in ['train','validation','test']},
            candidates=176,localizer_qualified=153,localizer_held=23,stage2_qualified=0,proposed_train=8,proposed_validation=4,
            source_array_reads=0,source_stat_calls=0,original_membership_changed=False),
        candidates=rows,proposed_candidates=proposal,
        historical_context_outside_candidate_scope=[s['study_id'] for s in m['studies'] if s['study_id'] not in {r['study_id'] for r in rows}],
        next_read_proposal=dict(stage='metadata_stat_then_bounded_lesion_headers_content',files=12,
            inputs=[r['expected_lesion']|dict(study_id=r['study_id'],protected_role=r['protected_role']) for r in proposal],
            compressed_bytes='unknown_until_new_bounded_metadata_stat',existing_pancreas_ct_evidence='reverify exact pins; not automatically reopened',
            no_read_request_issued=True))


def dump(path,data):
    with Path(path).open('xb') as f:f.write(canonical(data))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--replay',action='store_true');a=ap.parse_args();start=time.monotonic()
    def stop(signum,frame):raise TimeoutError('Retained metadata job exceeds 300 seconds')
    signal.signal(signal.SIGALRM,stop);signal.alarm(300)
    # Never resolve a legacy source path or a mask/model file in this metadata-only process.
    def block(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(args[0]).resolve()
            require(not str(p).startswith('/Volumes/') and not p.is_relative_to(Path.home()/'PROWL-Backups') and
                    not str(p).endswith(('.nii','.nii.gz','.pt','.pth')), 'Source arrays/models/external roots forbidden')
    sys.addaudithook(block)
    refs,payload=inputs();result=build(payload);encoded=canonical(result)
    require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)<=2*1024**3 and len(encoded)<=10*1024**2,'Metadata memory/output budget exceeded')
    if a.replay:
        require((OUT/'inventory.json').read_bytes()==encoded,'Exact metadata replay differs');print('Exact fresh-process metadata replay passed')
    else:
        dump(OUT/'inventory-started.json',dict(state='started',decision='D-315',selection_method=METHOD))
        dump(OUT/'input-pins.json',refs);dump(OUT/'inventory.json',result)
        dump(OUT/'inventory-receipt.json',dict(state='proposal_complete_not_qualification',decision='D-315',input_bytes=sum(map(len,payload.values())),
            seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
            files={n:dict(bytes=(OUT/n).stat().st_size,sha256=digest((OUT/n).read_bytes())) for n in ['input-pins.json','inventory.json']},
            source_array_reads=0,source_stat_calls=0,real_qualifications_created=0))
        print(json.dumps(result['accounting']));print('inventory_sha256='+digest(encoded))
    signal.alarm(0)

if __name__=='__main__':main()
