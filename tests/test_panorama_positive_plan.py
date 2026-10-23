import copy
import pytest
from scripts.diagnostics.plan_panorama_positive_cohort import plan


def fixture():
    row=dict(study_id='a',subject_id='s',publisher_study_id='1',disposition='expert_pdac_candidate_pending_qc_and_duplicates',lesion_method='human_manual',pdac='positive',training_ready=False,protected_role='unassigned',ct={'expected_sha256':'x'},label={'expected_sha256':'y'})
    audit=dict(study_id='a',status='ct_content_pass_not_admitted',ct_sha256='x',label_sha256='y')
    return row,audit


def test_candidate_not_admission():
    r,a=fixture();out=plan([r],[a]);assert out['admitted']==0 and not out['candidates'][0]['training_ready']


def test_subject_grouping():
    r,a=fixture();r2=copy.deepcopy(r);a2=dict(a);r2['study_id']=a2['study_id']='b';r2['publisher_study_id']='2'
    out=plan([r2,r],[a,a2]);assert out['studies']==2 and out['subjects']==1 and out['repeated_subject_groups']==1


@pytest.mark.parametrize('field,value',[('training_ready',True),('protected_role','test'),('lesion_method','machine_generated')])
def test_invalid_candidate_refused(field,value):
    r,a=fixture();r[field]=value
    with pytest.raises(ValueError):plan([r],[a])


def test_hash_mismatch_refused():
    r,a=fixture();a['ct_sha256']='changed'
    with pytest.raises(ValueError):plan([r],[a])


def test_held_stays_out():
    r,a=fixture();a['status']='held';assert plan([r],[a])['studies']==0


def test_duplicate_identity_refused():
    r,a=fixture()
    with pytest.raises(ValueError):plan([r,r],[a,a])
