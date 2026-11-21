"""Inventory a verified original archive and extract only regular CT members."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import stat
import time
import zipfile

def validate_members(infos, *, expected_ct=1204):
    if len(infos)>150000 or len({i.filename for i in infos})!=len(infos):raise ValueError('Archive inventory bound/duplicate names')
    ct=[];inventory=[]
    for i in infos:
        name=PurePosixPath(i.filename)
        if name.is_absolute() or '..' in name.parts or '\\' in i.filename:raise ValueError('Unsafe archive path')
        if stat.S_ISLNK(i.external_attr>>16):raise ValueError('Archive symlink')
        if name.name=='ct.nii.gz' and not any(x.startswith('.') for x in name.parts):
            if i.file_size>256*1024**2:raise ValueError('Individual CT bound')
            ct.append(i)
        inventory.append(dict(name=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size,crc32=i.CRC))
    if len(ct)!=expected_ct or sum(i.file_size for i in ct)>96*1024**3:raise ValueError('Original reference count/size gate')
    return ct,inventory

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--download-receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();receipt=json.loads(a.download_receipt.read_text())
    if receipt.get('status')!='VERIFIED' or receipt.get('md5')!='f0fbb3f91d9d99f2169863545f577b30':raise ValueError('Unverified original archive')
    if a.archive.stat().st_size!=28404091806:raise ValueError('Archive size differs')
    start=time.monotonic();a.output.mkdir(exist_ok=False);ct=[];inventory=[]
    # Recheck source bytes, not just a trusted JSON assertion.
    h=hashlib.md5();sha=hashlib.sha256()
    with a.archive.open('rb') as f:
        while block:=f.read(8*1024**2):h.update(block);sha.update(block)
    if h.hexdigest()!=receipt['md5'] or sha.hexdigest()!=receipt['sha256']:raise ValueError('Archive changed')
    with zipfile.ZipFile(a.archive) as archive:
        infos=archive.infolist()
        ct,inventory=validate_members(infos)
        (a.output/'inventory.json').write_text(json.dumps(inventory))
        rows=[]
        for i in ct:
            if time.monotonic()-start>3500 or shutil.disk_usage(a.output).free<100*1024**3:raise RuntimeError('Time/storage gate')
            case=PurePosixPath(i.filename).parent.name
            if not case.startswith('s') or not case[1:].isdigit():raise ValueError('Unexpected reference pseudonym')
            out=a.output/'ct'/case/'ct.nii.gz';out.parent.mkdir(parents=True,exist_ok=False)
            digest=hashlib.sha256();total=0
            with archive.open(i) as src,out.open('xb') as dst:
                while block:=src.read(1024**2):
                    total+=len(block)
                    if total>i.file_size:raise ValueError('Member size bound')
                    dst.write(block);digest.update(block)
            if total!=i.file_size:raise ValueError('Member length differs')
            rows.append(dict(case_id='TotalSegV1:'+case,role='pretraining_reference',path=str(out),sha256=digest.hexdigest(),archive_member=i.filename))
            with (a.output/'progress.jsonl').open('a') as f:f.write(json.dumps(dict(completed=len(rows),case_id=case,seconds=time.monotonic()-start))+'\n')
        (a.output/'reference-manifest.json').write_text(json.dumps(dict(references=rows,queries=[]),indent=2))
    summary=dict(ct_members=len(rows),extracted_bytes=sum(i.file_size for i in ct),archive_sha256=sha.hexdigest(),
                 seconds=time.monotonic()-start,labels_extracted=0,protected_prowl_images_read=0)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))

if __name__=='__main__':main()
