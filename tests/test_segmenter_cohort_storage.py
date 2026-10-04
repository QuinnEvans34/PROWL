import json
import pytest
from src.data.manifest_records import canonical,digest
from src.operations.segmenter_cohort_storage import ExactStore,segmenter_store
import src.operations.segmenter_cohort_storage as gate


class FakeStore:
    root='invented-only'
    def publish(self,*args,**kwargs):return 'published'
    def resolve(self,*args,**kwargs):return 'resolved'


def test_exact_identity_on_both_operations():
    store=ExactStore(FakeStore(),'exact')
    assert store.publish('exact')=='published' and store.resolve('exact')=='resolved'
    for op in (store.publish,store.resolve):
        with pytest.raises(ValueError):op('different')


@pytest.mark.parametrize('fault',['approval','identity','source','scientific','budget','registry','provider','hash','extra'])
def test_scope_cannot_widen_even_with_rehashed_capability(monkeypatch,fault):
    provider=canonical(dict(registry_sha256='a'*64,volume_uuid='invented'))
    cap=dict(schema_version='1.0.0',approval='D-320',root_alias='prowl_artifacts',area='cohorts',
        operation='publish_and_resolve_exact_segmenter_cohort',artifact_id='exact',scientific_runs_enabled=False,
        registry_sha256='a'*64,volume_uuid='invented',provider_capability_sha256=digest(provider),
        max_bytes=96*1024**2,deadline_seconds=1800,peak_rss_bytes=2*1024**3,source_access=False,model_updates=False)
    monkeypatch.setattr(gate,'cohort_store',lambda *args,**kwargs:FakeStore())
    def call(pin=None):
        raw=canonical(cap)
        return segmenter_store('invented',raw,trusted_capability_sha256=pin or digest(raw),artifact_id='exact',
            provider_capability=provider,trusted_provider_sha256=digest(provider))
    assert call().resolve('exact')=='resolved'
    if fault=='approval':cap['approval']='D-269'
    if fault=='identity':cap['artifact_id']='other'
    if fault=='source':cap['source_access']=True
    if fault=='scientific':cap['scientific_runs_enabled']=True
    if fault=='budget':cap['max_bytes']+=1
    if fault=='registry':cap['registry_sha256']='0'*64
    if fault=='provider':cap['provider_capability_sha256']='0'*64
    if fault=='extra':cap['extra_permission']='all'
    with pytest.raises(ValueError):call('f'*64 if fault=='hash' else None)
