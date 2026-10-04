from copy import deepcopy
import json
import pytest
from src.operations.segmenter_training_backup_v1 import validate_backup
from src.data.manifest_records import canonical,digest

@pytest.fixture
def fixture():
 payload={'state.pt':b'invented_bytes_not_model'};journal=b'invented_journal';result={'task':'invented_validation'}
 receipt=dict(state='complete',artifact_id='invented-primary',derivation_sha256='a'*64,metadata=dict(artifact_type='segmenter-training-checkpoint'),events_sha256=digest(journal),members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in payload.items()},validation=result);raw=canonical(receipt);ref=dict(artifact_id='invented-primary',derivation_sha256='a'*64,receipt_sha256=digest(raw));cat=dict(source_reference=ref,source_domain='invented-primary-domain',destination_domain='invented-backup-domain',approval='D-326',omissions=[],state='verified_snapshot')
 return payload|{'primary-complete.json':raw,'primary-events.jsonl':journal,'catalog.json':canonical(cat)},ref,lambda f,i:result

def test_complete_backup_provenance_valid(fixture):
 f,r,v=fixture;assert validate_backup(f,{},r,v)['primary_receipt_sha256']==r['receipt_sha256']
@pytest.mark.parametrize('fault',['missing','approval','same_domain','omission','payload','events','completion','artifact_type','semantic'])
def test_backup_provenance_refuses_forgery(fixture,fault):
 f,r,v=deepcopy(fixture);cat=json.loads(f['catalog.json']);receipt=json.loads(f['primary-complete.json'])
 if fault=='missing':f.pop('catalog.json')
 if fault=='approval':cat['approval']='D-322'
 if fault=='same_domain':cat['destination_domain']=cat['source_domain']
 if fault=='omission':cat['omissions']=['state.pt']
 if fault=='payload':f['state.pt']+=b'x'
 if fault=='events':f['primary-events.jsonl']+=b'x'
 if fault=='completion':r['receipt_sha256']='0'*64
 if fault=='artifact_type':
  receipt['metadata']['artifact_type']='segmenter-checkpoint';f['primary-complete.json']=canonical(receipt);r['receipt_sha256']=digest(f['primary-complete.json']);cat['source_reference']=r
 if fault=='semantic':v=lambda f,i:{'task':'wrong'}
 if fault!='missing':f['catalog.json']=canonical(cat)
 with pytest.raises(ValueError):validate_backup(f,{},r,v)
