"""Exercise production service wiring with injected local dependencies, no model/DB."""
from contextlib import contextmanager
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import serve_research_workflow as service
from tests.retrieval.test_research_workflow import inputs, request


@pytest.fixture
def wired(tmp_path, inputs, monkeypatch):
    calls = []
    config = dict(volume_uuid='fixture')
    corpus = dict(encoder_id='fixture', content_sha256='a'*64)
    class DB:
        @contextmanager
        def transaction(self): yield
        def execute(self, sql): calls.append(sql)
    @contextmanager
    def connect(_): yield DB()
    class Model:
        id = 'fixture'
        descriptor = {'fixture': True}
    monkeypatch.setattr(service, 'read_config', lambda _: copy.deepcopy(config))
    monkeypatch.setattr(service, 'limits', lambda _: calls.append('limits'))
    monkeypatch.setattr(service, 'connect', connect)
    monkeypatch.setattr(service, 'snapshot', lambda *_: copy.deepcopy(corpus))
    monkeypatch.setattr(service, 'database_inventory', lambda *_: copy.deepcopy(corpus))
    monkeypatch.setattr(service, 'encoder', lambda _: Model())
    monkeypatch.setattr(service, 'guided_search', lambda *_: calls.append('search') or inputs[0])
    store = service.create_store('fixture-config', tmp_path/'runs')
    store.generate = lambda *_: pytest.fail('Never invoke model in admission checks')
    return store, config, corpus, calls


def test_production_retrieval_identity_and_repeatable_read(wired):
    store, _, corpus, calls = wired
    assert store.binding['retrieval_identity']['corpus'] == corpus
    assert store.binding['retrieval_identity']['catalog_sha256'] == service.digest(service.CATALOG)
    store.retrieve('fixture')
    assert calls.index('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY') < calls.index('search')


def test_changed_database_refuses_before_query_or_model(wired):
    store, _, corpus, calls = wired
    corpus['content_sha256'] = 'b'*64
    failed = store.save(request())
    assert failed['state'] == 'failed' and failed['stages'][0]['reason'] == 'service_unavailable'
    assert 'search' not in calls


def test_changed_configuration_refuses_before_run_directory(wired):
    store, config, _, _ = wired
    config['changed'] = True
    r = request()
    with pytest.raises(ValueError, match='configuration'): store.save(r)
    assert not (store.directory/r['request_id']).exists()


def test_storage_refusal_precedes_encoder_construction(tmp_path, monkeypatch):
    monkeypatch.setattr(service, 'read_config', lambda _: {})
    monkeypatch.setattr(service, 'limits', lambda _: (_ for _ in ()).throw(OSError('floor')))
    monkeypatch.setattr(service, 'encoder', lambda _: pytest.fail('No encoder before admission'))
    with pytest.raises(OSError): service.create_store('fixture', tmp_path/'runs')
    assert not (tmp_path/'runs').exists()
