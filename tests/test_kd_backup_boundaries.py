"""CPU-only backup failure boundaries through the existing KD executor."""
import errno
import shutil
import pytest
from test_pancreas_region_executor import FakeSession, checkpoint, records
from test_kd_evidence_executor_v1 import evaluate
from src.training.segmenter_kd_evidence_executor_v1 import execute


@pytest.mark.parametrize('artifact', [
    'initial.pt', 'last.pt', 'step-000001.pt', 'best.pt',
    'native-000001.json', 'native-000001-components.json',
    'native-selected.json', 'native-selected-components.json',
    'native-terminal.json', 'native-terminal-components.json',
])
@pytest.mark.parametrize('failure_errno', [errno.ENOSPC, errno.EIO])
def test_backup_failure_stops_at_exact_boundary(tmp_path, artifact, failure_errno):
    run = tmp_path / 'run'
    backup = tmp_path / 'backup'
    backup.mkdir()
    calls = []
    session = FakeSession(2)
    def preserve(path):
        calls.append(path.name)
        if path.name == artifact:
            raise OSError(failure_errno, 'synthetic backup failure')
        shutil.copyfile(path, backup / path.name)

    with pytest.raises(OSError) as caught:
        execute(session, None, run, validate_every=1, checkpoint_every=1,
                evaluator=evaluate, checkpoint=checkpoint, checkpoint_hook=preserve)
    assert caught.value.errno == failure_errno
    assert calls[-1] == artifact
    assert calls.count(artifact) == 1  # No automatic retry.
    assert (run / artifact).exists()  # Preserve original evidence.
    assert not (backup / artifact).exists()
    events = records(run / 'history.jsonl')
    assert events[-1]['event'] == 'failed'
    assert events[-1]['error_type'] == 'OSError'
    assert not any(e['event'] in ('training_completed', 'completed') for e in events)
    failed_step = 0 if artifact == 'initial.pt' else 2 if 'terminal' in artifact else 1
    assert session.step == failed_step
    assert sum(e['event'] == 'update' for e in events) == failed_step
    assert not any(e['event'] == 'native_completed' and e['step'] == failed_step for e in events)
    for saved in backup.iterdir():
        assert saved.read_bytes() == (run / saved.name).read_bytes()
    before = (run / 'history.jsonl').read_bytes()
    with pytest.raises(FileExistsError):
        execute(FakeSession(2), None, run, evaluator=evaluate, checkpoint=checkpoint,
                checkpoint_hook=preserve)
    assert (run / 'history.jsonl').read_bytes() == before
