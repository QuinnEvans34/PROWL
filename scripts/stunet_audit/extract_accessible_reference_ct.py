"""Continue an audit over accessible members; CRC failures remain blocked, never repaired."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import time
import zipfile
import zlib
from scripts.stunet_audit.extract_reference_ct import validate_members

def file_evidence(path):
    sha=hashlib.sha256();crc=0;size=0
    with Path(path).open('rb') as f:
        while block:=f.read(4*1024**2):
            sha.update(block);crc=zlib.crc32(block,crc);size+=len(block)
    return sha.hexdigest(),crc,size

def copy_member(archive,info,partial):
    """Return a digest only after ZIP CRC and exact-length verification."""
    digest=hashlib.sha256();size=0
    with archive.open(info) as src,Path(partial).open('xb') as dst:
        while block:=src.read(1024**2):
            size+=len(block)
            if size>info.file_size:raise ValueError('Member allocation bound')
            dst.write(block);digest.update(block)
    if size!=info.file_size:raise ValueError('Incomplete member')
    return digest.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True)
    p.add_argument('--request-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raw=a.request.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.request_sha256:raise ValueError('Request identity')
    req=json.loads(raw)
    for name,pin in req['source_pins'].items():
        if file_evidence(name)[0]!=pin:raise ValueError('Source changed')
    for name,pin in req['input_pins'].items():
        if file_evidence(name)[0]!=pin:raise ValueError('Input evidence changed')
    a.output.mkdir(exist_ok=False);start=time.monotonic()
    archive_path=Path(req['archive']);md5=hashlib.md5();sha=hashlib.sha256()
    with archive_path.open('rb') as f:
        while block:=f.read(8*1024**2):md5.update(block);sha.update(block)
    if md5.hexdigest()!='f0fbb3f91d9d99f2169863545f577b30' or sha.hexdigest()!=req['archive_sha256']:raise ValueError('Original archive changed')
    previous=Path(req['previous_extraction'])
    progress=[json.loads(line) for line in (previous/'progress.jsonl').read_text().splitlines()]
    if [r['completed'] for r in progress]!=list(range(1,len(progress)+1)):raise ValueError('Prefix accounting')
    prefix=[r['case_id'] for r in progress];known=req['known_blocked_reference']
    rows=[];blocked=[known];reused=0
    with zipfile.ZipFile(archive_path) as archive:
        ct,inventory=validate_members(archive.infolist())
        if prefix!=[PurePosixPath(i.filename).parent.name for i in ct[:len(prefix)]]:raise ValueError('Original success prefix differs')
        (a.output/'inventory.json').write_text(json.dumps(inventory))
        for info in ct:
            if time.monotonic()-start>req['max_worker_seconds']-30 or shutil.disk_usage(a.output).free<100*1024**3:raise RuntimeError('Original remaining time/storage bound')
            case=PurePosixPath(info.filename).parent.name
            if info.filename==known['archive_member']:
                if info.CRC!=int(known['expected_crc32_hex'],16):raise ValueError('Known bad member changed')
                continue
            if case in prefix:
                path=previous/'ct'/case/'ct.nii.gz'
                digest,crc,size=file_evidence(path)
                if size!=info.file_size or crc!=info.CRC:raise ValueError('Previously valid prefix bytes changed')
                reused+=1
            else:
                directory=a.output/'ct'/case;directory.mkdir(parents=True,exist_ok=False)
                partial=directory/'ct.nii.gz.partial'
                try:
                    digest=copy_member(archive,info,partial)
                except zipfile.BadZipFile as error:
                    if not str(error).startswith('Bad CRC-32 for file'):raise
                    failure=dict(case_id='TotalSegV1:'+case,archive_member=info.filename,
                                 reason='ARCHIVE_MEMBER_CRC_FAILURE_UNUSABLE',error=str(error),
                                 expected_crc32_hex=f'{info.CRC:08x}',partial_path=str(partial),used_for_comparison=False)
                    blocked.append(failure)
                    with (a.output/'blocked-events.jsonl').open('a') as f:f.write(json.dumps(failure)+'\n')
                    continue
                path=directory/'ct.nii.gz';partial.rename(path)
            rows.append(dict(case_id='TotalSegV1:'+case,role='pretraining_reference',path=str(path),sha256=digest,archive_member=info.filename))
            with (a.output/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(verified=len(rows),blocked=len(blocked),case_id=case,reused=reused,seconds=time.monotonic()-start))+'\n')
    if len(rows)+len(blocked)!=1204:raise ValueError('Full pool accounting differs')
    (a.output/'reference-manifest.json').write_text(json.dumps(dict(references=rows,queries=[],blocked_references=blocked),indent=2))
    summary=dict(status='ACCESSIBLE_MEMBERS_VERIFIED_WITH_DECLARED_BLOCKERS',reference_pool=1204,
                 verified_ct_members=len(rows),blocked_references=blocked,reused_ct_members=reused,
                 newly_extracted_ct_members=len(rows)-reused,seconds=time.monotonic()-start,
                 labels_extracted=0,failed_members_used=0)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))

if __name__=='__main__':main()
