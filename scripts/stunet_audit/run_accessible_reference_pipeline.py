"""One bounded continuation, preserving a CRC-blocked reference and the original budget."""
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
    with Path(path).open('rb') as f:
        while block:=f.read(1024**2):h.update(block)
    return h.hexdigest()

def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2)

def main():
    start=time.monotonic();out=ROOT/'reference-pipeline-02';out.mkdir(exist_ok=False)
    source_files=[*Path('src').rglob('*.py'),*Path('scripts/stunet_audit').glob('*.py'),Path('scripts/audit_stunet_overlap.py')]
    pins={str(p):digest(p) for p in source_files}
    spent=json.loads((ROOT/'extraction-supervision-01/resources.json').read_text())
    if spent['success'] or not spent['workers_reaped'] or spent['exit_code']!=1:raise ValueError('Original failure not closed')
    if 'bad CRC cca32844  (should be 08acde52)' not in Path('outputs/prowl/stunet-audit-20261106/s0864-independent-zip-test.log').read_text():raise ValueError('Independent CRC evidence absent')
    if spent['seconds']+120+2600>3600:raise ValueError('Original cumulative extraction budget exceeded')
    request=dict(source_pins=pins,original_extraction_seconds=spent['seconds'],diagnostic_charge_seconds=120,
                 continuation_max_seconds=2600,original_extraction_budget_seconds=3600,comparison_max_seconds=3600,
                 max_owned_rss_bytes=8*1024**3,reference_pool_size=1204,protected_prowl_test_reads=False,
                 source_crc_failures_admitted=0,automatic_stage_retry=False,scientific_training=False)
    save(out/'request.json',request);last=[0.]
    def tick():
        if time.monotonic()-last[0]<5:return
        last[0]=time.monotonic()
        if shutil.disk_usage('/Volumes/PROWL-Data').free<100*1024**3:raise RuntimeError('External storage gate')
        if 'AC Power' not in subprocess.check_output(['pmset','-g','batt'],text=True,timeout=5):raise RuntimeError('AC gate')
    def unchanged():
        if any(digest(name)!=pin for name,pin in pins.items()):raise RuntimeError('Producing source changed')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    try:
        tick();receipt=json.loads((DOWNLOAD/'download.json').read_text())
        if receipt['status']!='VERIFIED' or receipt['md5']!='f0fbb3f91d9d99f2169863545f577b30':raise ValueError('Original source not verified')
        inputs=[ROOT/'reference-extraction-01/progress.jsonl',ROOT/'extraction-supervision-01/resources.json',
                Path('outputs/prowl/stunet-audit-20261106/s0864-independent-zip-test.log')]
        known=dict(case_id='TotalSegV1:s0864',archive_member='Totalsegmentator_dataset/s0864/ct.nii.gz',
                   reason='ARCHIVE_MEMBER_CRC_FAILURE_UNUSABLE',expected_crc32_hex='08acde52',observed_crc32_hex='cca32844',
                   independently_confirmed=True,publisher_archive_md5_matches=True,used_for_comparison=False,
                   partial_preserved=str(ROOT/'reference-extraction-01/ct/s0864/ct.nii.gz'))
        extraction_request=dict(source_pins=pins,input_pins={str(p):digest(p) for p in inputs},
            archive=str(DOWNLOAD/'Totalsegmentator_dataset.zip'),archive_sha256=receipt['sha256'],
            previous_extraction=str(ROOT/'reference-extraction-01'),known_blocked_reference=known,max_worker_seconds=2600)
        path=out/'extraction-request.json';save(path,extraction_request)
        supervision=ROOT/'extraction-supervision-02';supervision.mkdir(exist_ok=False)
        extraction=ROOT/'reference-extraction-02'
        cmd=[sys.executable,'scripts/stunet_audit/extract_accessible_reference_ct.py','--request',str(path),
             '--request-sha256',digest(path),'--output',str(extraction)]
        if not run(cmd,supervision,seconds=2600,rss_bytes=8*1024**3,tick=tick,env=env):raise RuntimeError('Continuation failed; no retry')
        unchanged();tick()
        with zipfile.ZipFile(DOWNLOAD/'Totalsegmentator_dataset.zip') as z:
            info=z.getinfo('Totalsegmentator_dataset/meta.csv')
            if info.file_size>128*1024:raise ValueError('Metadata bound')
            raw=z.read(info)
        if hashlib.sha256(raw).hexdigest()!=digest('outputs/prowl/stunet-audit-20261106/totalseg-meta-provisional.csv'):raise ValueError('Metadata bytes changed')
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
        save(out/'verified-reference-splits.json',dict(archive_sha256=receipt['sha256'],metadata_sha256=hashlib.sha256(raw).hexdigest(),
             rows=[dict(reference_id='TotalSegV1:'+r['image_id'],publisher_split=r['split'],institute_code=r['institute']) for r in rows]))
        m=json.loads((extraction/'reference-manifest.json').read_text())
        if digest(ROOT/'query-manifest.json')!='95a2a0137f5427b7f437ddd413d3d67f5b086f1cbed088a3ba2c2fa1d64bc710':raise ValueError('Development scope changed')
        queries=json.loads((ROOT/'query-manifest.json').read_text())['queries']
        for q in queries:
            fp=ROOT/'query-fingerprints-01'/(hashlib.sha256(q['case_id'].encode()).hexdigest()+'.json')
            q.update(fingerprint_path=str(fp),fingerprint_sha256=digest(fp))
        reference_request=dict(source_pins=pins,references=m['references'],blocked_references=m['blocked_references'],
            queries=queries,archive_sha256=receipt['sha256'],scope='Accessible original v1 reference members versus exactly75 permitted development cases',
            max_seconds=3600,max_owned_rss_bytes=8*1024**3,clearance_issued=False)
        path=out/'reference-request.json';save(path,reference_request)
        supervision=ROOT/'reference-supervision-02';supervision.mkdir(exist_ok=False)
        cmd=[sys.executable,'scripts/stunet_audit/reference_accessible_worker.py','--request',str(path),
             '--request-sha256',digest(path),'--output',str(ROOT/'reference-comparison-02')]
        if not run(cmd,supervision,seconds=3600,rss_bytes=8*1024**3,tick=tick,env=env):raise RuntimeError('Reference comparison failed; no retry')
        unchanged()
        for q in queries:
            if digest(q['path'])!=q['sha256']:raise ValueError('Development source bytes changed')
        result=dict(status='COMPLETE_WITH_DECLARED_BLOCKERS',seconds=time.monotonic()-start,clearance_issued=False,
                    blocked_reference_count=len(m['blocked_references']),scientific_training=False)
    except Exception as error:
        result=dict(status='FAILED_PRESERVED',seconds=time.monotonic()-start,error=repr(error),automatic_retry=False)
    save(out/'result.json',result);print(json.dumps(result),flush=True)
    if result['status']=='FAILED_PRESERVED':raise SystemExit(1)

if __name__=='__main__':main()
