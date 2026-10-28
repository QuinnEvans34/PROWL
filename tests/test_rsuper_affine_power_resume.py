import ast
from pathlib import Path
from scripts.diagnostics import resume_rsuper_affine_after_power_loss_v1 as resume
from scripts.diagnostics import build_rsuper_affine_checked_v1 as qualified

def test_uses_qualified_affine_worker():
    assert resume.frozen is qualified

def test_additive_runner_preserves_old_admission_and_supervision():
    text=Path(resume.__file__).read_text()
    for required in ['remaining_after_power_stop(previous, args.stop_review)',
                     'completed_members(previous, request)', 'with training_guard(',
                     'require_ac(); storage_preflight()', 'sha(Path(path)) != pin',
                     'mac_teacher_supervision_v2 import run', "output.mkdir(exist_ok=False)",
                     'existing + request[\'limits\'][\'output_bytes\'] > 32*1024**3']:
        assert required in text
    ast.parse(text)
