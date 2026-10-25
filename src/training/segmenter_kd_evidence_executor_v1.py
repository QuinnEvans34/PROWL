"""Native KD executor integration; preserve the existing training/selection loop."""
from pathlib import Path
import numpy as np
from src.training.segmenter_pancreas_region_executor_v1 import execute as region_execute
from src.training.segmenter_kd_native_evaluation_v1 import evaluate, bind_sidecar


def journal_value(value):
    """Convert NumPy scalars exactly; never stringify unsupported payloads."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: journal_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [journal_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(journal_value(item) for item in value)
    return value


class JournalSession:
    def __init__(self, session):
        self.session = session

    def __getattr__(self, key):
        return getattr(self.session, key)

    def update(self, provider):
        return journal_value(self.session.update(provider))


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

    return region_execute(JournalSession(session), provider, output, checkpoint_hook=preserve,
                          evaluator=evaluator, **kwargs)
