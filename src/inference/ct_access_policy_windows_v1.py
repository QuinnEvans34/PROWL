"""CT-only file tripwire for a future qualified Windows worker, not an OS sandbox.

Install only after loading reviewed weights. Code roots must be explicit installed
runtime/source directories, never a data drive or the whole repository.
"""
import os
from pathlib import Path


class CtAccessPolicy:
    def __init__(self, ct, output, code_roots):
        self.ct = Path(ct).resolve()
        self.output = Path(output).resolve()
        self.code_roots = tuple(Path(p).resolve() for p in code_roots)
        if self.ct.is_relative_to(self.output) or any(self.ct.is_relative_to(p) for p in self.code_roots):
            raise ValueError('CT must remain outside writable output and code roots')
        self.ct_reads = 0

    def __call__(self, event, values):
        if event != 'open' or not isinstance(values[0], (str, bytes)):
            return
        raw = os.fsdecode(values[0])
        # os.devnull is an exact platform device, not a directory permission.
        if os.path.normcase(raw) == os.path.normcase(os.devnull):
            return
        path = Path(raw).resolve()
        mode = values[1] if len(values) > 1 else None
        flags = values[2] if len(values) > 2 else 0
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
        if path.is_relative_to(self.output):
            return
        if writing:
            raise PermissionError('CT-only worker cannot write outside its output')
        if path == self.ct:
            self.ct_reads += 1
            return
        if any(path.is_relative_to(root) for root in self.code_roots):
            return
        raise PermissionError('CT-only worker blocked an undeclared data read')
