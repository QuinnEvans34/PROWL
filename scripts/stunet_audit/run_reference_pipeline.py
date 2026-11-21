"""One authorized CPU audit continuation; waits for verified v1 bytes, never retries stages."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile
from src.operations.mac_pilot_supervision_v1 import run

ROOT=Path('/Volumes/PROWL-Data/PROWL/artifacts/stunet-audit-20261106')
DOWNLOAD=Path('/Volumes/PROWL-Data/PROWL/sources/totalsegmentator-v1-audit-20261106-ranges-04')

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024**2):h.update(block)
    return h.hexdigest()

def save(path,payload):
    with path.open('x') as f:json.dump(payload,f,indent=2)

def main():
    start=time.monotonic();destination=ROOT/'reference-pipeline-01';destination.mkdir(exist_ok=False)
    sources=[*Path('src').rglob('*.py'),*Path('scripts/stunet_audit').glob('*.py'),Path('scripts/audit_stunet_overlap.py')]
    pins={str(p):digest(p) for p in sources}
    save(destination/'request.json',dict(source_pins=pins,download_receipt=str(DOWNLOAD/'download.json'),
        max_download_wait_seconds=4000,max_stage_seconds=3600,max_owned_rss_bytes=8*1024**3,
        max_new_external_bytes=128*1024**3,external_free_floor=100*1024**3,
        stages=['verify_archive_extract_CT_only','reference_fingerprint_and_compare'],automatic_stage_retries=0,
        scientific_training=False,protected_prowl_test_reads=False))
    def tick():
        if shutil.disk_usage('/Volumes/PROWL-Data').free<100*1024**3:raise RuntimeError('External free-space gate')
        if 'AC Power' not in subprocess.check_output(['pmset','-g','batt'],text=True,timeout=5):raise RuntimeError('AC gate')
    def unchanged():
        if any(digest(name)!=pin for name,pin in pins.items()):raise RuntimeError('Producing source changed')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    try:
        while not (DOWNLOAD/'download.json').exists():
            tick()
            if time.monotonic()-start>4000:raise RuntimeError('Archive wait bound')
            time.sleep(5)
        receipt=json.loads((DOWNLOAD/'download.json').read_text())
        if receipt.get('status')!='VERIFIED' or receipt.get('md5')!='f0fbb3f91d9d99f2169863545f577b30':raise RuntimeError('Archive not verified; no CPU stage dispatched')
        unchanged();tick()
        extraction=ROOT/'reference-extraction-01';supervision=ROOT/'extraction-supervision-01';supervision.mkdir(exist_ok=False)
        save(destination/'extraction-binding.json',dict(archive_sha256=receipt['sha256'],source_pins=pins))
        command=[sys.executable,'scripts/stunet_audit/extract_reference_ct.py','--archive',str(DOWNLOAD/'Totalsegmentator_dataset.zip'),
                 '--download-receipt',str(DOWNLOAD/'download.json'),'--output',str(extraction)]
        if not run(command,supervision,seconds=3600,rss_bytes=8*1024**3,tick=tick,env=env):raise RuntimeError('Extraction failed; preserved, no retry')
        unchanged();tick()
        with zipfile.ZipFile(DOWNLOAD/'Totalsegmentator_dataset.zip') as archive:
            info=archive.getinfo('Totalsegmentator_dataset/meta.csv')
            if info.file_size>128*1024:raise ValueError('Reference metadata size')
            raw=archive.read(info)
        provisional=Path('outputs/prowl/stunet-audit-20261106/totalseg-meta-provisional.csv')
        if hashlib.sha256(raw).hexdigest()!=digest(provisional):raise RuntimeError('Provisional metadata differs from verified archive')
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
        minimal=[dict(reference_id='TotalSegV1:'+r['image_id'],publisher_split=r['split'],institute_code=r['institute']) for r in rows]
        save(destination/'verified-reference-splits.json',dict(archive_sha256=receipt['sha256'],metadata_sha256=hashlib.sha256(raw).hexdigest(),rows=minimal))
        references=json.loads((extraction/'reference-manifest.json').read_text())['references']
        queries=json.loads((ROOT/'query-manifest.json').read_text())['queries']
        for q in queries:
            fp=ROOT/'query-fingerprints-01'/(hashlib.sha256(q['case_id'].encode()).hexdigest()+'.json')
            q.update(fingerprint_path=str(fp),fingerprint_sha256=digest(fp))
        request=dict(references=references,queries=queries,source_pins=pins,archive_sha256=receipt['sha256'],
                     scope='Original v1 pool versus exactly 75 permitted development CTs; no labels, GPU, training or protected PROWL test images',
                     native_voxel_allocation_cap=128000000,large_reference_mode='bounded proxy overview, no full native voxel hash',
                     native_header_cap=1000000000,max_seconds=3600,max_owned_rss_bytes=8*1024**3)
        request_path=destination/'reference-request.json';save(request_path,request)
        supervision=ROOT/'reference-supervision-01';supervision.mkdir(exist_ok=False)
        command=[sys.executable,'scripts/stunet_audit/reference_worker.py','--request',str(request_path),
                 '--request-sha256',digest(request_path),'--output',str(ROOT/'reference-comparison-01')]
        if not run(command,supervision,seconds=3600,rss_bytes=8*1024**3,tick=tick,env=env):raise RuntimeError('Reference comparison failed; preserved, no retry')
        unchanged()
        for q in queries:
            if digest(q['path'])!=q['sha256']:raise RuntimeError('Development source bytes changed')
        result=dict(status='COMPLETE',seconds=time.monotonic()-start,scientific_training=False,clearance_issued=False)
    except Exception as error:
        result=dict(status='FAILED_PRESERVED',error=repr(error),seconds=time.monotonic()-start,automatic_retry=False)
    save(destination/'result.json',result);print(json.dumps(result),flush=True)
    if result['status']!='COMPLETE':raise SystemExit(1)

if __name__=='__main__':main()
