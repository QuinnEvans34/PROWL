import copy
import hashlib
import numpy as np
import pytest
from src.inference.physical_cascade_comparison_v1 import compare_arrays,same_sources,CORE,RULE


def data():
    p=np.zeros((3,10,10,20),np.float32);p[0]=.5;p[1]=.3;p[2]=.2
    c=np.zeros(p.shape[1:],np.uint8)
    return p,c,c.copy()


def test_exact_and_predeclared_small_difference():
    p,c,m=data();q=p.copy();q[0]+=1e-6;q[1]-=1e-6
    r=compare_arrays(p,q,c,c,m,m)
    assert r['passed'] and r['probability_values_outside_tolerance']==0
    assert r['max_probability_absolute_difference']>0


def test_failure_not_hidden_by_zero_hard_disagreement():
    p,c,m=data();q=p.copy();q[0]+=.01;q[1]-=.01
    r=compare_arrays(p,q,c,c,m,m)
    assert not r['passed'] and r['hard_code_disagreements']==0
    assert r['probability_values_outside_tolerance']>0


@pytest.mark.parametrize('which',['codes','localizer'])
def test_hard_threshold_boundary(which):
    p,c,m=data();other=c.copy();other.flat[:2]=1
    args=(p,p,c,other,m,m) if which=='codes' else (p,p,c,c,m,other)
    assert compare_arrays(*args)['passed'] # Exactly2/2000=.001
    other.flat[2]=1
    assert not compare_arrays(*args)['passed']


@pytest.mark.parametrize('kind',['nan','range','normalization','dtype','shape'])
def test_invalid_probability_never_passes(kind):
    p,c,m=data();q=p.copy()
    if kind=='nan':q[0,0,0,0]=np.nan
    if kind=='range':q[0,0,0,0]=-1
    if kind=='normalization':q*=.9
    if kind=='dtype':q=q.astype(np.float64)
    if kind=='shape':q=q[:,:,:,:-1]
    with pytest.raises(ValueError):compare_arrays(p,q,c,c,m,m)


def test_source_equivalence_only_line_endings(tmp_path):
    a={'pins':{}};b={'pins':{}}
    for name in CORE:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'known\nsource\n')
        a['pins']['C:/repo/'+name]=hashlib.sha256(b'known\r\nsource\r\n').hexdigest()
        b['pins']['/repo/'+name]=hashlib.sha256(p.read_bytes()).hexdigest()
    assert len(same_sources(a,b,tmp_path))==len(CORE)
    b['pins']['/repo/'+CORE[0]]='0'*64
    with pytest.raises(ValueError,match='source mismatch'):same_sources(a,b,tmp_path)
