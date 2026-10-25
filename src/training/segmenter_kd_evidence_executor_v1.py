"""Native KD executor integration; preserve the existing training/selection loop."""
from pathlib import Path
from src.training.segmenter_pancreas_region_executor_v1 import execute as region_execute
from src.training.segmenter_kd_native_evaluation_v1 import evaluate, bind_sidecar


def execute(session, provider, output, *, checkpoint_hook, evaluator=evaluate, **kwargs):
    """Require evidence and its backup before declaring native evaluation complete.

    The supplied hook must durably back up each artifact or raise. A failure is
    journaled by the existing executor; there is no automatic retry or resume.
    This wrapper is not a launch/readiness gate or a replacement for GPU testing.
    """
    def preserve(path):
        path = Path(path)
        if path.name.startswith('native-') and path.suffix == '.json':
            sidecar = bind_sidecar(path)
            checkpoint_hook(path)
            checkpoint_hook(sidecar)
        else:
            checkpoint_hook(path)

    return region_execute(session, provider, output, checkpoint_hook=preserve,
                          evaluator=evaluator, **kwargs)
