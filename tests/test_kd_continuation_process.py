"""A real CPU worker exits; a second restores and completes the same synthetic run."""
import json
import os
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))


def worker(root,stage):
    import torch
    from src.training import segmenter_full_session_v1 as full
    from test_distillation_integration_v1 import Provider,store,same
    from test_errata_kd_session_v1 import session
    from test_kd_continuation_executor_v1 import native,backup_to
    from src.training.segmenter_distillation_session_v1 import BoundDistillationSession
    from src.training.segmenter_errata_kd_session_v1 import ErrataKDSession
    from src.training.segmenter_kd_continuation_executor_v1 import execute
    from src.operations.kd_continuation_v1 import inspect_checkpoint
    from src.data.segmenter_teacher_cache_v1 import TeacherTargetStore,sha
    assert os.environ['CUDA_VISIBLE_DEVICES']=='-1'
    torch.set_num_threads(1);full.build_model=lambda _:torch.nn.Conv3d(1,3,1)
    p=Provider();target=root/'targets'
    if stage=='first':
        target.mkdir();targets=store(target,p);(target/'common.json').write_text(json.dumps(targets.common))
        s=session(p,targets.pin,.1)
        execute(BoundDistillationSession(s,targets),p,root/'reference',checkpoint_hook=backup_to(root/'reference-backup'),
                validate_every=4,checkpoint_every=2,evaluator=native)
        torch.save(s.state(),root/'expected.pt')
        s=session(p,targets.pin,.1)
        result=execute(BoundDistillationSession(s,targets),p,root/'first-run',checkpoint_hook=backup_to(root/'first-backup'),
                validate_every=4,checkpoint_every=2,evaluator=native,pause_requested=lambda:s.step==5)
        assert result['status']=='paused'
    else:
        targets=TeacherTargetStore(target,sha(target/'manifest.json'),control=p.control,
            common_identity=json.loads((target/'common.json').read_text()))
        context=inspect_checkpoint(root/'first-run',root/'first-backup','pause.pt',validate_every=4)
        s=ErrataKDSession.restore(torch.load(context['checkpoint'],weights_only=True,map_location='cpu')['session'],context['identity'])
        result=execute(BoundDistillationSession(s,targets),p,root/'resumed-run',checkpoint_hook=backup_to(root/'resumed-backup'),
                validate_every=4,checkpoint_every=2,evaluator=native,continuation=context)
        assert result['completed'] and result['selected_step']==4
        assert same(s.state(),torch.load(root/'expected.pt',weights_only=True,map_location='cpu'))
    (root/(stage+'-pid.json')).write_text(json.dumps(dict(pid=os.getpid(),success=True)))


def test_fresh_worker_continues_exact_state(tmp_path):
    from src.operations.mac_teacher_supervision_v2 import run
    pids=[]
    for stage in ('first','cold'):
        dest=tmp_path/stage;dest.mkdir()
        assert run([sys.executable,str(Path(__file__).resolve()),str(tmp_path),stage],dest,
                   seconds=60,rss_bytes=2*1024**3,env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1'))
        resources=json.loads((dest/'resources.json').read_text())
        assert resources['workers_reaped'] and resources['exit_code']==0
        pid=json.loads((tmp_path/(stage+'-pid.json')).read_text())['pid'];pids.append(pid)
        with pytest.raises(ProcessLookupError):os.kill(pid,0)
    assert pids[0]!=pids[1]

if __name__=='__main__':worker(Path(sys.argv[1]),sys.argv[2])
