"""Actual executor/checkpoint stack with an invented CPU network and inputs."""
import shutil
import json
import numpy as np
import pytest
import torch
from test_distillation_integration_v1 import Provider, store, same, isolated_cpu
from test_errata_kd_session_v1 import session
from test_kd_evidence_executor_v1 import evaluate
from src.training.segmenter_distillation_session_v1 import BoundDistillationSession
from src.training.segmenter_errata_kd_session_v1 import ErrataKDSession
from src.training.segmenter_kd_evidence_executor_v1 import execute, journal_value
from src.data.manifest_records import canonical


def test_executor_checkpoint_backup_restores_identical_next_update(tmp_path):
    target_root = tmp_path/'targets'; target_root.mkdir()
    provider = Provider(); targets = store(target_root, provider)
    original = session(provider, targets.pin, .1)
    # Keep the fixture's frozen eight-update horizon; real checkpoint implementation.
    backup = tmp_path/'backup'; backup.mkdir()
    def native(s, p, name, progress):
        # Invented validation member must be positive for executor selection.
        row = evaluate(s, p, 'positive', progress)
        row['case_id'] = row['component_evidence']['case_id'] = name
        return row
    result = execute(BoundDistillationSession(original, targets), provider, tmp_path/'run',
        validate_every=4, checkpoint_every=4, evaluator=native,
        checkpoint_hook=lambda path: shutil.copyfile(path, backup/path.name))
    assert result['completed_updates'] == 8
    saved = torch.load(backup/'step-000004.pt', weights_only=True, map_location='cpu')
    restored = ErrataKDSession.restore(saved['session'], original.identity)
    assert restored.step == 4 and saved['history_bytes'] > 0
    for _ in range(4):
        row = restored.update(Provider(), targets)
        assert row['teacher_accessed'] and row['kd_weight'] > 0
    assert same(original.state(), restored.state())
    rows = [json.loads(line) for line in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert sum(r['event'] == 'update' for r in rows) == 8
    assert rows[-1]['event'] == 'completed'


def test_journal_conversion_preserves_values_and_rejects_unsupported_data():
    value = np.float32(.5/65535)
    assert json.loads(canonical(journal_value({'x':value})))['x'] == float(value)
    for invalid in (np.array([1]), object(), float('nan')):
        with pytest.raises((TypeError, ValueError)):
            canonical(journal_value({'x':invalid}))
