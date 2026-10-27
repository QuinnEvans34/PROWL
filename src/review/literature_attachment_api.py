"""Optional loopback routes and separate receipt references for review attachments."""
import fcntl
import stat
import json
import os
import re
import uuid

from fastapi import Request
from starlette.concurrency import run_in_threadpool
from src.operations.artifact_store import read_file
from src.review.store import ReviewError, digest, encode


class AttachmentCatalog:
    def __init__(self, attachments):
        self.attachments = attachments

    def remember(self, result):
        name = 'ref-'+result['artifact_id'].split(':')[1]+'.json'
        raw = encode({k: result[k] for k in ('artifact_id','receipt_sha256','manifest_sha256','review_event_id')})
        store = self.attachments.store
        with store.opened() as fd, store.writer(fd):
            if name in os.listdir(fd):
                if read_file(fd, name, 4096) != raw: raise ValueError('Attachment reference conflict')
                return
            store.space(fd, 4096)
            temporary = '.reference-'+uuid.uuid4().hex
            child = os.open(temporary, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600, dir_fd=fd)
            with os.fdopen(child,'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.link(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
            os.unlink(temporary, dir_fd=fd); os.fsync(fd)

    def list(self, manifest, event):
        # Discover references only; never infer a trusted receipt from the artifact itself.
        with self.attachments.store.opened() as fd:
            names = sorted(n for n in os.listdir(fd) if re.fullmatch(r'ref-[a-f0-9]{64}\.json',n))
            if len(names)>1000: raise ReviewError('Attachment catalog limit reached.',507)
            refs = [json.loads(read_file(fd,n,4096)) for n in names]
        selected = [r for r in refs if r['manifest_sha256']==manifest and r['review_event_id']==event]
        if len(selected)>20: raise ReviewError('Review attachment limit reached.',507)
        rows=[]
        for ref in selected:
            opened=self.attachments.reopen(ref['artifact_id'], ref['receipt_sha256'])
            binding=opened['binding']
            if binding['manifest_sha256']!=manifest or binding['review_event_id']!=event:
                raise ValueError('Attachment reference target differs')
            response=opened['capture']['response']
            rows.append({**ref,'question':opened['capture']['request']['question'],
                         'state':response['state'],'generation':response['generation'],
                         'capture_sha256':binding['capture_sha256']})
        return rows

    def attach(self, manifest, event, body):
        with self.attachments.store.opened() as fd:
            lock=os.open('.catalog-writer.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=fd)
            try:
                info=os.fstat(lock)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1: raise ValueError('Unsafe catalog lock')
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                return self._attach(manifest,event,body)
            finally: os.close(lock)

    def _attach(self, manifest, event, body):
        if set(body)!={'capture_text','review_receipt'} or not isinstance(body['capture_text'],str):
            raise ValueError('Invalid attachment request')
        raw=body['capture_text'].encode('utf8')
        # Verify the revision before discovery/publication. Never trust a client-supplied receipt alone.
        receipt_pin=digest(encode(body['review_receipt']))
        self.attachments.review(manifest,event,receipt_pin)
        prior=self.list(manifest,event)
        if len(prior)>=20 and not any(r['capture_sha256']==digest(raw) for r in prior):
            raise ReviewError('Review attachment limit reached.',507)
        with self.attachments.store.opened() as fd:
            if len([n for n in os.listdir(fd) if n.startswith('ref-')])>=1000 and not any(r['capture_sha256']==digest(raw) for r in prior):
                raise ReviewError('Attachment catalog limit reached.',507)
        result=self.attachments.attach(manifest_sha256=manifest, review_event_id=event,
            review_receipt_sha256=receipt_pin, capture=raw, capture_sha256=digest(raw))
        self.remember(result)
        return result


def register_attachment_routes(app, attachments):
    catalog=AttachmentCatalog(attachments)

    def identity(manifest,event):
        if not re.fullmatch('[a-f0-9]{64}',manifest) or not re.fullmatch(r'review:[a-f0-9-]{36}',event):
            raise ReviewError('Invalid review identity.',400)

    @app.get('/review-records/literature/{manifest}/{event}')
    def listing(manifest:str,event:str):
        identity(manifest,event)
        return {'attachments':catalog.list(manifest,event)}

    @app.post('/review-records/literature/{manifest}/{event}')
    async def attach(manifest:str,event:str,request:Request):
        identity(manifest,event)
        if request.headers.get('content-type')!='application/json' or request.headers.get('transfer-encoding'):
            raise ReviewError('JSON request required.',400)
        size=int(request.headers.get('content-length','0'))
        if not 0<size<=2*1024**2: raise ReviewError('Attachment request exceeds limit.',400)
        raw=await request.body()
        if len(raw)!=size: raise ReviewError('Invalid request size.',400)
        return await run_in_threadpool(catalog.attach,manifest,event,json.loads(raw))

    @app.get('/review-records/literature-capture/{artifact}/{receipt}')
    def reopen(artifact:str,receipt:str):
        return attachments.reopen('review-literature:'+artifact,receipt)
