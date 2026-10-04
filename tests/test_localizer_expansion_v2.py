"""Synthetic successor and hold regressions; no source payloads."""
import json
from copy import deepcopy
import pytest
from test_localizer_expansion import inputs
from src.data.localizer_expansion import derive as old_derive
from src.data.localizer_expansion_v2 import derive,freeze_records,consume
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import build_manifest_v3
from src.data.source_inventory_records import content_hash


def fresh():
    args=inputs();m=args['prior'];ids=set(args['facts'])
    subjects={s['subject_id'] for s in m['studies'] if s['study_id'] in ids}
    m['studies']=[s for s in m['studies'] if s['study_id'] not in ids]
    m['annotations']=[a for a in m['annotations'] if a['study_id'] not in ids]
    m['subjects']=[s for s in m['subjects'] if s['subject_id'] not in subjects]
    args['prior']=build_manifest_v3(**{k:m[k] for k in ('name','snapshots','protection','subjects','studies','annotations','issues','qualification_policy_sha256')})
    return args


def change(args,sid,fn):
    f=json.loads(args['facts'][sid]);r=json.loads(args['review_bytes']);row=next(x for x in r['cases'] if x['study_id']==sid)
    fn(f,row);args['facts'][sid]=canonical(f);row['facts_sha256']=digest(args['facts'][sid]);args['review_bytes']=canonical(r)


def test_successor_preserves_all_old_issues_annotations_and_replays():
    args=inputs(held=True);m,q,e=old_derive(**args);args.update(prior=m,evidence=e)
    new,qs,ev=derive(**args)
    assert all(i in new['issues'] for i in m['issues'])
    assert [x['outcome'] for x in qs]==['qualified','held']
    assert {a['annotation_id'] for a in new['annotations']}=={a['annotation_id'] for a in m['annotations']}
    assert derive(**args)==(new,qs,ev)


def test_empty_target_is_held_not_negative_and_cannot_refill():
    args=fresh();sid=list(args['facts'])[1]
    def empty(f,r):
        f.update(holds=['empty_pancreas_reference'],semantic_values=[{'value':0,'count':4}],review_planes=[])
        f['decode']['foreground_voxels']=0;r.update(assessment='not_reviewed_empty_reference',reviewed_planes=[],retained_automated_holds=f['holds'])
    change(args,sid,empty);m,q,e=derive(**args)
    assert next(x for x in q if x['study_id']==sid)['outcome']=='held'
    a=next(a for a in m['annotations'] if a['study_id']==sid);assert a['allowed_uses']==[]
    s=next(s for s in m['studies'] if s['study_id']==sid);assert s['target_statuses'][0]['status']=='unknown'
    expected={'train':[next(iter(args['facts']))],'validation':[]}
    expected['validation']=[sid]
    with pytest.raises(ValueError,match='reviewed subset'):freeze_records(m,q,e,None,expected_members=expected)


@pytest.mark.parametrize('fault',['missing_review','role','crc','unit_hold_removed','empty_hold_removed','unreviewed','permissions','changed_predecessor'])
def test_invalid_qualification_refused(fault):
    args=fresh();sid=next(iter(args['facts']))
    if fault=='missing_review':
        r=json.loads(args['review_bytes']);r['cases'].pop();args['review_bytes']=canonical(r)
    elif fault=='permissions':args['use_ref']['content_sha256']='f'*64
    elif fault=='changed_predecessor':
        args=inputs();m,q,e=old_derive(**args);args.update(prior=m,evidence=e)
        change(args,sid,lambda f,r:f['files'][0].update(content_sha256='f'*64))
    else:
        def mutate(f,r):
            if fault=='role':f['protected_role']='validation'
            elif fault=='crc':f['files'][0]['gzip_eof_crc_verified']=False
            elif fault=='unit_hold_removed':f['files'][0]['units'][0]='unknown'
            elif fault=='empty_hold_removed':f['decode']['foreground_voxels']=0;r['assessment']='not_reviewed_empty_reference'
            else:r['assessment']='pending'
        change(args,sid,mutate)
    with pytest.raises(ValueError):derive(**args)


def test_difficulty_retained_and_role_consumption_checked():
    args=fresh();m,q,e=derive(**args)
    expected={r:[c['study_id'] for c in args['selection']['candidates'][r]] for r in ('train','validation')}
    parents,children=freeze_records(m,q,e,None,expected_members=expected)
    assert all(x['outcome']=='qualified' for x in q)
    for op,role in [('optimizer','train'),('evaluator','validation')]:
        assert [x['study_id'] for x in consume(m,q,e,None,parents,children,operation=op,current_manifest_sha256=content_hash(m))]==expected[role]
    with pytest.raises(ValueError,match='Current manifest'):consume(m,q,e,None,parents,children,operation='optimizer',current_manifest_sha256='0'*64)
    children[1]['protected_role']='train'
    with pytest.raises(ValueError):consume(m,q,e,None,parents,children,operation='evaluator',current_manifest_sha256=content_hash(m))


@pytest.mark.parametrize('delta,accepted',[(1e-8,True),(2e-5,False)])
def test_geometry_uses_pinned_audit_absolute_tolerance(delta,accepted):
    args=fresh();sid=next(iter(args['facts']))
    change(args,sid,lambda f,r:f['files'][1]['affine'][0].__setitem__(3,delta))
    if accepted:derive(**args)
    else:
        with pytest.raises(ValueError,match='Geometry evidence'):derive(**args)


def test_retained_package_refuses_member_omission_or_mutation():
    from scripts.diagnostics.freeze_localizer_expansion_v2 import verified_package
    payload='synthetic';raw=canonical({'files':{'facts.json':digest(payload.encode())}}).decode();pin=digest(raw.encode())
    assert verified_package(raw,{'facts.json':payload},pin)
    for files in [{},{'facts.json':'changed'}]:
        with pytest.raises(ValueError):verified_package(raw,files,pin)


def test_inherited_blocking_issue_cannot_be_promoted_by_clean_new_checks():
    from src.data.localizer_expansion import issue
    args=inputs();m,q,e=old_derive(**args);sid=next(iter(args['facts']))
    s=next(s for s in m['studies'] if s['study_id']==sid)
    denial=issue(sid,'SOURCE_USE_UNRESOLVED','Synthetic later denial',digest(b'hold'),created_at=args['recorded_at'])
    m['issues'].append(denial);s['issue_ids'].append(denial['issue_id'])
    m=build_manifest_v3(**{k:m[k] for k in ('name','snapshots','protection','subjects','studies','annotations','issues','qualification_policy_sha256')})
    args.update(prior=m,evidence=e);new,qs,ev=derive(**args)
    assert denial in new['issues']
    assert next(q for q in qs if q['study_id']==sid)['outcome']=='held'


def test_validation_reuse_detects_mutation_and_revalidates_after_session(monkeypatch):
    import src.data.manifest_records_v3 as module
    m=inputs()['prior'];original=module._validate_manifest_v3;calls=[]
    def counted(*args,**kwargs):
        calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(module,'_validate_manifest_v3',counted)
    with module.manifest_validation_session():
        module.validate_manifest_v3(m);module.validate_manifest_v3(deepcopy(m));assert len(calls)==1
        bad=deepcopy(m);bad['protection'].pop()
        with pytest.raises(ValueError):module.validate_manifest_v3(bad)
        module.validate_manifest_v3(m);assert len(calls)==2
    module.validate_manifest_v3(m);assert len(calls)==3


def test_validation_reuse_keys_membership_and_schema_bytes(monkeypatch,tmp_path):
    import src.data.manifest_records_v3 as module
    m=inputs()['prior'];calls=[]
    # The counting validator isolates cache invalidation; full semantic rejection is tested above.
    def counted(*args,**kwargs):calls.append(1);return {}
    monkeypatch.setattr(module,'_validate_manifest_v3',counted);monkeypatch.setattr(module,'CONTRACTS',tmp_path)
    schema=tmp_path/'synthetic.schema.json';schema.write_text('{}')
    with module.manifest_validation_session():
        module.validate_manifest_v3(m,base_membership_bytes={'train':b'a'})
        module.validate_manifest_v3(m,base_membership_bytes={'train':b'b'})
        schema.write_text('{"type":"object"}')
        module.validate_manifest_v3(m,base_membership_bytes={'train':b'b'})
        assert len(calls)==3


def test_validation_reuse_cannot_hide_python_tuple_as_json_array():
    import src.data.manifest_records_v3 as module
    m=inputs()['prior']
    with module.manifest_validation_session():
        module.validate_manifest_v3(m)
        changed=deepcopy(m);changed['protection']=tuple(changed['protection'])
        assert canonical(changed)==canonical(m)
        with pytest.raises(ValueError,match='JSON-shaped'):module.validate_manifest_v3(changed)
