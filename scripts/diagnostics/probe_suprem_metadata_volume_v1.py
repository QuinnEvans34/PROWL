"""Two approved directory-only diskutil diagnostics; no source leaf access."""
import json
import os
from pathlib import Path
import plistlib
import selectors
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).absolute().parents[2]
ALLOWED = (ROOT / "pretrained_weights", ROOT / "outputs/prowl")
SECONDS, RSS, POLL = 3, 3 * 1024**3, .05
STDOUT, STDERR = 65536, 4096


class Refusal(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise Refusal(reason)


def sample(pid=None):
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,rss="], capture_output=True,
                            text=True, timeout=1, check=False)
    require(result.returncode == 0 and len(result.stdout) <= 4 * 1024**2, "monitor_unavailable")
    try:
        rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines() if line.strip()]
        require(all(len(x) == 3 and all(v >= 0 for v in x) for x in rows), "monitor_unavailable")
    except ValueError:
        raise Refusal("monitor_unavailable")
    require(any(p == os.getpid() for p, _, _ in rows), "monitor_unavailable")
    owned = set() if pid is None else {pid}
    while True:
        enlarged = owned | {p for p, parent, rss in rows if parent in owned}
        if enlarged == owned:
            break
        owned = enlarged
    return sum(rss * 1024 for p, _, rss in rows if p in owned or p == os.getpid())


def probe_one(path, *, domain):
    path = Path(path)
    require(domain in ("volume_diagnostic_only", "invented_volume_diagnostic"), "diagnostic_domain")
    if domain == "volume_diagnostic_only":
        require(path in ALLOWED, "diagnostic_locator")
    else:
        require(Path(tempfile.gettempdir()).resolve() in path.parents and
                path.name.startswith("prowl-volume-invented-"), "invented_locator")
    report = dict(schema_version="metadata-volume-diagnostic-1", domain=domain, path=str(path),
                  status="refused", reason="not_completed", command_returncode=None,
                  stdout_bytes=0, stderr_bytes=0, error=None, volume=None, resources=None,
                  source_payload_bytes=0, execution_authority="none", training_eligible=False)
    start, process, peak, samples = time.monotonic(), None, 0, 0
    out, err = bytearray(), bytearray()
    try:
        require(os.name == "posix" and sys.platform in ("darwin", "linux"), "monitor_platform")
        peak, samples = sample(), 1
        require(peak <= RSS, "aggregate_rss_limit")
        process = subprocess.Popen(["/usr/sbin/diskutil", "info", "-plist", str(path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, start_new_session=True,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
        with selectors.DefaultSelector() as sel:
            sel.register(process.stdout, selectors.EVENT_READ, "out")
            sel.register(process.stderr, selectors.EVENT_READ, "err")
            while sel.get_map():
                require(time.monotonic() - start <= SECONDS, "command_time_limit")
                peak, samples = max(peak, sample(process.pid)), samples + 1
                require(peak <= RSS, "aggregate_rss_limit")
                for key, _ in sel.select(POLL):
                    raw = os.read(key.fileobj.fileno(), 8192)
                    if not raw:
                        sel.unregister(key.fileobj)
                    elif key.data == "out":
                        report["stdout_bytes"] += len(raw)
                        require(len(out) + len(raw) <= STDOUT, "stdout_limit")
                        out.extend(raw)
                    else:
                        report["stderr_bytes"] += len(raw)
                        require(len(err) + len(raw) <= STDERR, "stderr_limit")
                        err.extend(raw)
        report["command_returncode"] = process.wait(timeout=.2)
        require(process.returncode == 0, "command_nonzero")
        fields = plistlib.loads(out)
        require(type(fields) is dict, "plist_fields")
        volume = dict(mount=fields.get("MountPoint"), uuid=fields.get("VolumeUUID"),
                      filesystem=fields.get("FilesystemType"))
        require(all(type(v) is str and 0 < len(v.encode()) <= 512 for v in volume.values()), "plist_volume_fields")
        report.update(status="pass", reason="volume_fields_observed", volume=volume)
    except Refusal as e:
        report["reason"] = str(e)
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        report["reason"] = "tool_monitor_or_plist_failure"
    finally:
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=.2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=1)
            report["command_returncode"] = process.returncode
            process.stdout.close()
            process.stderr.close()
        report["error"] = err.decode("utf-8", errors="replace").encode("utf-8")[:STDERR].decode("utf-8", errors="ignore") or None
        report["resources"] = dict(elapsed_seconds=round(time.monotonic() - start, 6),
            aggregate_sampled_peak_rss_bytes=peak, samples=samples, poll_seconds=POLL,
            owned_child_reaped=process is None or process.poll() is not None)
    return report


if __name__ == "__main__":
    require(sys.argv[1:] == ["--approved-directory-diagnostic"], "trusted_diagnostic_invocation_required")
    for target in ALLOWED:
        print(json.dumps(probe_one(target, domain="volume_diagnostic_only"), sort_keys=True))
