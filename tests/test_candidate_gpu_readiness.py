"""CPU-only candidate ownership checks; never start a model or real service."""
import fcntl
from types import SimpleNamespace
import pytest
from scripts.retrieval import prepare_local_expert as prep
from scripts import serve_single_summary_candidate as candidate
from src.operations import full_training_platform as platform


def setup_health(monkeypatch):
    config={'storage':'invented'}
    health={'backend':'checked','storage_identity':prep.digest(config),
            'answer_policy':'single-pass-summary-v1','answer_gpu_reserved':True}
    monkeypatch.setattr(prep,'gpu_busy',lambda:True)
    monkeypatch.setattr(prep,'read_config',lambda _:config)
    monkeypatch.setattr(prep,'http',lambda *a:health)
    return health


def test_own_candidate_reservation_allows_proxy_answers(monkeypatch):
    setup_health(monkeypatch)
    assert not prep.answer_gpu_busy()
    assert prep.gpu_busy()  # Preparation still cannot load another model.


@pytest.mark.parametrize('field,value',[
    ('backend','unavailable'),('storage_identity','old'),
    ('answer_policy','other'),('answer_gpu_reserved',False),
    ('answer_gpu_reserved','true'),
])
def test_other_or_unverified_owner_blocks_answers(monkeypatch,field,value):
    health=setup_health(monkeypatch);health[field]=value
    assert prep.answer_gpu_busy()


def test_failed_health_blocks_answers(monkeypatch):
    setup_health(monkeypatch)
    def fail(*args): raise OSError('offline')
    monkeypatch.setattr(prep,'http',fail)
    assert prep.answer_gpu_busy()


def test_candidate_reservation_lifetime_and_cleanup(tmp_path,monkeypatch):
    monkeypatch.setattr(candidate,'ROOT',tmp_path)
    monkeypatch.setattr(platform,'require_ac',lambda:None)
    service=SimpleNamespace()
    monkeypatch.setattr(candidate,'create_service',lambda _:service)
    monkeypatch.setattr(candidate,'create_study_answers',lambda _:(object(),None))
    monkeypatch.setattr(candidate,'handler_for',lambda *a:None)
    closed=[]
    class Server:
        def __init__(self,*args): pass
        def serve_forever(self):
            assert service.answer_gpu_reserved is True
            with (tmp_path/'outputs/prowl/.mps-profile.lock').open('a+b') as handle:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            raise RuntimeError('synthetic shutdown')
        def server_close(self):
            assert service.answer_gpu_reserved is True
            closed.append(True)
    monkeypatch.setattr(candidate,'LocalFixtureServer',Server)
    with pytest.raises(RuntimeError,match='synthetic shutdown'):
        candidate.run_candidate('invented',8021)
    assert closed==[True] and service.answer_gpu_reserved is False
    with (tmp_path/'outputs/prowl/.mps-profile.lock').open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)


def test_busy_teacher_prevents_candidate_creation(tmp_path,monkeypatch):
    monkeypatch.setattr(candidate,'ROOT',tmp_path)
    monkeypatch.setattr(candidate,'create_service',lambda _:pytest.fail('must not create candidate'))
    lock=tmp_path/'outputs/prowl/.mps-profile.lock';lock.parent.mkdir(parents=True)
    with lock.open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            candidate.run_candidate('invented',8021)
