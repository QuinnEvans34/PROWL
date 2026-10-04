import json
from copy import deepcopy
import pytest
from scripts.diagnostics import segmenter_cache_qualification as q
from src.data.manifest_records import digest
from src.operations.segmenter_cache_storage_v1 import cache_store,ExactCacheStore
from retained_segmenter_metadata import metadata


def retained_inputs():
    saved=metadata()
    return saved['cache_binding'],saved['cache_scope']


def test_committed_retained_inventory_is_exact_no_source_arrays(monkeypatch):
    monkeypatch.setattr(q.loader,'resolve_registered',lambda:pytest.fail('Unexpected registered storage read'))
    monkeypatch.setattr(q.source,'source_stream',lambda *a:pytest.fail('Unexpected source array'))
    b,s=retained_inputs();assert len(b['entries'])==7 and q.cache.checked_binding(b,q.content_hash(b))==104509440
    assert sum(x['compressed_bytes'] for x in s['files'])==145701969 and sum(x['expanded_bytes'] for x in s['files'])==544986944
    assert [e['descriptor']['protected_role'] for e in b['entries']]==['train']*6+['validation']
    assert all(e['fidelity']['outside_pancreas_voxels']>=0 for e in b['entries'])


@pytest.mark.parametrize('fault',['bare_session','wrong_stage','wrong_permission','wrong_pin','held_member','wrong_role','missing_file','duplicate_file'])
def test_exact_read_gate_rejects_before_source_access(monkeypatch,fault):
    b,s=retained_inputs();r=dict(stage='segmenter_cache_build',binding=b,binding_sha256=q.content_hash(b),cases=s['cases'],files=s['files'],capability=s['capability'],model_updates_allowed=False,source_writes=False,cohort_completion_sha256=q.loader.COMPLETION,descriptor_sha256=q.loader.DESCRIPTORS)
    session=q.loader.ResolvedInputs(b['records'],q.loader._TOKEN);sid=b['entries'][0]['descriptor']['study_id'];op='optimizer'
    if fault=='bare_session':session=b['records']
    if fault=='wrong_stage':r['stage']='segmenter_geometry_fidelity'
    if fault=='wrong_permission':r['model_updates_allowed']=True
    if fault=='held_member':sid='pants:study:PanTS_00005641'
    if fault=='wrong_role':op='evaluator'
    if fault=='missing_file':r['files']=r['files'][:-1]
    if fault=='duplicate_file':r['files'][-1]=deepcopy(r['files'][0])
    pin=digest(q.source.encoded(r)) if fault!='wrong_pin' else 'a'*64
    monkeypatch.setattr(q.source,'mount_guard',lambda *a:pytest.fail('Mount touched after denial'))
    with pytest.raises(ValueError):q.read_case(session,r,pin,sid,op,-1,{},lambda:None)


@pytest.mark.parametrize('fault',['pin','area','artifact','decision','model','bytes','registry'])
def test_storage_capability_rejection_precedes_filesystem(tmp_path,monkeypatch,fault):
    cap=json.loads(q.CAP.read_bytes());artifact=cap['artifact_id']
    if fault=='area':cap['area']='localizer-runs'
    if fault=='artifact':artifact='other-cache'
    if fault=='decision':cap['approval']='D-322'
    if fault=='model':cap['model_updates_allowed']=True
    if fault=='bytes':cap['max_new_bytes']+=1
    if fault=='registry':cap['registry_sha256']='0'*64
    raw=q.source.encoded(cap);pin=digest(raw) if fault!='pin' else 'a'*64
    with pytest.raises((ValueError,FileNotFoundError)):cache_store(tmp_path/'missing-registry',raw,trusted_capability_sha256=pin,artifact_id=artifact)


def test_exact_storage_wrapper_never_calls_wrong_artifact():
    class Forbidden:
        root='invented'
        def publish(self,*a,**k):pytest.fail('Wrong artifact written')
        def resolve(self,*a,**k):pytest.fail('Wrong artifact read')
    s=ExactCacheStore(Forbidden(),'expected')
    with pytest.raises(ValueError):s.publish('other')
    with pytest.raises(ValueError):s.resolve('other')


@pytest.mark.parametrize('fault',['request','code','runtime','hash_bytes','decode_bytes','expanded_bytes','read_count','boolean_updates'])
def test_production_is_tied_to_exact_read_transaction(fault):
    from tests.test_segmenter_cache import fixture
    files,b,pin=fixture();p=json.loads(files['production.json'])
    req=dict(binding=b,binding_sha256=pin,code_pins=p['code_pins'],runtime=p['runtime'],limits=p['source_counts'].copy());request_pin=p['request_sha256']
    if fault=='request':p['request_sha256']='d'*64
    if fault=='code':p['code_pins']={'changed.py':'d'*64}
    if fault=='runtime':p['runtime']={'python':'changed'}
    if fault in ('hash_bytes','decode_bytes','expanded_bytes'):p['source_counts'][fault]+=1
    if fault=='read_count':p['source_arrays_read']+=1
    if fault=='boolean_updates':p['model_updates']=False
    files['production.json']=q.canonical(p)
    with pytest.raises(ValueError):q.validate_production(files,req,request_pin)


@pytest.mark.parametrize('field',['bytes','inode','mtime_ns','ctime_ns','mode','retained_sha256','uri','inventory'])
def test_metadata_refresh_never_weakens_content_or_nonvolatile_identity(field):
    saved=metadata();original=saved['refresh_rows'];evidence=saved['refresh_evidence']
    if field in ('bytes','inode','mtime_ns','ctime_ns','mode'):evidence['files'][0]['current'][field]+=1;evidence['files'][0]['changed_fields'].append(field)
    if field=='retained_sha256':evidence['files'][0][field]='a'*64
    if field=='uri':evidence['files'][0]['uri']='changed-path'
    if field=='inventory':evidence['files'].pop()
    with pytest.raises(ValueError):q.refreshed_rows(original,evidence)


def test_metadata_refresh_preserves_every_original_content_pin():
    saved=metadata();original=saved['refresh_rows'];evidence=saved['refresh_evidence'];fresh=q.refreshed_rows(original,evidence)
    assert all({k:v for k,v in a.items() if k!='observation'}=={k:v for k,v in b.items() if k!='observation'} for a,b in zip(original,fresh))
    assert {r['observation']['device'] for r in fresh}=={16777239}
