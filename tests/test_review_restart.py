"""Complete transport/restart check using the existing invented native-package worker."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import uuid
from urllib.request import Request, urlopen

import pytest
from test_on_demand import config, finish
from src.inference.on_demand import PredictionJobs


def test_native_package_review_survives_server_restart_and_session_cleanup(tmp_path, config):
    # The production writer has a fixed loopback port; never replace another process.
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',8018)) == 0: pytest.skip('Existing review service owns port8018')
    node=shutil.which('node')
    if not node:pytest.skip('Node required for actual native viewer loader')
    repo=Path(__file__).resolve().parents[1]
    jobs=PredictionJobs(tmp_path/'jobs',config)
    child=None
    def start(source=None):
        command=[sys.executable,str(repo/'scripts/serve_reviews.py'),'--root',str(tmp_path/'reviews')]
        if source:command+=['--saved-package',str(source)]
        process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        for _ in range(100):
            if process.poll() is not None:raise AssertionError(process.stderr.read().decode())
            try:
                with urlopen('http://127.0.0.1:8018/review-records/packages',timeout=.2):return process
            except OSError:time.sleep(.05)
        process.terminate();process.wait(5);raise AssertionError('Writer did not start')
    def get(path):
        with urlopen('http://127.0.0.1:8018/review-records/'+path,timeout=10) as response:return json.load(response)
    try:
        job=jobs.submit('one');assert finish(jobs,job)['status']=='ready'
        package=jobs.artifact(job['job_id'],'manifest.json').parent
        child=start(package)
        target=get('targets/saved');identity=target['manifest_sha256']
        body=dict(request_id=str(uuid.uuid4()),manifest_sha256=identity,expected_latest_id=None,
                  reviewer=dict(reviewer_id='Invented restart operator',role='research_operator'),
                  action='accept',reason_codes=['contour_acceptable'],note='Synthetic test, not human acceptance')
        request=Request('http://127.0.0.1:8018/review-records/targets/saved',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urlopen(request,timeout=15) as response:receipt=json.load(response)
        child.terminate();assert child.wait(10) in (0,-15);child.stderr.close();child=None
        jobs.release(job['job_id']);assert not package.exists()
        child=start()
        history=get('targets/archive/'+identity)['history']
        assert history==[receipt] and get('packages')['packages'][0]['case_id']=='one'
        script='''
const {loadSavedPrediction}=await import(process.env.PROWL_TEST_MODULE);
const loaded=await loadSavedPrediction(process.env.PROWL_TEST_BASE);
try {if(loaded.measurement.status!=='ready'||loaded.measurement.pancreasMl!==.008||!loaded.measurement.assisted)throw Error('retained native measurement mismatch');console.log('retained CT/mask/provenance and 8 mm3 verified after restart');}finally{loaded.release()}
'''
        env=dict(os.environ,PROWL_TEST_MODULE=(repo/'ui/src/lib/savedPrediction.js').as_uri(),PROWL_TEST_BASE=f'http://127.0.0.1:8018/review-records/packages/{identity}/files')
        result=subprocess.run([node,'--input-type=module','-e',script],env=env,capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr
        assert '8 mm3 verified after restart' in result.stdout
    finally:
        if child:
            child.terminate();child.wait(10);child.stderr.close()
        jobs.close()
