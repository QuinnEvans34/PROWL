"""Exercise real CPU pause/cold recovery through the replacement supervisor."""
import json
import os
from pathlib import Path
import sys
from src.operations.mac_teacher_supervision_v3 import run


def test_executor_pause_and_cold_under_v3(tmp_path):
    helper=Path(__file__).with_name('test_kd_continuation_process.py')
    for stage in ('first','cold'):
        dest=tmp_path/stage;dest.mkdir()
        assert run([sys.executable,str(helper),str(tmp_path),stage],dest,
                   seconds=60,rss_bytes=2*1024**3,
                   env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1'))
        resources=json.loads((dest/'resources.json').read_text())
        assert resources['workers_reaped'] and resources['exit_code']==0
        assert resources['surviving_workers']==[]
