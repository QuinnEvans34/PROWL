from copy import deepcopy
import pytest
from test_qualification_transition import setup
from src.data.localizer_qualification_records import qualify_successor, migrate_context
from src.data.manifest_records_v3 import build_manifest_v3


def inputs():
    old,args,ctx,kw=setup()
    a=args['annotations'][0]
    return old,args,dict(prior=kw['prior_manifest'],study_id=a['study_id'],
        mapping=a['label_encoding']['mapping'],provenance=a['provenance'],evidence=ctx['evidence_by_sha256'])


def test_builder_replays_and_keeps_history_and_unrelated_hold():
    old,args,kw=inputs();before=deepcopy(kw)
    after,q,cert,evidence=qualify_successor(**kw)
    assert kw==before
    assert q['outcome']=='qualified'
    assert len(after['issues'])==len(kw['prior']['issues'])-3
    assert after['issues'][0] in kw['prior']['issues']
    assert qualify_successor(**kw)==(after,q,cert,evidence)


@pytest.mark.parametrize('fault',['specific_hold','unknown_hold','missing_evidence','reference_permission','per_file_claim'])
def test_builder_does_not_turn_review_failures_into_passes(fault):
    old,args,kw=inputs()
    if fault in ('specific_hold','unknown_hold'):
        old['issues'][-1]['rule_code']='PHYSICAL_UNITS_UNRESOLVED' if fault=='specific_hold' else 'NEW_HOLD'
        kw['prior']=build_manifest_v3(**old)
    if fault=='missing_evidence':kw['evidence']={}
    if fault=='reference_permission':kw['provenance']['allowed_use_decision_file']=None
    if fault=='per_file_claim':kw['provenance']['scope']='per_file_review'
    with pytest.raises((ValueError,TypeError)):qualify_successor(**kw)


def test_migration_preserves_all_holds_and_rejects_permission():
    old,args,kw=inputs()
    # Use one detailed case plus full synthetic protection/source scope.
    prior={c:deepcopy(old[c][:1]) for c in ('subjects','studies','annotations')}
    subject,study,a=(prior[c][0] for c in ('subjects','studies','annotations'))
    study['annotation_ids']=[a['annotation_id']]
    ids={*subject['issue_ids'],*study['issue_ids'],*a['issue_ids']}
    prior['issues']=[i for i in old['issues'] if i['issue_id'] in ids]
    prior['snapshot']=old['snapshots'][0]
    before=deepcopy(prior)
    result=migrate_context(prior=prior,snapshot=args['snapshots'][0],protection=args['protection'])
    assert prior==before and result['issues']==sorted(prior['issues'],key=lambda i:i['issue_id'])
    prior['annotations'][0]['allowed_uses']=['training_target']
    with pytest.raises(ValueError,match='permissions'):
        migrate_context(prior=prior,snapshot=args['snapshots'][0],protection=args['protection'])
