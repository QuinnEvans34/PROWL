"""Run S sizing-only tool, version 1 (Plan 07 S2; PROPOSAL, not a signed or executed run).

Scope: the downloader subset and the sizing-only parser mode required by run record S in
``docs/capstone/retrieval/planning/ACQUISITION-PLAN.md`` (SHA-256 ``a2be620c...``). Nothing here
builds a cross-file event log, a final state, a snapshot, a corpus, an index or embeddings.

Every external effect sits behind an injectable interface: transport, clock, volume probe, memory
probe, parser launcher and, from ``sizing_v1.1``, the filesystem hook ``fsio.SizingFs``. Every
read and write in the run's scratch, receipts and fallback areas goes through that hook. The test
suite therefore runs on invented inputs with the network denied.

This package has **no live volume or writer binding**. That belongs to the Codex-owned S1 storage
adapter (S1-S2-BINDING-V1), which supplies the guarded hook. The CLI therefore refuses live
execution.

Stop reasons are the ``stopped_<reason>`` final statuses written to the journal.
"""

GIB = 1024 ** 3
MIB = 1024 ** 2
KIB = 1024

TOOL_NAME = 'prowl-run-s-sizing'
TOOL_VERSION = 'sizing_v1.3'
SIZING_ONLY_MARKER = 'sizing_only'


class SizingStop(Exception):
    """Ends the run with final status ``stopped_<reason>``."""

    reason = 'unspecified'

    def __init__(self, message, reason=None, **detail):
        super().__init__(message)
        if reason is not None:
            self.reason = reason
        self.detail = detail


class CapExceeded(SizingStop):
    pass


class PreflightFailed(SizingStop):
    reason = 'preflight'


class UnexpectedFile(SizingStop):
    reason = 'unexpected_file'


class TransferFailed(SizingStop):
    reason = 'transfer_failed'


class VolumeCheckFailed(SizingStop):
    reason = 'volume_check'


class ParserGuard(SizingStop):
    """Memory, expansion, XML-safety or malformed-XML guard tripped."""


class JournalError(SizingStop):
    reason = 'journal'


class RunRefused(Exception):
    """Raised before any journal exists: the run never starts (no final status is written)."""


class SizingOnlyRefused(Exception):
    """A selection, promotion or export boundary was offered sizing-only output."""


class Interrupted(BaseException):
    """Raised by the signal handler; ends the run with final status ``interrupted``."""
