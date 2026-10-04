"""One D-341 native invented setup probe. No live S2 execution interface."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.operations.literature_storage_v1 import (LiteratureStorage, NativeVolume,
                                                 load_capability, read_regular)


def imaging_idle():
    result = subprocess.run(["/bin/ps", "-axo", "pid=,command="], check=True,
                            capture_output=True, text=True, timeout=10)
    busy = []
    for line in result.stdout.splitlines():
        try:
            pid, command = line.strip().split(None, 1)
            args = shlex.split(command)
        except ValueError:
            continue
        if args and "python" in Path(args[0]).name and "pytest" not in args:
            if any(any(word in a for word in ("segmenter_", "localizer_", "train_", "run_s_sizing"))
                   for a in args[1:]):
                busy.append(int(pid))
    if busy:
        raise RuntimeError(f"imaging/sizing is not idle; worker PIDs {busy}")
    return dict(active_worker_pids=busy, method="native ps; Python imaging/sizing command arguments")


class FaultProbe:
    def __init__(self, native):
        self.native, self.failed = native, False

    def observe(self):
        obs = self.native.observe()
        if self.failed:
            obs["writable"] = False  # Invented observation; do not alter/disconnect the drive.
        return obs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--capability-sha256", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--result", required=True, help="exclusive local result path, outside public Git")
    args = parser.parse_args()
    idle = imaging_idle()
    cap = load_capability(args.capability, args.capability_sha256)
    primary = FaultProbe(NativeVolume(cap.external_mount, "literature"))
    storage = LiteratureStorage(args.registry, cap, primary=primary,
                                internal=NativeVolume(cap.internal_mount, "fallback"))
    before = storage.verify()
    storage.setup()
    with storage.writer(cap.writer_id) as writer:
        writer.begin()
        data = b"PROWL S1 invented probe; no literature or clinical content.\n" * 1024
        writer.write_invented("invented-probe.txt", data)
        probe_path = str(Path(cap.scratch_root) / writer.name / "invented-probe.txt")
        assert read_regular(probe_path) == data
        writer.record("readback_verified")
        try:
            with storage.writer(cap.writer_id):
                raise AssertionError("second writer acquired the lease")
        except BlockingIOError:
            pass
        writer.record("lock_contention_verified")
        primary.failed = True
        try:
            writer.write_invented("must-not-exist.txt", b"invented")
        except Exception as exc:
            fault = dict(type=type(exc).__name__, message=str(exc))
        else:
            raise AssertionError("primary failure did not stop payload")
        writer.record("stopped_primary_failure")
        assert not os.path.lexists(str(Path(cap.scratch_root) / writer.name / "must-not-exist.txt"))
        primary.failed = False
        events = [json.loads(line) for line in read_regular(str(Path(cap.receipts_dir) / writer.journal_name)).splitlines()]
        fallback = [json.loads(line) for line in read_regular(str(Path(cap.fallback_dir) / writer.journal_name)).splitlines()]
        assert [e["sequence"] for e in events + fallback] == [1, 2, 3, 4]
        assert fallback[-1]["event"] == "stopped_primary_failure"
        assert "completed" not in [e["event"] for e in events + fallback]
    after = storage.verify()
    sizing_observation = storage.sizing_start_check()  # Read only, no signing or run allocation.
    result = dict(status="bounded_native_setup_passed", imaging_idle=idle,
                  capability_sha256=args.capability_sha256, capability=asdict(cap),
                  before=before, after=after, sizing_observation=sizing_observation,
                  payload_bytes=len(data), payload_sha256=hashlib.sha256(data).hexdigest(),
                  primary_events=events, fallback_events=fallback, injected_fault=fault,
                  run_s_authorized=False, binding_implemented=False,
                  code_sha256={str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (Path(__file__), REPO / "src/operations/literature_storage_v1.py")})
    with open(args.result, "x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(dict(status=result["status"], payload_bytes=len(data), result=args.result,
                          run_s_authorized=False)))


if __name__ == "__main__":
    main()
