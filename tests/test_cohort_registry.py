from copy import deepcopy
import json
import pytest
import src.data.cohort_registry as registry
from qualification_fixtures import fixture,add_qualification
from src.data.manifest_records import canonical,digest
from src.data.manifest_records_v3 import build_manifest_v3
from src.data.source_inventory_records import content_hash


def synthetic(monkeypatch):
    args,ctx=fixture()
    a=args['annotations'][1];a.update(status='eligible',allowed_uses=['training_target'],issue_ids=[])
    args['issues']=[]
    ctx['manifest']=build_manifest_v3(**args);ctx['trusted_manifest_sha256']=content_hash(ctx['manifest'])
    add_qualification(ctx,0);add_qualification(ctx,1)
    ids=[args['studies'][n]['study_id'] for n in (0,1)]
    monkeypatch.setattr(registry,'MEMBERS',ids)
    monkeypatch.setattr(registry,'qualification_context',lambda *a,**kw:deepcopy(ctx))
    # This isolates ancestry/selection checks; retained real history is separately replayed natively.
    files=registry.build_bundle({'verification.json':canonical(dict(files={}))},
        trusted_s3_receipt_sha256='a'*64,current_manifest_sha256=ctx['trusted_manifest_sha256'])
    return files,ctx


def test_three_protection_parents_and_exact_child(monkeypatch):
    files,ctx=synthetic(monkeypatch)
    result=registry.validate_bundle(files,trusted_s3_receipt_sha256='a'*64,current_manifest_sha256=ctx['trusted_manifest_sha256'])
    assert result['protected_counts']==dict(train=2,validation=1,test=1)
    assert len(result['study_ids'])==2


@pytest.mark.parametrize('fault',['parent','member','selection','extra','role','qualification'])
def test_no_parent_omission_refill_or_permission_bypass(monkeypatch,fault):
    files,ctx=synthetic(monkeypatch)
    if fault=='parent':files['parents.json']=canonical(json.loads(files['parents.json'])[:-1])
    if fault=='member':
        c=json.loads(files['cohort.json']);c['members'].pop();files['cohort.json']=canonical(c)
    if fault=='selection':
        s=json.loads(files['selection.json']);s['shortage_policy']='refill';files['selection.json']=canonical(s)
    if fault=='extra':files['surprise.json']=b'{}'
    if fault=='role':
        c=json.loads(files['cohort.json']);c['members'][0]['protected_role']='validation';files['cohort.json']=canonical(c)
    if fault=='qualification':
        ctx['qualifications_by_id']={};ctx['trusted_qualification_sha256']={}
        monkeypatch.setattr(registry,'qualification_context',lambda *a,**kw:deepcopy(ctx))
    with pytest.raises((ValueError,KeyError)):
        registry.validate_bundle(files,trusted_s3_receipt_sha256='a'*64,current_manifest_sha256=ctx['trusted_manifest_sha256'])


def test_untrusted_s3_refused_before_parsing():
    with pytest.raises(ValueError,match='receipt pin'):
        registry.qualification_context({'s3-verification.json':b'{}'},trusted_s3_receipt_sha256='a'*64,
                                      current_manifest_sha256='b'*64)


def test_rehashed_current_context_cannot_revoke_hold_silently():
    receipt=canonical(dict(status='s3_qualification_complete_not_cohort_publication',files={}))
    files={'s3-verification.json':receipt,'s3-manifests.json':canonical([{}, {}, {}, {}]),
           's3-qualifications.json':canonical([{}, {}, {}]),'s3-transitions.json':canonical([{}, {}, {}])}
    with pytest.raises(ValueError,match='Current authorization'):
        registry.qualification_context(files,trusted_s3_receipt_sha256=digest(receipt),current_manifest_sha256='b'*64)
