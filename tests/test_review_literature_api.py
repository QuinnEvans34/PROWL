import json
from fastapi.testclient import TestClient
import pytest
from test_review_literature_attachments import setup, store, package
from scripts.serve_reviews import create_app
from src.review.store import encode, digest


def client_for(service):
    return TestClient(create_app(service.reviews,attachments=service),base_url='http://127.0.0.1:8018')


def test_api_attach_list_reopen_retry_and_original_review(setup):
    service,args,record=setup;client=client_for(service)
    route=f"/review-records/literature/{args['manifest_sha256']}/{args['review_event_id']}"
    body={'capture_text':args['capture'].decode(),'review_receipt':record['receipt']}
    assert client.get(route).json()=={'attachments':[]}
    first=client.post(route,json=body);assert first.status_code==200,first.text
    saved=first.json();assert saved['state']=='published'
    again=client.post(route,json=body);assert again.status_code==200
    assert again.json()['receipt_sha256']==saved['receipt_sha256']
    rows=client.get(route).json()['attachments'];assert len(rows)==1
    opened=client.get(f"/review-records/literature-capture/{saved['artifact_id'].split(':')[1]}/{saved['receipt_sha256']}")
    assert opened.status_code==200 and opened.json()['review']==record
    assert opened.json()['capture']==json.loads(args['capture'])
    assert service.reviews.target('saved')['history']==[record]
    wrong=client.get(route.replace(args['manifest_sha256'],'0'*64));assert wrong.json()=={'attachments':[]}


def test_rejected_origin_wrong_receipt_and_large_request(setup):
    service,args,record=setup;client=client_for(service)
    route=f"/review-records/literature/{args['manifest_sha256']}/{args['review_event_id']}"
    body={'capture_text':args['capture'].decode(),'review_receipt':record['receipt']}
    assert client.post(route,json=body,headers={'origin':'https://elsewhere.invalid'}).status_code==403
    body['review_receipt']={**record['receipt'],'content_sha256':'0'*64}
    assert client.post(route,json=body).status_code==400
    assert client.post(route,content=b' '* (2*1024**2+1),headers={'content-type':'application/json'}).status_code==400
    assert not list(service.root.glob('ref-*.json'))


def test_reference_failure_retry_recovers_without_second_artifact(setup,monkeypatch):
    service,args,record=setup
    from src.review.literature_attachment_api import AttachmentCatalog
    catalog=AttachmentCatalog(service)
    body={'capture_text':args['capture'].decode(),'review_receipt':record['receipt']}
    remember=catalog.remember
    monkeypatch.setattr(catalog,'remember',lambda r: (_ for _ in ()).throw(OSError('simulated receipt failure')))
    with pytest.raises(OSError):catalog.attach(args['manifest_sha256'],args['review_event_id'],body)
    assert len(list(service.root.glob('*/complete.json')))==1
    monkeypatch.setattr(catalog,'remember',remember)
    result=catalog.attach(args['manifest_sha256'],args['review_event_id'],body)
    assert result['state']=='reused'
    assert len(catalog.list(args['manifest_sha256'],args['review_event_id']))==1


def test_reference_tampering_rejected(setup):
    service,args,record=setup
    from src.review.literature_attachment_api import AttachmentCatalog
    catalog=AttachmentCatalog(service)
    catalog.attach(args['manifest_sha256'],args['review_event_id'],{'capture_text':args['capture'].decode(),'review_receipt':record['receipt']})
    path=next(service.root.glob('ref-*.json'));ref=json.loads(path.read_bytes());ref['receipt_sha256']='0'*64;path.write_bytes(encode(ref))
    with pytest.raises(ValueError):catalog.list(args['manifest_sha256'],args['review_event_id'])
