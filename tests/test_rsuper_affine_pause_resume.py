from pathlib import Path
from scripts.diagnostics import resume_rsuper_affine_after_pause_v1 as resume
from scripts.diagnostics import build_rsuper_affine_checked_v1 as qualified


def test_qualified_worker_and_existing_pause_gates():
    assert resume.frozen is qualified
    text=Path(resume.__file__).read_text()
    for required in ["request.get('preprocessing_extension') != POLICY",'Recorded pause identity differs',
                     'remaining_seconds(request, resources, owned_worker_kill=killed)',
                     'completed_members(previous, request)', 'with training_guard(',
                     'require_ac(); storage_preflight()', 'sha(Path(path)) != pin',
                     'mac_teacher_supervision_v2 import run', 'output.mkdir(exist_ok=False)',
                     "existing + request['limits']['output_bytes'] > 32*1024**3"]:
        assert required in text
