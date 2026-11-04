import numpy as np
import pytest
from src.training.candidate_verifier_v1 import candidates, training_labels, retain_candidates, validate_provenance


def records():
    return [dict(case_id=n,role=r,generator_exposed_ids=['generator_train'],
                 **{k:'a'*64 for k in ('checkpoint_sha256','source_sha256','prediction_sha256','generator_receipt_sha256')})
            for n,r in [('a','fit'),('b','calibration')]]


def test_roles():
    assert validate_provenance(records(), ['a','b','generator_train'], ['dev']) == {'fit':['a'],'calibration':['b']}


@pytest.mark.parametrize('bad', ['own','development','calibration','duplicate','identity','protected'])
def test_leakage_rejected(bad):
    r=records()
    if bad=='own':r[0]['generator_exposed_ids']=['a']
    if bad=='development':r[0]['generator_exposed_ids']=['dev']
    if bad=='calibration':r[0]['generator_exposed_ids']=['b']
    if bad=='duplicate':r.append(r[0])
    if bad=='identity':r[0]['checkpoint_sha256']=''
    if bad=='protected':r[0]['case_id']='dev'
    with pytest.raises(ValueError):validate_provenance(r,['a','b','generator_train'],['dev'])


def test_components_labels_and_identity_gate():
    a=np.zeros((5,5,5),dtype=bool);a[0,0,0]=True;a[1,1,1]=True;a[4,4,4]=True
    labels,rows=candidates(a)
    assert [r['voxels'] for r in rows]==[2,1] # 26-connectivity, retain tiny candidates
    truth=np.zeros_like(a);truth[1,1,1]=True
    assert training_labels(labels,truth)=={1:True,2:False}
    np.testing.assert_array_equal(retain_candidates(labels,{1:0.,2:0.},0),a)
    result=retain_candidates(labels,{1:.8,2:.1},.5)
    assert result.sum()==2 and not (result & ~a).any()


def test_empty_and_all_false_candidates():
    a=np.zeros((2,2,2),dtype=bool);labels,rows=candidates(a)
    assert rows==[] and not retain_candidates(labels,{},.5).any()
    a[0,0,0]=True;labels,_=candidates(a)
    assert training_labels(labels,np.zeros_like(a))=={1:False}


@pytest.mark.parametrize('scores,threshold',[({},.5),({1:float('nan')},.5),({1:.5},-1),({1:.5,2:.2},.5)])
def test_invalid_scores(scores,threshold):
    with pytest.raises(ValueError):retain_candidates(np.ones((2,2,2),dtype=int),scores,threshold)


def test_misaligned_truth():
    with pytest.raises(ValueError):training_labels(np.ones((2,2,2),dtype=int),np.zeros((3,3,3),dtype=bool))
