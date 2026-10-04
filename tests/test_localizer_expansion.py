"""Invented evidence only; pinning does not imply anatomical or source-rights truth."""
import json
from copy import deepcopy
import pytest
from jsonschema import ValidationError
from qualification_fixtures import fixture
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import content_hash
from src.data.localizer_expansion import derive,evidence_ref,freeze_records,consume,issue


def inputs(held=False):
    _,ctx=fixture();m=ctx['manifest'];e=dict(ctx['evidence_by_sha256'])
    payload=b'Synthetic scoped use';use=evidence_ref('use.txt',payload,'text/plain');e[digest(payload)]=payload
    source=evidence_ref('source.txt',b'Synthetic publisher provenance','text/plain');e[source['content_sha256']]=b'Synthetic publisher provenance'
    selection={'candidates':{'train':[],'validation':[]}};facts={};reviews=[]
    for index,role in [(0,'train'),(2,'validation')]:
        s=m['studies'][index];a=next(a for a in m['annotations'] if a['study_id']==s['study_id']);sid=s['study_id']
        files=[]
        for kind,ref in [('ct',s['image']),('pancreas',a['file'])]:
            files.append(dict(kind=kind,source={'uri':ref['uri']},compressed_bytes=ref['bytes'],content_sha256=ref['content_sha256'],gzip_eof_crc_verified=True,
                shape=[2,2,1],affine=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],units=['unknown' if held and role=='validation' or kind=='pancreas' else 'mm','unknown'],effective_scaling={'slope':1,'intercept':0}))
        f=dict(study_id=sid,protected_role=role,files=files,holds=['physical_units_unresolved'] if held and role=='validation' else [],
            ct_finite=True,geometry_matches=True,decode={'foreground_voxels':1},semantic_values=[{'value':0,'count':3},{'value':1,'count':1}],review_planes=[[2,0]])
        facts[sid]=canonical(f)
        selection['candidates'][role].append(dict(study_id=sid,protected_role=role,inventory_inputs=[{'uri':f['source']['uri']} for f in files]))
        reviews.append(dict(study_id=sid,protected_role=role,facts_sha256=digest(facts[sid]),assessment='no_obvious_gross_displacement_in_sampled_views',
            reviewed_planes=f['review_planes'],retained_automated_holds=f['holds'],observations=['Synthetic noise; retain.']))
    return dict(recorded_at='2026-09-29T00:00:00Z',prior=m,bases=None,evidence=e,facts=facts,review_bytes=canonical({'cases':reviews}),selection=selection,use_ref=use,source_ref=source,
        mapping=m['annotations'][0]['label_encoding']['mapping'])


def test_derivation_preserves_old_holds_and_roles_and_replays():
    args=inputs();m,q,e=derive(**args)
    assert all(i in m['issues'] for i in args['prior']['issues'])
    assert m['protection']==args['prior']['protection']
    assert {r['outcome'] for r in q}=={'qualified'}
    assert derive(**args)==(m,q,e)
    expected={role:[c['study_id'] for c in args['selection']['candidates'][role]] for role in ('train','validation')}
    parents,children=freeze_records(m,q,e,None,expected_members=expected)
    for op,role in [('optimizer','train'),('evaluator','validation')]:
        members=consume(m,q,e,None,parents,children,operation=op,current_manifest_sha256=content_hash(m))
        assert [x['study_id'] for x in members]==expected[role]
    val=next(a for a in m['annotations'] if a['annotation_id']==q[1]['annotation_id'])
    assert val['allowed_uses']==['evaluation_reference']
    with pytest.raises(ValueError,match='Current manifest'):consume(m,q,e,None,parents,children,operation='optimizer',current_manifest_sha256='0'*64)
    children[1]['protected_role']='train'
    with pytest.raises(ValueError):consume(m,q,e,None,parents,children,operation='evaluator',current_manifest_sha256=content_hash(m))


def test_unit_hold_survives_and_no_shortage_refill():
    args=inputs(held=True);m,q,e=derive(**args)
    assert q[1]['outcome']=='held'
    a=next(a for a in m['annotations'] if a['annotation_id']==q[1]['annotation_id']);assert a['allowed_uses']==[]
    expected={r:[c['study_id'] for c in args['selection']['candidates'][r]] for r in ('train','validation')}
    with pytest.raises(ValueError,match='reviewed subset'):freeze_records(m,q,e,None,expected_members=expected)


@pytest.mark.parametrize('fault',['facts','missing_review','role','crc','existing_hold','permissions','units'])
def test_changed_or_unsupported_evidence_refused(fault):
    args=inputs();sid=next(iter(args['facts']));r=json.loads(args['review_bytes'])
    if fault=='missing_review':r['cases'].pop()
    elif fault=='role':args['selection']['candidates']['train'][0]['protected_role']='validation'
    elif fault=='existing_hold':
        from src.data.manifest_records_v3 import build_manifest_v3
        m=args['prior'];subject=m['subjects'][0]
        hold=issue(sid,'SOURCE_USE_UNRESOLVED','Synthetic retained denial.',digest(b'review'),'subject',subject['subject_id'],created_at='2026-09-29T00:00:00Z')
        m['issues'].append(hold);subject['issue_ids']=[hold['issue_id']]
        args['prior']=build_manifest_v3(**{k:m[k] for k in ('name','snapshots','protection','subjects','studies','annotations','issues','qualification_policy_sha256')})
    elif fault=='permissions':args['use_ref']['content_sha256']='f'*64
    else:
        f=json.loads(args['facts'][sid])
        if fault=='crc':f['files'][0]['gzip_eof_crc_verified']=False
        elif fault=='units':f['files'][0]['units'][0]='unknown'
        else:f['ct_range']=[-1,1]
        args['facts'][sid]=canonical(f)
        if fault!='facts':r['cases'][0]['facts_sha256']=digest(args['facts'][sid])
    args['review_bytes']=canonical(r)
    with pytest.raises((ValueError,ValidationError)):
        derive(**args)
