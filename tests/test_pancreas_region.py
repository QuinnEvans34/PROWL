import numpy as np
import pytest
from src.data.segmenter_native_windows_v1 import geometry,orient
from src.data.segmenter_pancreas_region_v1 import source_box,oriented_box,crop_case,window_origin


def test_region_uses_pancreas_only_and_preserves_flip_alignment():
    shape=(250,220,190);pan=np.zeros(shape,np.uint8);pan[110:125,90:100,80:90]=1
    a=np.diag([-1.,2.,-3.,1.]);g=geometry(list(shape),a)
    lo,hi=source_box(pan,a);ol,oh=oriented_box(pan,g)
    marker=np.zeros(shape,np.uint8);marker[tuple(slice(l,h) for l,h in zip(lo,hi))]=1
    expected=orient(marker,g)
    assert expected.sum()==np.prod(oh-ol)
    assert expected[tuple(slice(l,h) for l,h in zip(ol,oh))].all()
    case=dict(original_pancreas=pan,geometry=g,target=orient(pan,g),image=orient(pan.astype(np.float32),g))
    first=crop_case(case);case['target']=np.full_like(case['target'],2);second=crop_case(case)
    assert first['region_low']==second['region_low'] and first['region_high']==second['region_high']
    assert first['target'].sum()==pan.sum()
    assert first['geometry']['affine']==second['geometry']['affine']


def test_global_mix_and_independent_focus_counter():
    record=dict(shape=[220,220,220]);cover=[(0,0,0),(76,76,76)];counts={'a':0,'b':0,'c':0};kinds=[]
    for step in range(48):
        name=['a','b','c'][step%3]
        origin,kind=window_origin(record,cover,step=step,focused_visit=counts[name],seed=42,name=name)
        assert (origin,kind)==window_origin(record,cover,step=step,focused_visit=counts[name],seed=42,name=name)
        kinds.append(kind)
        if kind=='focused_cover':
            assert origin==cover[counts[name]%2];counts[name]+=1
        else:assert all(0<=v<=76 for v in origin)
    assert all(kinds[i:i+4].count('region_context')==1 for i in range(0,48,4))
    assert counts==dict(a=12,b=12,c=12)


@pytest.mark.parametrize('affine',[
    np.array([[0.,-2.,0.,60.],[1.,0.,0.,-30.],[0.,0.,3.,2.],[0.,0.,0.,1.]]),
    np.array([[-1.,.1,0.,80.],[0.,2.,0.,-30.],[0.,0.,-3.,2.],[0.,0.,0.,1.]])])
def test_permuted_oblique_region_reembeds_in_native_space(affine,monkeypatch):
    from types import SimpleNamespace
    from src.training import segmenter_pancreas_region_session_v1 as mod
    shape=(230,190,150);pan=np.zeros(shape,np.uint8);pan[100:120,80:95,60:75]=1
    lesion=np.zeros_like(pan);lesion[105:110,85:90,65:70]=1
    target=pan.copy();target[lesion!=0]=2;g=geometry(list(shape),affine)
    parent=dict(original_pancreas=pan,original_lesion=lesion,geometry=g,target=orient(target,g),image=orient(pan.astype(np.float32),g))
    case=crop_case(parent)
    def predict(raw,image,geo,progress):return case['target'],dict(gap_voxels=0)
    monkeypatch.setattr(mod,'predict_native',predict)
    class Provider:
        def load(self,name,*,role,operation):
            assert role=='validation' and operation=='evaluator'
            return case
    result=mod.evaluate(SimpleNamespace(raw=None,step=1),Provider(),'example',lambda *a:None)
    assert result['metrics']['lesion']['dice']==1
    assert result['reconstruction']['lesion_guided_region'] is False


def test_adapter_rejects_development_optimization():
    from src.training.segmenter_pancreas_region_session_v1 import Adapter
    from types import SimpleNamespace
    adapter=Adapter(SimpleNamespace(control={}),None)
    with pytest.raises(ValueError):adapter.get('heldout',role='validation',operation='optimizer')


def test_focus_counter_integrity_is_checked():
    from src.training.segmenter_pancreas_region_session_v1 import RegionSession
    from types import SimpleNamespace
    raw=SimpleNamespace(control={'train':['a','b']},identity={},exposure={'a':2,'b':2},step=4)
    s=RegionSession(raw)
    with pytest.raises(ValueError):s.check()
    s.focused={'a':2,'b':1};s.check()
    s.focused={'a':3,'b':0}
    with pytest.raises(ValueError):s.check()
