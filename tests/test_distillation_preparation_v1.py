from types import SimpleNamespace
import pytest
from scripts.diagnostics import prepare_distillation as prep


def test_storage_projection_does_not_assume_compression_or_raise_cap():
    result=prep.storage_projection(15181877307,22957418839,32*1024**3)
    assert result['raw_uint16_bytes']==30363754614 and not result['raw_fits']
    assert result['available_bytes']==11402319529
    assert not result['compression_measured'] and not result['full_cache_authorized']
    with pytest.raises(ValueError):prep.storage_projection(100,101,100)


def test_active_parent_stops_pilot_before_gpu_or_dispatch(tmp_path,monkeypatch):
    from scripts.diagnostics import setup_fast_varied
    from src.operations import full_training_platform
    monkeypatch.setattr(prep,'OUT',tmp_path/'prep');monkeypatch.setattr(prep,'PILOT_CACHE',tmp_path/'cache')
    monkeypatch.setattr(prep,'check_preparation',lambda:None);monkeypatch.setattr(prep,'resources',lambda:None)
    closed=[]
    monkeypatch.setattr(setup_fast_varied,'provider',lambda **kw:SimpleNamespace(control={'validation':['V']},close=lambda:closed.append(True)))
    def unfinished(names):raise ValueError('Parent incomplete')
    monkeypatch.setattr(prep,'normal_parent_gate',unfinished)
    def forbidden(*a,**kw):raise AssertionError('GPU lock/dispatch was reached')
    monkeypatch.setattr(full_training_platform,'training_guard',forbidden)
    monkeypatch.setattr(prep.subprocess,'Popen',forbidden)
    with pytest.raises(ValueError,match='Parent incomplete'):prep.pilot()
    assert closed==[True] and not prep.OUT.exists() and not prep.PILOT_CACHE.exists()


@pytest.mark.parametrize('exists',['pilot','cache'])
def test_existing_pilot_is_never_retried(tmp_path,monkeypatch,exists):
    monkeypatch.setattr(prep,'OUT',tmp_path/'prep');monkeypatch.setattr(prep,'PILOT_CACHE',tmp_path/'cache')
    (prep.OUT/'pilot-01' if exists=='pilot' else prep.PILOT_CACHE).mkdir(parents=True)
    with pytest.raises(ValueError,match='already started'):prep.pilot()
