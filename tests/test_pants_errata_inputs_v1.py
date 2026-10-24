from copy import deepcopy
import numpy as np
import pytest
from src.data.pants_errata_inputs_v1 import ErrataInputs
from src.data.segmenter_varied_region_v1 import VariedInputs
from src.data.pants_errata_v1 import EXPECTED
from src.data.segmenter_native_windows_v1 import geometry
from src.data.segmenter_pancreas_region_v1 import bank
from src.training.segmenter_augmentation_v1 import augment


def provider(monkeypatch):
    def init(self, **kwargs):
        self.control = dict(train=sorted(EXPECTED)+['unaffected'], validation=['dev'])
        self.pin = 'original'; self.component_cache = {}
        self.planned_counts = {n:12 for n in self.control['train']}
    monkeypatch.setattr(VariedInputs, '__init__', init)
    monkeypatch.setattr(ErrataInputs, 'corrected_target', lambda self,n: (None,None))
    return ErrataInputs(correction_root='unused', correction_manifest_sha256='a'*64, overlay_sha256='b'*64)


def test_new_identity_and_unchanged_routing(monkeypatch):
    p = provider(monkeypatch)
    assert p.pin != 'original'
    assert p.control['label_revision']['original_provider_sha256'] == 'original'
    calls = []
    monkeypatch.setattr(VariedInputs, 'load', lambda self,n,**kw: calls.append((n,kw)) or 'original')
    assert p.load('dev',role='validation',operation='evaluator') == 'original'
    assert p.load('unaffected',role='train',operation='optimizer') == 'original'
    assert len(calls)==2
    with pytest.raises(ValueError): p.load('dev',role='validation',operation='optimizer')
    with pytest.raises(ValueError): p.load(sorted(EXPECTED)[0],role='validation')


def test_corrected_sampling_and_augmentation_replay(monkeypatch):
    p = provider(monkeypatch); name = sorted(EXPECTED)[0]
    g = geometry((150,150,150),np.eye(4))
    y = np.zeros((150,)*3,np.uint8); y[65:85,60:90,50:100]=1
    case = dict(name=name, image=np.full(y.shape,.4,np.float32),target=y,geometry=g,
                source_sha256={'lesion':'corrected'},region_low=[0]*3,region_high=[150]*3)
    monkeypatch.setattr(p,'load',lambda *a,**kw: deepcopy(case))
    for step,visit in [(0,0),(1,1),(3,1)]:
        a=p.training_window(name,step=step,focused_visit=visit,seed=42)
        b=p.training_window(name,step=step,focused_visit=visit,seed=42)
        assert np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1])
        assert a[3] == b[3] and not a[3]['positive_case'] and not (a[1]==2).any()
        x,y,trace=augment(*a[:3],seed=42,update=step+1,case_id=name)
        xx,yy,other=augment(*b[:3],seed=42,update=step+1,case_id=name)
        assert np.array_equal(x,xx) and np.array_equal(y,yy) and trace==other
