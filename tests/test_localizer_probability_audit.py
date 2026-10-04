import numpy as np
import pytest
from src.training.localizer_probability_audit import audit_probabilities, require_baseline_parity


def fixture():
    y = np.zeros((4,4,4),np.uint8);y[1:3,1:3,1:3]=1
    fg = np.zeros(y.shape, np.float32)+.01;fg[y==1]=.5
    p = np.stack([1-fg,fg])
    a=np.diag([3.,3.,3.,1.]).tolist()
    t=dict(processed_shape=list(y.shape),source_shape=list(y.shape),processed_affine=a,source_affine=a)
    return p,y,t


def test_ties_quantiles_and_empty_baseline():
    p,y,t=fixture();r=audit_probabilities(p,y,t)
    assert r['operating_points']['argmax']['predicted_voxels']==0
    assert r['operating_points']['0.5']['true_positive']==8
    assert r['operating_points']['0.01']['predicted_voxels']==64
    assert r['distributions']['missed_reference']['quantiles']['50']==.5
    assert r['operating_points']['argmax']['source_crop_geometry']['scan_fraction'] is None
    assert not r['policy_selected']


@pytest.mark.parametrize('bad', ['nan','inf','negative','large','unnormalized','shape','target'])
def test_bad_probabilities_refused(bad):
    p,y,t=fixture()
    if bad=='nan':p[0,0,0,0]=np.nan
    if bad=='inf':p[0,0,0,0]=np.inf
    if bad=='negative':p[0,0,0,0]=-.1
    if bad=='large':p[0,0,0,0]=1.1
    if bad=='unnormalized':p[:,0,0,0]=.2
    if bad=='shape':p=p[:1]
    if bad=='target':y[:]=0
    with pytest.raises(ValueError):audit_probabilities(p,y,t)


def test_no_missed_reference_and_exact_parity():
    p,y,t=fixture();p[1][y==1]=.9;p[0]=1-p[1]
    r=audit_probabilities(p,y,t);m=r['operating_points']['argmax']
    assert r['distributions']['missed_reference']==dict(count=0,quantiles=None)
    original=dict(role='evaluator',study_id='case',step=2400,metrics=m.copy())
    require_baseline_parity(m,original,role='evaluator',study_id='case')
    with pytest.raises(ValueError):require_baseline_parity(m,original,role='optimizer',study_id='case')
    original['metrics']['predicted_voxels']+=1
    with pytest.raises(ValueError):require_baseline_parity(m,original,role='evaluator',study_id='case')
