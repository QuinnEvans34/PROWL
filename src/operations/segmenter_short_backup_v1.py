"""D-327 independent segmenter checkpoint backup and new-destination recovery."""
import json
import os
from uuid import uuid4
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.operations.artifact_store import read_file,now
from src.training.segmenter_training_session_v1 import validate_payload

EXTRA={'primary-complete.json','primary-events.jsonl','catalog.json'}


def validate_backup(files,identity,primary_reference,validator=validate_payload):
    require(EXTRA<=set(files),'Missing backup provenance')
    require(digest(files['primary-complete.json'])==primary_reference['receipt_sha256'],'Wrong primary completion')
    receipt=json.loads(files['primary-complete.json']);catalog=json.loads(files['catalog.json'])
    require(receipt['state']=='complete' and receipt['artifact_id']==primary_reference['artifact_id'] and
        receipt['derivation_sha256']==primary_reference['derivation_sha256'] and receipt['metadata']['artifact_type'] in ('segmenter-training-checkpoint','segmenter-trained-native-case','segmenter-short-run-summary','segmenter-short-run-probes','segmenter-short-images'),'Wrong source artifact')
    require(digest(files['primary-events.jsonl'])==receipt['events_sha256'],'Changed primary attempt journal')
    payload={k:v for k,v in files.items() if k not in EXTRA}
    require({n:dict(bytes=len(v),sha256=digest(v)) for n,v in payload.items()}==receipt['members'],'Backup payload differs from complete primary')
    require(catalog['source_reference']==primary_reference and catalog['source_domain']!=catalog['destination_domain'] and
        catalog['approval']=='D-327' and catalog['omissions']==[] and catalog['state']=='verified_snapshot','Wrong backup catalog')
    result=validator(payload,identity)
    require(receipt['validation']==result,'Primary semantic receipt differs')
    return dict(**result,primary_receipt_sha256=primary_reference['receipt_sha256'])


def backup_checkpoint(primary,backup,reference,identity,*,source_domain,destination_domain,validator=validate_payload):
    require(source_domain!=destination_domain and primary.root.stat().st_dev!=backup.root.stat().st_dev,'Independent backup device required')
    payload,receipt=primary.resolve(reference['artifact_id'],receipt_sha256=reference['receipt_sha256'],
        expected_derivation=reference['derivation_sha256'],validate=lambda f:validator(f,identity))
    with primary.opened() as fd:
        child=os.open(digest(reference['artifact_id'].encode()),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            completion=read_file(child,'complete.json',1024**2);events=read_file(child,'events.jsonl',1024**2)
        finally:os.close(child)
    catalog=dict(schema_version='1.0.0',catalog_id=str(uuid4()),state='verified_snapshot',source_reference=reference,
        source_domain=source_domain,destination_domain=destination_domain,approval='D-327',operator='Codex for Quinton',
        created_at=now(),copy_tool='segmenter-short-backup-v1',retention='recovery-verification-keeper',omissions=[])
    files=dict(payload,**{'primary-complete.json':completion,'primary-events.jsonl':events,'catalog.json':canonical(catalog)})
    artifact_id='backup:'+reference['artifact_id'];derivation=digest(canonical(reference))
    metadata=dict(artifact_type='segmenter-backup',schema_version='1.0.0',component='segmenter-short-backup-v1',
        code_sha256=identity['source_sha256'],parents=[reference['receipt_sha256']],retention='recovery-verification-keeper',
        sensitivity='private-research',run_id=identity['run_id'],stage_id='backup')
    pin,status=backup.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,
        validate=lambda f:validate_backup(f,identity,reference,validator))
    return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,status=status)


def restore_backup(backup,restore,backup_reference,primary_reference,identity,validator=validate_payload):
    """No primary store/path parameter. Verify backup, publish new restore, reread that copy."""
    validate=lambda f:validate_backup(f,identity,primary_reference,validator)
    files,receipt=backup.resolve(backup_reference['artifact_id'],receipt_sha256=backup_reference['receipt_sha256'],
        expected_derivation=backup_reference['derivation_sha256'],validate=validate)
    artifact_id='restore:'+str(uuid4());metadata=dict(receipt['metadata'],artifact_type='segmenter-restore',stage_id='restore',
        parents=[backup_reference['receipt_sha256']])
    pin,status=restore.publish(artifact_id,derivation_sha256=backup_reference['receipt_sha256'],files=files,
        metadata=metadata,validate=validate)
    restored,_=restore.resolve(artifact_id,receipt_sha256=pin,validate=validate,expected_derivation=backup_reference['receipt_sha256'])
    return {k:v for k,v in restored.items() if k not in EXTRA},dict(artifact_id=artifact_id,receipt_sha256=pin,status=status)
