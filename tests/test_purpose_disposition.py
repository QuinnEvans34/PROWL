"""Invented records only; no real decision publication or source data access."""
from copy import deepcopy
import pytest

from test_annotation_contract_v2 import approved
from test_manifest_records import inputs
from src.data.manifest_records import canonical, digest, validate_schema
from src.data.purpose_disposition import make_purpose_issue, check_purpose

pytestmark = pytest.mark.unit
NOW = '2026-09-28T00:00:00Z'
ISSUE = 'issue:10000000-0000-4000-8000-000000000001'


def fixture(case=78, rule='PANCREAS_PRESENT_TARGET_EXCLUDED', purpose='pancreas_present_localizer'):
    study = inputs()['studies'][0]
    raw_id = f'PanTS_{case:08d}'
    study.update(study_id='pants:study:'+raw_id, subject_id='pants:subject:'+raw_id,
                 source_study_id=raw_id, source_partition='publisher_train', status='eligible', issue_ids=[])
    annotation = approved()
    annotation.update(annotation_id='pants:annotation:'+raw_id+'-pancreas-fixture',
                      study_id=study['study_id'], source_snapshot_id=study['source_snapshot_id'],
                      structure='pancreas', source_structure='pancreas')
    annotation['label_encoding']['mapping']['canonical_foreground'] = 1
    study['annotation_ids'] = [annotation['annotation_id']]
    decision, evidence = b'Invented reviewer decision', b'Invented coverage or geometry evidence'
    issue = make_purpose_issue(study=study, annotation=annotation, purpose=purpose,
                              rule_code=rule, decision_sha256=digest(decision),
                              evidence_sha256=digest(evidence), issue_id=ISSUE, created_at=NOW)
    return dict(study=study, annotation=annotation, purpose=purpose, protected_role='train',
                existing_issues=[], purpose_issues=[issue],
                trusted_study_sha256=digest(canonical(study)),
                trusted_annotation_sha256=digest(canonical(annotation)),
                trusted_issue_sha256={ISSUE:digest(canonical(issue))},
                evidence_by_sha256={digest(decision):decision,digest(evidence):evidence},
                trusted_evidence_sha256=frozenset((digest(decision),digest(evidence))))


def repin(args):
    """Tests simulate separate review to reach deeper binding checks, never production guidance."""
    args['trusted_study_sha256'] = digest(canonical(args['study']))
    args['trusted_annotation_sha256'] = digest(canonical(args['annotation']))
    args['trusted_issue_sha256'] = {r['issue_id']:digest(canonical(r))
                                  for r in args['existing_issues']+args['purpose_issues']}


def test_localizer_exclusion_replay_and_preservation():
    args = fixture(); before = deepcopy(args)
    result = check_purpose(**args)
    assert result['outcome'] == 'rejected'
    assert result['reasons'] == ['PANCREAS_PRESENT_TARGET_EXCLUDED']
    assert result['allowed_uses'] == [] and result['eligibility'] == 'not_granted'
    assert result['protected_membership'] == 'unchanged' and result['preserve_source']
    assert args == before and canonical(result) == canonical(check_purpose(**args))
    validate_schema('data-issue', result['new_issues'][0])
    result['new_issues'][0]['message'] = 'mutated result'
    assert args == before


@pytest.mark.parametrize('case', [2,266])
@pytest.mark.parametrize('purpose', ['pancreas_present_localizer','geometry_dependent_training',
                                     'anatomy_absent_robustness'])
def test_unit_holds_even_with_plausible_geometry_and_broad_permission(case,purpose):
    args = fixture(case,'PHYSICAL_UNITS_UNRESOLVED',purpose)
    assert args['study']['geometry'] is not None
    assert args['annotation']['allowed_uses'] == ['training_target']
    result = check_purpose(**args)
    assert result['reasons'] == ['PHYSICAL_UNITS_UNRESOLVED']
    assert result['eligibility'] == 'not_granted'


@pytest.mark.parametrize('fault', ['study_pin','annotation_pin','issue_pin','bytes','evidence_pin',
                                  'missing_evidence','extra_evidence','missing_issue_pin'])
def test_independent_pin_and_bytes_rejection(fault):
    args=fixture()
    if fault=='study_pin': args['trusted_study_sha256']='a'*64
    if fault=='annotation_pin': args['trusted_annotation_sha256']='a'*64
    if fault=='issue_pin': args['trusted_issue_sha256'][ISSUE]='a'*64
    if fault=='bytes': args['evidence_by_sha256'][next(iter(args['evidence_by_sha256']))]=b'changed'
    if fault=='evidence_pin': args['trusted_evidence_sha256']=frozenset()
    if fault=='missing_evidence': args['evidence_by_sha256']={}
    if fault=='extra_evidence':
        h=digest(b'extra');args['evidence_by_sha256'][h]=b'extra'
        args['trusted_evidence_sha256'] |= {h}
    if fault=='missing_issue_pin':args['trusted_issue_sha256']={}
    with pytest.raises(ValueError):check_purpose(**args)


@pytest.mark.parametrize('field', ['study','snapshot','ct_sha256','annotation_sha256','purpose','policy'])
def test_rehashed_issue_cannot_override_context_bindings(field):
    args=fixture()
    ref=next(r for r in args['purpose_issues'][0]['evidence'] if r['reference'].startswith(field+'='))
    ref['reference']=field+'=wrong'
    repin(args)
    with pytest.raises(ValueError,match='binding'):check_purpose(**args)


@pytest.mark.parametrize('fault', ['duplicate_issue','duplicate_rule','dangling','wrong_entity',
    'unknown_rule','conflict','resolution','supersedes','duplicate_evidence','unknown_purpose',
    'changed_purpose','wrong_role','test_partition','unknown_units'])
def test_malformed_conflicting_or_missing_qualification(fault):
    args=fixture();issue=args['purpose_issues'][0]
    if fault=='duplicate_issue': args['purpose_issues'].append(deepcopy(issue))
    if fault=='duplicate_rule':
        other=deepcopy(issue);other['issue_id']='issue:20000000-0000-4000-8000-000000000002'
        args['purpose_issues'].append(other)
    if fault=='dangling':args['study']['issue_ids']=[ISSUE]
    if fault=='wrong_entity':issue['entity_id']='pants:annotation:other'
    if fault=='unknown_rule':issue['rule_code']='UNKNOWN_POLICY'
    if fault=='conflict':issue['disposition']='retain'
    if fault=='resolution':issue['disposition']='resolved_by_new_artifact'
    if fault=='supersedes':issue['supersedes_issue_id']='issue:20000000-0000-4000-8000-000000000002'
    if fault=='duplicate_evidence':issue['evidence'].append(deepcopy(issue['evidence'][0]))
    if fault=='unknown_purpose':args['purpose']='training'
    if fault=='changed_purpose':args['purpose']='anatomy_absent_robustness'
    if fault=='wrong_role':args['protected_role']='validation'
    if fault=='test_partition':args['study']['source_partition']='publisher_test'
    if fault=='unknown_units':
        args['study'].update(geometry=None,status='discovered');repin(args)
        assert 'GEOMETRY_UNRESOLVED' in check_purpose(**args)['reasons'];return
    repin(args)
    with pytest.raises(ValueError):check_purpose(**args)


def test_no_case_number_inference_or_automatic_clearance():
    for purpose in ('pancreas_present_localizer','anatomy_absent_robustness'):
        args=fixture(case=3)
        args.update(purpose=purpose,purpose_issues=[],trusted_issue_sha256={},
                    evidence_by_sha256={},trusted_evidence_sha256=frozenset())
        result=check_purpose(**args)
        assert result['reasons']==['PURPOSE_DECISION_MISSING']
        assert result['outcome']=='rejected' and result['allowed_uses']==[]


def test_attached_denial_cannot_be_hidden_as_history():
    args=fixture();args['existing_issues']=args['purpose_issues'];args['purpose_issues']=[]
    args['annotation']['issue_ids']=[ISSUE];repin(args)
    result=check_purpose(**args)
    assert 'PANCREAS_PRESENT_TARGET_EXCLUDED' in result['reasons']
    assert 'EXISTING_BLOCKING_ISSUE' in result['reasons']
    assert not result['new_issues']


def test_other_quarantine_preserved_and_cross_entity_reference_rejected():
    args=fixture();old=deepcopy(args['purpose_issues'][0])
    old.update(issue_id='issue:20000000-0000-4000-8000-000000000002',
               rule_code='SOURCE_PROVENANCE_PENDING',entity_type='study',
               entity_id=args['study']['study_id'],disposition='quarantine')
    args['existing_issues']=[old];args['study']['issue_ids']=[old['issue_id']]
    args['study']['status']='quarantined';repin(args);before=deepcopy(args)
    result=check_purpose(**args)
    assert {'EXISTING_BLOCKING_ISSUE','RECORD_QUALIFICATION_PENDING'} <= set(result['reasons'])
    assert args==before
    args['annotation']['issue_ids']=[old['issue_id']];repin(args)
    with pytest.raises(ValueError,match='wrong entity'):check_purpose(**args)


def test_synthetic_consumer_refuses_before_selecting_members():
    selected=[]
    def consume(args):
        check=check_purpose(**args)
        if check['outcome']=='rejected':raise ValueError('Purpose gate rejected')
        selected.append(args['study']['study_id'])
    for args in (fixture(),fixture(266,'PHYSICAL_UNITS_UNRESOLVED')):
        with pytest.raises(ValueError,match='Purpose gate'):consume(args)
    assert selected==[]


def test_new_issue_integrates_without_promoting_or_changing_prior_inputs():
    from src.data.manifest_records_v2 import assemble_manifest_v2
    import json
    args=fixture();before=deepcopy(args)
    result=check_purpose(**args)
    data=inputs()
    study=deepcopy(args['study']);annotation=deepcopy(args['annotation'])
    annotation['issue_ids']=[ISSUE]
    data['subjects'][0].update(subject_id=study['subject_id'],source_subject_id=study['source_study_id'])
    data.update(studies=[study],annotations=[annotation],issues=result['new_issues'])
    first=assemble_manifest_v2(**data)
    assert json.loads(first['manifest.json'])['status']=='quarantined'
    assert first==assemble_manifest_v2(**data)
    assert args==before


@pytest.mark.parametrize('fault', ['unknown_rule','wrong_purpose','bad_hash','wrong_target'])
def test_issue_proposal_rejects_unsupported_inputs(fault):
    args=fixture()
    kw=dict(study=args['study'],annotation=args['annotation'],purpose=args['purpose'],
            rule_code='PANCREAS_PRESENT_TARGET_EXCLUDED',decision_sha256='a'*64,
            evidence_sha256='b'*64,issue_id=ISSUE,created_at=NOW)
    if fault=='unknown_rule':kw['rule_code']='CLEAR_FOR_TRAINING'
    if fault=='wrong_purpose':kw['purpose']='anatomy_absent_robustness'
    if fault=='bad_hash':kw['decision_sha256']='not-a-hash'
    if fault=='wrong_target':kw['annotation']['structure']='lesion'
    with pytest.raises(ValueError):make_purpose_issue(**kw)
