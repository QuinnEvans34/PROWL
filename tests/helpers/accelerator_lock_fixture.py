"""Synthetic CPU lock owner; never uses the real accelerator lock or an accelerator."""
from pathlib import Path
import sys
from src.operations import full_training_platform as platform

lock=Path(sys.argv[1]);mode=sys.argv[2]
# Isolate AC behavior from the machine; no compute follows either outcome.
def power():
    if mode=='no-ac':raise RuntimeError('synthetic AC unavailable')
platform.require_ac=power
try:
    with platform.training_guard(lock):
        print('admitted',flush=True)
        if mode=='hold':sys.stdin.readline()
except BlockingIOError:
    print('busy',flush=True);sys.exit(3)
except RuntimeError as error:
    print(str(error),flush=True);sys.exit(4)
