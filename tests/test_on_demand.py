import copy
import json
from pathlib import Path
import sys
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import nibabel as nib
import numpy as np
import pytest
from src.inference.on_demand import PredictionJobs, JobError, sha
from scripts.serve_on_demand import handler_for, LocalFixtureServer


@pytest.fixture
def config(tmp_path):
    worker=Path(__file__).parent/'helpers/on_demand_fixture_worker.py'
    ct=tmp_path/'ct.nii.gz'; mask=tmp_path/'pancreas.nii.gz'; checkpoint=tmp_path/'checkpoint.txt'
    image=nib.Nifti1Image(np.zeros((4,4,4),dtype=np.uint8),np.eye(4));image.header.set_xyzt_units('mm');nib.save(image,ct)
    labels=np.zeros((4,4,4),dtype=np.uint8);labels[1:3,1:3,1:3]=1
    image=nib.Nifti1Image(labels,np.eye(4));image.header.set_xyzt_units('mm');nib.save(image,mask)
    checkpoint.write_text('artificial non-model bytes')
    ref=lambda p:dict(path=str(p.resolve()),sha256=sha(p))
    return dict(schema='on-demand-worker-v1',device='cpu',python=sys.executable,worker=ref(worker),code=[ref(worker)],
                timeout_seconds=10,rss_limit_mib=512,checkpoint=ref(checkpoint),recipe_sha256='a'*64,
                cases=[dict(case_id=name,role='exposed_development',ct=ref(ct),pancreas=ref(mask)) for name in ('one','slow','wrong')])


def finish(jobs, job):
    jobs.jobs[job['job_id']]['thread'].join(15)
    assert not jobs.jobs[job['job_id']]['thread'].is_alive()
    return jobs.get(job['job_id'])


def test_unconfigured_never_starts(tmp_path):
    jobs=PredictionJobs(tmp_path)
    assert jobs.catalog()==dict(configured=False,cases=[])
    with pytest.raises(JobError,match='not configured'):jobs.submit('one')


def test_result_bound_to_request_and_private_files(tmp_path,config):
    jobs=PredictionJobs(tmp_path/'jobs',config)
    try:
        job=jobs.submit('one'); done=finish(jobs,job);assert done['status']=='ready'
        manifest=json.loads(jobs.artifact(job['job_id'],'manifest.json').read_bytes())
        assert manifest['request_identity']==done['request_identity']
        with pytest.raises(JobError):jobs.artifact(job['job_id'],'../../checkpoint.txt')
        assert 'path' not in json.dumps(jobs.catalog())
        jobs.artifact(job['job_id'],'prediction.nii.gz').write_bytes(b'changed')
        with pytest.raises(JobError,match='changed'):jobs.artifact(job['job_id'],'prediction.nii.gz')
        jobs.release(job['job_id']);assert not jobs.jobs
    finally:jobs.close()


def test_cancel_reaps_and_busy_refuses(tmp_path,config):
    jobs=PredictionJobs(tmp_path/'jobs',config)
    try:
        job=jobs.submit('slow')
        with pytest.raises(JobError,match='busy'):jobs.submit('one')
        jobs.cancel(job['job_id']);assert finish(jobs,job)['status']=='cancelled'
        with pytest.raises(JobError):jobs.artifact(job['job_id'],'manifest.json')
    finally:jobs.close()


@pytest.mark.parametrize('mutation',['input','checkpoint','identity','timeout'])
def test_failure_never_publishes(tmp_path,config,mutation):
    case='one'
    if mutation=='input':Path(config['cases'][0]['ct']['path']).write_bytes(b'changed')
    if mutation=='checkpoint':Path(config['checkpoint']['path']).write_bytes(b'changed')
    if mutation=='identity':case='wrong'
    if mutation=='timeout':case='slow';config['timeout_seconds']=1
    jobs=PredictionJobs(tmp_path/'jobs',config)
    try:
        job=jobs.submit(case);assert finish(jobs,job)['status']=='failed'
        with pytest.raises(JobError):jobs.artifact(job['job_id'],'manifest.json')
    finally:jobs.close()


def test_only_exposed_development_catalog(tmp_path,config):
    config['cases'][0]['role']='test'
    with pytest.raises(ValueError,match='development'):PredictionJobs(tmp_path,config)


def test_http_origin_paths_and_unconfigured(tmp_path):
    jobs=PredictionJobs(tmp_path);server=LocalFixtureServer(('127.0.0.1',0),handler_for(jobs))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}/scan-inference'
    try:
        assert json.load(urlopen(base+'/cases'))['configured'] is False
        for path,data,headers,expected in [('/jobs',b'{"case_id":"one"}',{'Content-Type':'application/json'},503),
                ('/jobs',b'{"case_id":"one"}',{'Content-Type':'application/json','Origin':'https://example.org'},403),
                ('/jobs',b'{"path":"/secret"}',{'Content-Type':'application/json'},400),('/../../secret',None,{},404)]:
            with pytest.raises(HTTPError) as error:urlopen(Request(base+path,data=data,headers=headers))
            assert error.value.code==expected
    finally:server.shutdown();server.server_close();jobs.close();thread.join()

def test_native_result_consumed_by_real_js_measurement_loader(tmp_path,config):
    import os,subprocess,shutil
    node=shutil.which('node')
    if not node:pytest.skip('Node runtime required for cross-language transport check')
    jobs=PredictionJobs(tmp_path/'jobs',config);server=LocalFixtureServer(('127.0.0.1',0),handler_for(jobs))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}/scan-inference'
    try:
        job=jobs.submit('one');assert finish(jobs,job)['status']=='ready'
        module=(Path(__file__).resolve().parents[1]/'ui/src/lib/savedPrediction.js').as_uri()
        script='''
const {loadSavedPrediction}=await import(process.env.PROWL_TEST_MODULE);
const expected=JSON.parse(process.env.PROWL_TEST_JOB);
const loaded=await loadSavedPrediction(process.env.PROWL_TEST_BASE+'/jobs/'+expected.job_id+'/files',undefined,expected);
try {if(loaded.measurement.status!=='ready'||loaded.measurement.pancreasMl!==.008||!loaded.measurement.assisted)throw Error('measurement mismatch');console.log('native identity and 8 mm3 predicted volume verified');}finally{loaded.release()}
'''
        env=dict(os.environ,PROWL_TEST_MODULE=module,PROWL_TEST_JOB=json.dumps(job),PROWL_TEST_BASE=base)
        done=subprocess.run([node,'--input-type=module','-e',script],env=env,capture_output=True,text=True,timeout=20)
        assert done.returncode==0,done.stderr
        assert '8 mm3' in done.stdout
    finally:server.shutdown();server.server_close();jobs.close();thread.join()
