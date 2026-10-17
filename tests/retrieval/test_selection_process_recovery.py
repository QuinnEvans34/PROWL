"""Actual owned subprocess signals on synthetic catalogs."""
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
import pytest
from test_resumable_selection import case, full
from test_topic_selection import mesh_path
from src.retrieval import resumable_selection as rs


@pytest.mark.parametrize('workers',[1,2])
@pytest.mark.parametrize('boundary',['evaluation','export','publication'])
@pytest.mark.parametrize('sig',[signal.SIGINT,signal.SIGTERM,signal.SIGKILL])
def test_process_signal_resume(case,tmp_path,boundary,sig,workers):
    args=dict(full(case),workers=workers)
    config=tmp_path/'worker.json';config.write_text(json.dumps(args,default=str))
    marker=tmp_path/'ready'
    with (tmp_path/'child.log').open('w') as log:
        proc=subprocess.Popen([sys.executable,str(Path(__file__).parent/'helpers/selection_signal_worker.py'),
                               str(config),str(marker),boundary],stdout=log,stderr=log)
        try:
            deadline=time.monotonic()+15
            while not marker.exists() and proc.poll() is None and time.monotonic()<deadline:
                time.sleep(0.02)
            assert marker.exists(),(tmp_path/'child.log').read_text()
            children=json.loads(marker.read_text())['children']
            os.kill(proc.pid,sig)
            code=proc.wait(timeout=10)
            assert code!=0
            if sig==signal.SIGKILL: assert code==-signal.SIGKILL
            def alive(pid):
                try: os.kill(pid,0); return True
                except ProcessLookupError: return False
            deadline=time.monotonic()+5
            while any(alive(pid) for pid in children) and time.monotonic()<deadline:
                time.sleep(0.05)
            assert not any(alive(pid) for pid in children), 'Orphan evaluation workers'
        finally:
            if proc.poll() is None:
                proc.kill();proc.wait(timeout=10)
    assert not (args['output']/'summary.json').exists()
    if boundary=='evaluation':
        with sqlite3.connect(args['output']/'selection.sqlite') as db:
            assert db.execute('SELECT count(*) FROM rows').fetchone()[0]==1
    # Normal SQLite hot-journal recovery and both OS locks are exercised by resume.
    recovered=rs.run(**args,resume=True)
    baseline=rs.run(**dict(args,output=tmp_path/'baseline'))
    assert recovered['counts']==baseline['counts']
    for name in ('records.jsonl','candidate-pmids.txt'):
        assert (args['output']/name).read_bytes()==(tmp_path/'baseline'/name).read_bytes()
