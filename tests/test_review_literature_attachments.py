import json
import shutil

import pytest
from test_review_store import package, store, request
from test_case_literature_workflow_v1 import capture_fixture
from src.review.store import digest, encode
from src.review.literature_attachments_v1 import LiteratureAttachments

NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(not NODE, reason='Node24 required')


@pytest.fixture
def setup(tmp_path, store):
    record = store.append('saved', request(store))
    root = tmp_path/'attachments'; root.mkdir()
    service = LiteratureAttachments(root, store, node=NODE, minimum_free_bytes=0)
    raw = encode(capture_fixture())
    args = dict(manifest_sha256=record['event']['case_package_id'].split(':')[1],
                review_event_id=record['event']['review_event_id'],
                review_receipt_sha256=digest(encode(record['receipt'])),
                capture=raw, capture_sha256=digest(raw))
    return service, args, record


def test_attach_retry_reopen_and_later_revision_preserve_original(setup):
    service, args, record = setup
    event_path = service.reviews.root/record['receipt']['location']
    before = event_path.read_bytes()
    first = service.attach(**args)
    second = service.attach(**args)
    assert first['state'] == 'published' and second['state'] == 'reused'
    assert first['receipt_sha256'] == second['receipt_sha256']
    newer = service.reviews.append('archive/'+args['manifest_sha256'], request(service.reviews,
        expected_latest_id=args['review_event_id'], action='reject', reason_codes=['missed_lesion']))
    restarted = LiteratureAttachments(service.root, service.reviews, node=NODE, minimum_free_bytes=0)
    opened = restarted.reopen(first['artifact_id'], first['receipt_sha256'])
    assert opened['review'] == record and newer['event']['revision'] == 2
    assert opened['binding']['decision_changed'] is False
    assert opened['binding']['measurement_qualification'] == 'not_evaluated'
    assert opened['capture'] == json.loads(args['capture'])
    assert event_path.read_bytes() == before


@pytest.mark.parametrize('fault', ['case','event','receipt','capture','citation','oversize'])
def test_invalid_attachment_never_published(setup, fault):
    service, args, _ = setup
    if fault == 'case': args['manifest_sha256'] = '0'*64
    if fault == 'event': args['review_event_id'] = 'review:00000000-0000-4000-8000-000000000000'
    if fault == 'receipt': args['review_receipt_sha256'] = '0'*64
    if fault == 'capture': args['capture_sha256'] = '0'*64
    if fault == 'citation':
        c = json.loads(args['capture']); c['response']['answer']['claims'][0]['citations'][0]['quote'] = 'unsupported'
        args['capture'] = encode(c); args['capture_sha256'] = digest(args['capture'])
    if fault == 'oversize': args['capture'] = b' '* (1024**2+1)
    with pytest.raises(ValueError): service.attach(**args)
    assert not list(service.root.glob('*/complete.json'))


@pytest.mark.parametrize('kind', ['refusal','insufficient','unavailable'])
def test_preserves_non_answer_outcomes(setup,kind):
    service,args,_ = setup
    args['capture'] = encode(capture_fixture(kind)); args['capture_sha256'] = digest(args['capture'])
    result = service.attach(**args)
    opened = service.reopen(result['artifact_id'], result['receipt_sha256'])
    assert opened['capture'] == capture_fixture(kind)


@pytest.mark.parametrize('fault', ['member','receipt','review'])
def test_reopen_rejects_tampering(setup, fault):
    service,args,record = setup
    result = service.attach(**args)
    if fault == 'member':
        path = service.root/digest(result['artifact_id'].encode())/'capture.json'; path.write_bytes(b'{}')
    if fault == 'receipt': result['receipt_sha256'] = '0'*64
    if fault == 'review':
        path = service.reviews.root/record['receipt']['location']
        value = json.loads(path.read_bytes()); value['event']['note'] = 'changed'; path.write_bytes(encode(value))
    with pytest.raises(Exception): service.reopen(result['artifact_id'], result['receipt_sha256'])


def test_capacity_rejection_does_not_change_review(setup):
    service,args,record = setup
    path = service.reviews.root/record['receipt']['location']; before = path.read_bytes()
    service.store.minimum_free_bytes = 10**30
    with pytest.raises(ValueError, match='reserve'): service.attach(**args)
    assert path.read_bytes() == before
    assert not list(service.root.glob('*/complete.json'))


def test_replaced_attachment_root_rejected(setup):
    service,args,_ = setup
    service.root.rename(service.root.with_name('old')); service.root.mkdir()
    with pytest.raises(ValueError, match='root changed'): service.attach(**args)
