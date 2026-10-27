"""Actual supervised process boundaries, invented CPU data/model only."""
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tests'))
from src.data.segmenter_teacher_cache_v1 import sha, TeacherTargetStore
from src.operations.kd_gpu_qualification_v1 import dispatch, write
from src.operations.mac_teacher_supervision_v2 import run as supervised
from test_kd_gpu_qualification_v1 import fixture


def worker(root, stage):
    import torch
    from test_distillation_integration_v1 import Provider
    from test_kd_evidence_executor_v1 import evaluate
    from src.data.manifest_records import canonical, digest
    from src.training import segmenter_full_session_v1 as full
    from src.training.segmenter_errata_kd_session_v1 import OnDemandStudent, ErrataKDSession
    from src.training.segmenter_distillation_v1 import DistillationConfig
    from src.training.kd_executor_qualification_v1 import exercise
    from scripts.diagnostics.mac_kd_synthetic import compare

    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
    torch.set_num_threads(1)
    full.build_model = lambda _: torch.nn.Conv3d(1, 3, 1)
    p = Provider(); p.control['validation'] = ['positive', 'empty']
    p.pin = digest(canonical(p.control))
    inputs = root/'synthetic-targets'
    targets = TeacherTargetStore(inputs, sha(inputs/'manifest.json'), control=p.control,
                                common_identity=json.loads((inputs/'common.json').read_text()))
    config = dict(max_steps=24000, lr_horizon_steps=24000, tensor_shape=[16]*3, seed=42,
                  learning_rate=1e-4, weight_decay=1e-5, warmup_steps=500,
                  lr_schedule='warmup_cosine', loss_id=full.DICE_FOCAL)
    def student():
        return OnDemandStudent(full.Session(config, p.control, device='cpu', initialization={'kind':'scratch'}))
    def kd(weight):
        return ErrataKDSession(student(), teacher_identity={'weights':{'sha256':'a'*64}},
                              loss_config=DistillationConfig(max_weight=weight), target_manifest_sha256=targets.pin)
    write(root/stage/'synthetic-process.json', dict(pid=os.getpid(), device='cpu', synthetic=True))
    exercise(root, stage, json.loads((root/'request.json').read_text()), inputs=p, targets=targets,
             student=student, kd=kd, tick=lambda:None, compare=compare, evaluate=evaluate,
             backup_admission=lambda size:None)


def test_four_stages_restore_in_fresh_supervised_processes(tmp_path):
    from test_distillation_integration_v1 import Provider, store
    from src.data.manifest_records import canonical, digest
    root, pin = fixture(tmp_path)
    p = Provider(); p.control['validation'] = ['positive', 'empty']; p.pin = digest(canonical(p.control))
    target_root = root/'synthetic-targets'; target_root.mkdir()
    targets = store(target_root, p); write(target_root/'common.json', targets.common)
    before = {str(f):sha(f) for f in target_root.iterdir()}
    pids = []
    def bounded(command, destination, **kwargs):
        kwargs.update(seconds=60, rss_bytes=2*1024**3)
        return supervised(command, destination, **kwargs)
    for stage in ('reference','zero','producer','cold'):
        receipt = dispatch(root, stage, pin, guard=nullcontext, preflight=lambda r:None,
                           supervise=bounded,
                           command=lambda s:[sys.executable, str(Path(__file__).resolve()), str(root), s],
                           env=dict(os.environ, CUDA_VISIBLE_DEVICES='-1', OMP_NUM_THREADS='1'))
        assert receipt['success'] and receipt['scientific_ready'] is False
        resources = json.loads((root/stage/'resources.json').read_text())
        assert resources['workers_reaped'] is True and resources['exit_code'] == 0
        pid = json.loads((root/stage/'synthetic-process.json').read_text())['pid']; pids.append(pid)
        with pytest.raises(ProcessLookupError): os.kill(pid, 0)
    assert len(set(pids)) == 4
    assert before == {str(f):sha(f) for f in target_root.iterdir()}
    # Independent step-3 backup was consumed by the new cold worker; exercise
    # compares the entire restored next-update state with producer step4.
    cold = json.loads((root/'cold/result.json').read_text())
    assert cold['engineering_updates'] == 1 and cold['scientific_updates'] == 0
    assert len(json.loads((root/'cold/receipt.json').read_text())['parents']) == 3


if __name__ == '__main__':
    worker(Path(sys.argv[1]), sys.argv[2])
