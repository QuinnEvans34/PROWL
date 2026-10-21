import copy
import json
from pathlib import Path
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
import pytest

from src.review.store import ReviewStore, ReviewError, digest, encode, FILES
from scripts.serve_reviews import create_app


@pytest.fixture
def package(tmp_path):
    folder = tmp_path/'source'; folder.mkdir()
    refs = {}
    # These are explicitly invented transport bytes, never a scientific model result.
    for key, name in FILES.items():
        data = (key+' invented bytes').encode()
        (folder/name).write_bytes(data)
        refs[key] = dict(uri=name,bytes=len(data),content_sha256=digest(data))
    manifest = dict(schema_version='saved-prediction-view-v2',case_id='invented_case',status='completed',
                    prediction_mode='autonomous',reference_inputs_used=False,model_sha256={'localizer':'a'*64,'segmenter':'b'*64},
                    geometry=dict(units='mm',shape=[2,2,2],affine=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]),
                    ct_window=[-100,300],labels={'0':'background','1':'pancreas','2':'lesion'},warnings=['Invented transport fixture'],
                    files=refs,result_sha256=refs['result']['content_sha256'],inference_evidence_sha256=refs['evidence']['content_sha256'])
    (folder/'manifest.json').write_bytes(encode(manifest))
    return folder


@pytest.fixture
def store(tmp_path, package): return ReviewStore(tmp_path/'records', package, floor_bytes=0)


def request(store, **change):
    body = dict(request_id=str(uuid.uuid4()),manifest_sha256=store.target('saved')['manifest_sha256'],
                expected_latest_id=None, reviewer=dict(reviewer_id='Invented test operator',role='research_operator'),
                action='edit_required',reason_codes=['boundary_correction'],note='Synthetic test only')
    return dict(body, **change)


def test_save_restart_reopen_revision_and_idempotent_retry(store, package):
    body = request(store)
    first = store.append('saved',body)
    h = body['manifest_sha256']
    assert first['receipt']['content_sha256'] == digest(encode(first['event']))
    original = (store.root/first['receipt']['location']).read_bytes()
    shutil.rmtree(package)  # on-demand cleanup/source unavailable does not erase the review
    restarted = ReviewStore(store.root,floor_bytes=0)
    assert restarted.append('saved',body) == first  # acknowledgment lost, original source gone
    assert restarted.target('archive/'+h)['history'] == [first]
    for name in FILES.values(): assert restarted.reader('archive/'+h)(name,1024)
    revised = dict(body,request_id=str(uuid.uuid4()),expected_latest_id=first['event']['review_event_id'],action='reject',reason_codes=['missed_lesion'])
    second = restarted.append('archive/'+h,revised)
    assert second['event']['revision'] == 2 and second['event']['supersedes_review_event_id'] == first['event']['review_event_id']
    assert (store.root/first['receipt']['location']).read_bytes() == original
    assert restarted.packages()[0]['latest'] == second['event']


def test_concurrent_writers_one_stale(store):
    bodies = [request(store),request(store)]
    def write(body):
        try: return ReviewStore(store.root,store.saved,floor_bytes=0).append('saved',body)
        except ReviewError as e: return e
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(write,bodies))
    assert sum(isinstance(r,ReviewError) for r in results) == 1
    assert len(store.target('saved')['history']) == 1


def test_duplicate_token_different_content_refused(store):
    body=request(store);store.append('saved',body)
    with pytest.raises(ReviewError,match='different content'):store.append('saved',dict(body,note='changed'))


@pytest.mark.parametrize('field,value', [('action','unknown'),('reason_codes',['contour_acceptable']),('reason_codes',[]),('reason_codes',['other']),('reviewer',{'reviewer_id':' ','role':'research_operator'})])
def test_invalid_decisions_never_saved(store,field,value):
    with pytest.raises(ReviewError):store.append('saved',request(store,**{field:value, **({'note':''} if value == ['other'] else {})}))
    assert not store.packages()


def test_changed_prediction_cannot_receive_stale_decision(store,package):
    body=request(store)
    m=json.loads((package/'manifest.json').read_bytes());m['case_id']='another_invented_case';(package/'manifest.json').write_bytes(encode(m))
    with pytest.raises(ReviewError,match='Prediction changed'):store.append('saved',body)
    assert not store.packages()


def test_corrupt_file_and_symlink_refused(store,package):
    body=request(store);p=package/'prediction.nii.gz';p.write_bytes(b'wrong')
    with pytest.raises(ReviewError,match='Prediction changed'):store.append('saved',body)
    p.unlink();p.symlink_to(package/'ct.nii.gz')
    with pytest.raises(ReviewError,match='unsafe'):store.append('saved',body)
    assert not store.packages()


def test_disk_failure_never_receipts_and_retry_preserves_only_one_event(store,monkeypatch):
    body=request(store)
    import src.review.store as module
    real=module.write_new
    def fail(path,data):
        if path.name.startswith('.event-'):raise OSError('invented disk error')
        return real(path,data)
    monkeypatch.setattr(module,'write_new',fail)
    with pytest.raises(OSError):store.append('saved',body)
    assert store.target('saved')['history']==[]
    monkeypatch.setattr(module,'write_new',real)
    assert store.append('saved',body)['event']['revision']==1


def test_acknowledgment_failure_retries_same_durable_event(store,monkeypatch):
    body=request(store)
    import src.review.store as module
    real=module.sync_dir
    def fail(path):
        if list(path.glob('event-*.json')):raise OSError('invented sync error')
        return real(path)
    monkeypatch.setattr(module,'sync_dir',fail)
    with pytest.raises(OSError):store.append('saved',body)
    monkeypatch.setattr(module,'sync_dir',real)
    assert store.append('saved',body)['event']['revision']==1
    assert len(store.target('saved')['history'])==1


def test_storage_limit_no_eviction(store):
    store.floor_bytes=10**20
    with pytest.raises(ReviewError,match='limit'):store.append('saved',request(store))
    assert not store.packages()


def test_history_corruption_fails_closed(store):
    saved=store.append('saved',request(store));path=store.root/saved['receipt']['location']
    record=json.loads(path.read_bytes());record['event']['note']='tampered';path.write_bytes(encode(record))
    with pytest.raises(ReviewError,match='integrity'):store.target('saved')


def test_http_roundtrip_refusals_and_restart(store):
    body=request(store)
    with TestClient(create_app(store), base_url='http://127.0.0.1:8018') as client:
        assert client.get('/review-records/targets/saved').json()['history']==[]
        assert client.post('/review-records/targets/saved',json=body,headers={'Origin':'https://example.org'}).status_code==403
        assert client.get('/review-records/packages',headers={'Host':'evil.example'}).status_code==403
        assert client.post('/review-records/targets/saved',content='a'*9000,headers={'Content-Type':'application/json'}).status_code==400
        assert client.get('/review-records/targets/job/not-an-id').status_code==404
        assert client.post('/review-records/targets/saved',json=body).status_code==200
    with TestClient(create_app(ReviewStore(store.root, floor_bytes=0)), base_url='http://127.0.0.1:8018') as client:
        h=body['manifest_sha256']
        assert len(client.get('/review-records/packages').json()['packages'])==1
        assert len(client.get('/review-records/targets/archive/'+h).json()['history'])==1
        for name in ['manifest.json',*FILES.values()]: assert client.get(f'/review-records/packages/{h}/files/{name}').status_code==200
        assert client.get(f'/review-records/packages/{h}/files/private.json').status_code==404
        assert client.post('/review-records/targets/saved',json=body).json()['event']['revision']==1
