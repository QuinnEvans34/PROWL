from copy import deepcopy
import json
import threading
import numpy as np
import pytest
import torch
from src.data.segmenter_fast_varied_v1 import normalize_region,save_target,FastVariedInputs
from src.data.segmenter_native_windows_v1 import geometry,orient
from src.data.segmenter_physical_windows_v1 import physical_geometry,sample_window
from src.training.segmenter_fast_varied_session_v1 import member_at,FastVariedSession
from src.training.segmenter_full_session_v1 import Session


@pytest.mark.parametrize('affine',[
    np.diag([.7,.8,3.,1.]),np.array([[0,-.7,0,10],[.9,0,0,-5],[0,0,-2.5,9],[0,0,0,1.]]),
    np.array([[1.,.2,0,0],[0,.8,.1,0],[0,0,1.5,0],[0,0,0,1.]])])
def test_pointwise_normalization_commutes_with_region_crop_exactly(affine):
    image=np.random.default_rng(2).normal(0,250,(18,20,22)).astype(np.float32)
    image[0,0,:5]=[-100,250,-99.123,249.99,1e10]
    parent=geometry(image.shape,affine);lo=[1,2,3];hi=[n-1 for n in parent['shape']]
    old=orient(image.copy(),parent);np.clip(old,-100,250,out=old);old+=100;old/=350
    old=np.ascontiguousarray(old[tuple(slice(a,b) for a,b in zip(lo,hi))])
    new=normalize_region(image,parent,lo,hi)
    assert np.array_equal(old,new) and new.dtype==np.float32
    affine2=np.array(parent['affine']);affine2[:3,3]=(affine2@[*lo,1])[:3]
    record=physical_geometry(geometry(new.shape,affine2))
    assert np.array_equal(sample_window(old,record,(0,0,0),order=1)[0],sample_window(new,record,(0,0,0),order=1)[0])


def test_nonfinite_ct_not_hidden_by_cropping():
    image=np.ones((5,5,5),np.float32);image[0,0,0]=np.nan
    with pytest.raises(ValueError,match='Nonfinite'):
        normalize_region(image,geometry(image.shape,np.eye(4)),[1]*3,[4]*3)


def test_target_cache_lossless_and_exclusive(tmp_path):
    y=np.random.default_rng(42).integers(0,3,(10,12,14),dtype=np.uint8)
    meta={'geometry':{'shape':list(y.shape)}}
    result=save_target(tmp_path,'case',y,meta)
    assert result['bytes']>0
    with np.load(tmp_path/'case.npz',allow_pickle=False) as data:assert np.array_equal(data['target'],y)
    with pytest.raises(FileExistsError):save_target(tmp_path,'case',y,meta)


def test_member_at_matches_actual_session_across_epoch_boundaries():
    session=object.__new__(Session);session.control={'train':[f'case{i}' for i in range(7)]}
    session.config={'seed':42,'max_steps':40};session._epoch=None;session._order=None
    before=torch.get_rng_state().clone()
    for step in range(40):
        session.step=step
        assert member_at(session.control['train'],step,42)==session.next_member()
    assert torch.equal(before,torch.get_rng_state())


def stub_provider():
    from concurrent.futures import ThreadPoolExecutor
    p=object.__new__(FastVariedInputs)
    p._executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='prowl-input-test')
    p._future=None;p._future_key=None;p._next=None;p._closed=False
    p._produce=lambda key:key
    p.cache_member=lambda name:None
    return p


def test_one_lookahead_exact_request_and_clean_close(monkeypatch):
    monkeypatch.setattr('src.data.segmenter_fast_varied_v1.source_info',lambda *a,**k:None)
    p=stub_provider()
    try:
        p.plan_next(('b',1,0,42))
        assert p.training_window('a',step=0,focused_visit=0,seed=42)==('a',0,0,42)
        p.wait_pending()
        assert p.training_window('b',step=1,focused_visit=0,seed=42)==('b',1,0,42)
    finally:p.close()
    assert not any(t.name.startswith('prowl-input-test') for t in threading.enumerate())
    with pytest.raises(ValueError,match='closed'):p.plan_next(None)


def test_prefetch_mismatch_fails_without_silent_fallback():
    p=stub_provider()
    try:
        p.plan_next(('b',1,0,42));p.training_window('a',step=0,focused_visit=0,seed=42)
        with pytest.raises(ValueError,match='order/counters'):p.training_window('b',step=1,focused_visit=1,seed=42)
    finally:p.close()


def test_prefetch_worker_failure_surfaces_and_closes():
    p=stub_provider()
    def bad(key):raise ValueError('source failure')
    p._future=p._executor.submit(bad,('b',1,0,42));p._future_key=('b',1,0,42)
    with pytest.raises(ValueError,match='source failure'):p.close()
    assert p._closed and not any(t.name.startswith('prowl-input-test') for t in threading.enumerate())


def test_validation_delegates_to_unchanged_reader(monkeypatch):
    from src.data.segmenter_varied_region_v1 import VariedInputs
    p=stub_provider();calls=[]
    monkeypatch.setattr(VariedInputs,'load',lambda self,name,**kw:calls.append((name,kw)) or 'original')
    try:assert p.load('dev',role='validation',operation='evaluator')=='original'
    finally:p.close()
    assert calls==[('dev',{'role':'validation','operation':'evaluator'})]


def test_cache_member_corruption_rejected(tmp_path):
    y=np.zeros((4,4,4),np.uint8);meta={'geometry':{'shape':[4,4,4]}}
    p=object.__new__(FastVariedInputs);p.target_cache=tmp_path
    p.cache_manifest={'members':{'a':save_target(tmp_path,'a',y,meta)}}
    p.cache_member('a')
    (tmp_path/'a.json').write_text('{}')
    with pytest.raises(ValueError,match='member changed'):p.cache_member('a')


@pytest.mark.parametrize('members,complete,qualification,allowed',[
    ({'a':{}},True,False,True),({'a':{}},False,False,False),
    ({'a':{}},False,True,True),({'dev':{}},True,True,False)])
def test_manifest_admission_and_partial_cache_never_promoted(tmp_path,monkeypatch,members,complete,qualification,allowed):
    from src.data.segmenter_varied_region_v1 import VariedInputs
    from src.data.segmenter_pancreas_region_v1 import POLICY as REGION
    from src.data.manifest_records import canonical,digest
    from src.training.experiment_config import sha256
    base=dict(train=['a'],validation=['dev'],policy={'source':'native'})
    def init(p,**kwargs):p.control=deepcopy(base)
    monkeypatch.setattr(VariedInputs,'__init__',init)
    expected=deepcopy(base);expected['source_loader_policy']=expected.pop('policy');expected['policy']=deepcopy(REGION)
    manifest=tmp_path/'manifest.json'
    manifest.write_bytes(canonical(dict(source_control_sha256=digest(canonical(expected)),members=members,complete=complete)))
    kwargs=dict(target_cache=tmp_path,cache_manifest_sha256=sha256(manifest),qualification_only=qualification)
    if allowed:
        p=FastVariedInputs(**kwargs)
        try:assert bool(p.control.get('qualification_only'))==qualification
        finally:p.close()
    else:
        with pytest.raises(ValueError):FastVariedInputs(**kwargs)
