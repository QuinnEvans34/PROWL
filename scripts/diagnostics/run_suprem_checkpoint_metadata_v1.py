"""R04: pinned, consumed, single metadata attempt; never scientific authorization."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT))
from src.models import segmenter_checkpoint_source_inspection_v1 as reader

RUN_ID = "SUPREM_META_20261006_B01"
VERSION = "checkpoint-metadata-dispatch-1"
APPROVAL_VERSION = "checkpoint-metadata-dispatch-approval-1"
REPORT_VERSION = "checkpoint-metadata-dispatch-report-1"
MEMBERS = {"control.json", "approval.json", "consumption-receipt.json", "report.json", "attempt.log"}
MAX_OUTPUT = 4 * 1024**2
HEADROOM = 1024**3
MAX_SECONDS = 90
MAX_RSS = 3 * 1024**3
POLL = .05
AUTHORIZATION = dict(approved_by="Quinton Evans", date="2026-10-06",
                    instruction="Yes, I approve. How close are we to training?",
                    scope="R04_single_metadata_attempt")
INVENTED_AUTHORIZATION = dict(approved_by="invented test", date="invented",
                              instruction="invented dispatch qualification", scope="invented")
FIXED_READER_PINS = {
    "src/models/segmenter_checkpoint_source_inspection_v1.py": "ffa33c8147805e2379807f3b3da81df5622d91e04925ce5ed776e753d5ed4f6f",
    "tests/test_segmenter_checkpoint_source_inspection_v1.py": "aaad6ad6676f004354a32ce30fa0393b8cfc30c2045064cad4dbe23c3c8c6f09",
    "docs/capstone/imaging/SEGMENTER-CHECKPOINT-SOURCE-INSPECTION-CONTRACT-V1.md": "af259acd80ebf6bf685664870e6563452e93171d36ebaad95a8b1a1285247360",
}
OWN_PATHS = (
    "scripts/diagnostics/run_suprem_checkpoint_metadata_v1.py",
    "tests/test_suprem_checkpoint_metadata_dispatch_v1.py",
    "docs/capstone/imaging/SUPREM-CHECKPOINT-METADATA-DISPATCH-CONTRACT-V1.md",
)
Refusal = reader.Refusal
require = reader._require
canonical = reader._json_bytes
digest = reader.control_sha256


def bounds(domain):
    return dict(max_output_bytes=MAX_OUTPUT, headroom_bytes=HEADROOM, max_seconds=MAX_SECONDS,
                max_aggregate_rss_bytes=MAX_RSS, poll_seconds=POLL,
                max_read_bytes=64889231 if domain == reader.ACTUAL_DOMAIN else None)


def code_pins():
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (*FIXED_READER_PINS, *OWN_PATHS)}
    require(all(pins[p] == sha for p, sha in FIXED_READER_PINS.items()), "delivered_reader_changed")
    return pins


def environment():
    return dict(python=sys.version.split()[0], executable=str(Path(sys.executable).absolute()),
                torch=importlib.metadata.version("torch"), monai=importlib.metadata.version("monai"))


def identity(info, root=False):
    value = dict(device=info.st_dev, inode=info.st_ino, mode=info.st_mode, owner=info.st_uid)
    if not root:
        value.update(links=info.st_nlink, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)
    return value


def directory_fd(path):
    path = Path(path)
    require(path.is_absolute() and str(path) == str(path.absolute()) and
            all(p not in (".", "..") for p in str(path).split("/")), "unsafe_directory_path")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        info = os.fstat(fd)
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) & 0o022 == 0,
                "unsafe_directory_owner_or_mode")
        return fd
    except BaseException:
        os.close(fd)
        raise


def observe_volume(path, domain):
    if domain == reader.DOMAIN:
        return dict(mount="invented", uuid="invented", filesystem="invented")
    v = reader._observe_volume(path)
    require(v["filesystem"] == "apfs", "output_volume_unqualified")
    return v


def source_metadata(path, domain):
    """No leaf open/hash/decode; traverse ancestors and stat the exact leaf."""
    path = Path(path)
    fd = directory_fd(path.parent)
    try:
        root_info = os.fstat(fd)
        info = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid(),
                "source_type_links_owner")
        require(info.st_dev == root_info.st_dev, "source_root_device_mismatch")
        volume = observe_volume(path.parent, domain)
        require(identity(os.stat(path.parent, follow_symlinks=False), True) == identity(root_info, True),
                "source_root_replaced")
        require(identity(os.stat(path.name, dir_fd=fd, follow_symlinks=False)) == identity(info),
                "source_identity_drift")
        return dict(root=str(path.parent), path=str(path), bytes=info.st_size,
                    identity=identity(info), root_identity=identity(root_info, True), volume=volume)
    finally:
        os.close(fd)


def output_observation(parent, domain):
    fd = directory_fd(parent)
    try:
        info = os.fstat(fd)
        volume = observe_volume(parent, domain)
        require(identity(os.stat(parent, follow_symlinks=False), True) == identity(info, True),
                "output_parent_replaced")
        fs = os.fstatvfs(fd)
        free = fs.f_bavail * fs.f_frsize
        require(free - MAX_OUTPUT >= HEADROOM, "output_headroom_limit")
        return dict(parent_identity=identity(info, True), volume=volume), free
    finally:
        os.close(fd)


def _reader_approval(control):
    return dict(schema_version="checkpoint-metadata-approval-1", approved_by="Quinton Evans",
                operation="single_checkpoint_metadata", run_id=control["request"]["run_id"],
                control_sha256=digest(control), reader_sha256=reader.reader_sha256(),
                consumption_receipt_sha256=control["request"]["consumption_receipt_sha256"],
                source_sha256=control["source"]["sha256"])


def prepare(run_id, authorization, *, invented_source=None, invented_output=None, invented_sha=None):
    """Trusted caller transcribes actual approval. Tests supply explicit invented provenance."""
    domain = reader.ACTUAL_DOMAIN if invented_source is None else reader.DOMAIN
    require(authorization == (AUTHORIZATION if domain == reader.ACTUAL_DOMAIN else INVENTED_AUTHORIZATION),
            "authorization_missing_or_out_of_scope")
    if domain == reader.ACTUAL_DOMAIN:
        require(run_id == RUN_ID and invented_output is None and invented_sha is None, "actual_scope_mismatch")
        source_path = reader.candidate_locator()
        output = ROOT / "outputs/prowl" / ("SUPREM-CHECKPOINT-INSPECTION-" + RUN_ID)
        source_sha = reader.ACTUAL_CANDIDATE_SHA
    else:
        require(type(run_id) is str and run_id.startswith("invented_") and
                reader.re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id) is not None, "invented_run_id")
        source_path, output = Path(invented_source), Path(invented_output)
        temporary = Path(tempfile.gettempdir()).resolve()
        require(temporary in output.parents and output.parent.name.startswith("prowl-dispatch-invented-"),
                "invented_output_root")
        source_sha = invented_sha
        reader._sha(source_sha)
        require(temporary in source_path.parents and source_path.parent.name.startswith("prowl-source-invented-") and
                reader.re.fullmatch(r"invented-[A-Za-z0-9_.-]+\.pth", source_path.name) is not None and
                source_sha != reader.ACTUAL_CANDIDATE_SHA, "invented_source_scope")
    meta = source_metadata(source_path, domain)
    meta["sha256"] = source_sha
    if domain == reader.ACTUAL_DOMAIN:
        require(meta["bytes"] == 56500623, "actual_size_mismatch")
        require(environment() == dict(python="3.12.13", executable=str(ROOT / ".venv-prowl/bin/python"),
                                      torch="2.13.0", monai="1.6.0"), "actual_environment_mismatch")
    observed, free = output_observation(output.parent, domain)
    require(not os.path.lexists(output), "output_area_already_exists")
    output_record = dict(path=str(output), **observed, observed_free_bytes=free)
    scope = dict(run_id=run_id, domain=domain, source=meta, namespace="uniform_module",
                 output=output_record, pins=code_pins(), environment=environment(), bounds=bounds(domain))
    receipt = dict(schema_version="checkpoint-metadata-consumption-1", run_id=run_id,
                   scope_sha256=digest(scope), state="consumed")
    c = dict(schema_version=reader.CONTROL_VERSION, evidence_domain=domain, source=meta,
             architecture=reader.architecture(), expected_signature=reader.expected_signature(),
             namespace="uniform_module", wrapper="net_optimizer_scheduler_epoch", limits=reader.limits(),
             request=dict(run_id=run_id, reader_sha256=reader.reader_sha256(),
                          consumption_receipt_sha256=digest(receipt)))
    request = dict(schema_version=VERSION, scope=scope, reader_control=c, receipt=receipt,
                   pins=scope["pins"], environment=scope["environment"], output=output_record)
    approval = dict(schema_version=APPROVAL_VERSION, authorization=authorization,
                    request_sha256=digest(request),
                    reader_approval=_reader_approval(c) if domain == reader.ACTUAL_DOMAIN else None)
    reader._validate_control(str(source_path), c, digest(c), approval["reader_approval"],
                             digest(approval["reader_approval"]) if approval["reader_approval"] else None)
    parent_fd = directory_fd(output.parent)
    try:
        require(identity(os.fstat(parent_fd), True) == observed["parent_identity"], "output_parent_replaced")
        os.mkdir(output.name, mode=0o700, dir_fd=parent_fd)
        fd = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        try:
            _write(fd, "control.json", canonical(request))
            _write(fd, "approval.json", canonical(approval))
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)
    return dict(output=str(output), request_sha256=digest(request), approval_sha256=digest(approval),
                source=meta, output_observation=output_record, consumed=False)


def _members(fd):
    names = set(os.listdir(fd))
    require(names <= MEMBERS, "unexpected_output_member")
    total = 0
    for name in names:
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid() and
                stat.S_IMODE(info.st_mode) == 0o600, "unsafe_output_member")
        total += info.st_size
    require(total <= MAX_OUTPUT, "output_byte_limit")
    return names, total


def _write(fd, name, raw):
    require(name in MEMBERS and type(raw) is bytes, "output_member_refused")
    names, total = _members(fd)
    require(name not in names, "output_member_exists")
    require(total + len(raw) <= MAX_OUTPUT, "output_byte_limit")
    member = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(member, view)
            require(count > 0, "output_short_write")
            view = view[count:]
        os.fsync(member)
    finally:
        os.close(member)
    os.fsync(fd)


def _read(fd, name):
    member = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    try:
        info = os.fstat(member)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid() and
                stat.S_IMODE(info.st_mode) == 0o600 and info.st_size <= 1024**2, "unsafe_control_member")
        raw = os.read(member, 1024**2 + 1)
        require(len(raw) == info.st_size and len(raw) <= 1024**2, "control_read_limit")
        require(identity(os.fstat(member)) == identity(info) and
                identity(os.stat(name, dir_fd=fd, follow_symlinks=False)) == identity(info) and
                os.fstat(member).st_size == info.st_size,
                "control_member_drift")
        value = json.loads(raw)
        require(canonical(value) == raw, "noncanonical_control")
        return value
    finally:
        os.close(member)


def validate(request, approval, run_id, request_pin, approval_pin, output):
    require(digest(request) == request_pin and digest(approval) == approval_pin, "external_pin_mismatch")
    reader._fields(request, ("schema_version", "scope", "reader_control", "receipt", "pins", "environment", "output"),
                   "dispatch_control_fields")
    reader._fields(approval, ("schema_version", "authorization", "request_sha256", "reader_approval"),
                   "dispatch_approval_fields")
    require(request["schema_version"] == VERSION and approval["schema_version"] == APPROVAL_VERSION,
            "dispatch_version")
    scope, c = request["scope"], request["reader_control"]
    domain = c["evidence_domain"]
    require(domain in (reader.DOMAIN, reader.ACTUAL_DOMAIN), "dispatch_domain")
    expected_scope = dict(run_id=run_id, domain=domain, source=c["source"], namespace=c["namespace"],
                          output=request["output"], pins=request["pins"], environment=request["environment"],
                          bounds=bounds(domain))
    require(scope == expected_scope and c["request"]["run_id"] == run_id and
            c["namespace"] == "uniform_module", "dispatch_scope_mismatch")
    require(request["pins"] == code_pins() and request["environment"] == environment(), "code_or_environment_drift")
    if domain == reader.ACTUAL_DOMAIN:
        require(run_id == RUN_ID and output == ROOT / "outputs/prowl" / ("SUPREM-CHECKPOINT-INSPECTION-" + RUN_ID),
                "actual_dispatch_locator")
        auth = AUTHORIZATION
    else:
        require(run_id.startswith("invented_") and Path(tempfile.gettempdir()).resolve() in output.parents and
                output.parent.name.startswith("prowl-dispatch-invented-"), "invented_dispatch_locator")
        auth = INVENTED_AUTHORIZATION
    expected_receipt = dict(schema_version="checkpoint-metadata-consumption-1", run_id=run_id,
                            scope_sha256=digest(scope), state="consumed")
    require(request["receipt"] == expected_receipt and digest(expected_receipt) ==
            c["request"]["consumption_receipt_sha256"], "receipt_binding_mismatch")
    require(approval == dict(schema_version=APPROVAL_VERSION, authorization=auth,
            request_sha256=request_pin,
            reader_approval=_reader_approval(c) if domain == reader.ACTUAL_DOMAIN else None),
            "authorization_or_approval_mismatch")
    reader._fields(request["output"], ("path", "parent_identity", "volume", "observed_free_bytes"), "output_fields")
    require(request["output"]["path"] == str(output) and type(request["output"]["observed_free_bytes"]) is int and
            request["output"]["observed_free_bytes"] >= HEADROOM + MAX_OUTPUT, "output_scope_mismatch")
    reader._validate_control(c["source"]["path"], c, digest(c), approval["reader_approval"],
                             digest(approval["reader_approval"]) if approval["reader_approval"] else None)
    return c


def check_current(request, output, fd, initial):
    require(identity(os.stat(output, follow_symlinks=False), True) == initial and
            identity(os.fstat(fd), True) == initial, "output_directory_replaced")
    domain = request["reader_control"]["evidence_domain"]
    observed, _ = output_observation(output.parent, domain)
    expected = {k: request["output"][k] for k in ("parent_identity", "volume")}
    require(observed == expected, "output_volume_or_parent_drift")
    meta = source_metadata(Path(request["reader_control"]["source"]["path"]), domain)
    source = dict(request["reader_control"]["source"])
    source.pop("sha256")
    require(meta == source, "source_preflight_drift")
    _members(fd)


def _process_rows():
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,pgid=,rss="], capture_output=True,
                            text=True, timeout=1, check=False)
    require(result.returncode == 0 and len(result.stdout) <= 4 * 1024**2, "aggregate_monitor_unavailable")
    try:
        rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines() if line.strip()]
        require(all(len(r) == 4 and all(x >= 0 for x in r) for r in rows), "aggregate_monitor_unavailable")
        return rows
    except ValueError:
        raise Refusal("aggregate_monitor_unavailable")


def _aggregate(rows, worker_pid):
    descendants = {worker_pid}
    while True:
        expanded = descendants | {pid for pid, parent, group, rss in rows if parent in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    require(any(pid == os.getpid() for pid, _, _, _ in rows), "aggregate_monitor_unavailable")
    total = sum(rss * 1024 for pid, parent, group, rss in rows if pid in descendants or pid == os.getpid())
    groups = {group for pid, parent, group, rss in rows if pid in descendants}
    require(os.getpgrp() not in groups, "owned_process_group_mismatch")
    return total, groups


def _stop(process, groups):
    # Intermediary handles SIGTERM so R01 can reap its child in its own finally block.
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
    for group in groups - {process.pid}:
        try:
            os.killpg(group, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is not None:
            stream.close()


def _run_reader(request, approval, started):
    require(os.name == "posix" and sys.platform in ("darwin", "linux"), "dispatch_platform_unqualified")
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(Path(tempfile.gettempdir()).resolve()),
           "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "TORCH_FORCE_WEIGHTS_ONLY_LOAD": "1"}
    process = subprocess.Popen([sys.executable, "-I", str(Path(__file__).absolute()), "--owned-worker"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=env, start_new_session=True, close_fds=True)
    peak, samples, groups, out, err = 0, 0, {process.pid}, bytearray(), bytearray()
    reason, value = None, None
    try:
        current, observed = _aggregate(_process_rows(), process.pid)
        peak, groups, samples = current, groups | observed, 1
        require(peak <= MAX_RSS, "aggregate_rss_limit")
        require(time.monotonic() - started <= MAX_SECONDS, "dispatch_time_limit")
        process.stdin.write(canonical(dict(request=request, approval=approval)))
        process.stdin.close()
        with selectors.DefaultSelector() as selector:
            for stream, tag in ((process.stdout, "out"), (process.stderr, "err")):
                selector.register(stream, selectors.EVENT_READ, tag)
            while selector.get_map():
                require(time.monotonic() - started <= MAX_SECONDS, "dispatch_time_limit")
                current, observed = _aggregate(_process_rows(), process.pid)
                peak, groups, samples = max(peak, current), groups | observed, samples + 1
                require(peak <= MAX_RSS, "aggregate_rss_limit")
                for key, _ in selector.select(POLL):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                    elif key.data == "out":
                        out.extend(data)
                        require(len(out) <= 1024**2, "dispatch_worker_output_limit")
                    else:
                        err.extend(data)
                        require(len(err) <= 65536, "dispatch_worker_log_limit")
        require(process.wait(timeout=1) == 0, "dispatch_worker_exit")
        value = json.loads(out)
        reader._fields(value, ("reader", "peak_rss_bytes"), "dispatch_worker_fields")
        require(type(value["peak_rss_bytes"]) is int and value["peak_rss_bytes"] <= MAX_RSS,
                "dispatch_worker_post_peak_limit")
        result = value["reader"]
        require(type(result) is dict and set(result) == set(reader._report()) and
                result["schema_version"] == reader.REPORT_VERSION and
                result["evidence_domain"] == request["reader_control"]["evidence_domain"] and
                result["scope"] == "checkpoint_metadata_only" and result["execution_authority"] == "none" and
                result["training_eligible"] is False and result["values_audited"] is False and
                result["status"] in ("pass", "refused"), "dispatch_reader_report_invalid")
    except Refusal as exc:
        reason = str(exc)
        result = reader._report(reason, domain=request["reader_control"]["evidence_domain"])
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        reason = "dispatch_worker_or_monitor_failed"
        result = reader._report(reason, domain=request["reader_control"]["evidence_domain"])
    finally:
        _stop(process, groups)
    return result, dict(aggregate_sampled_peak_rss_bytes=peak, samples=samples, poll_seconds=POLL,
                        intermediary_peak_rss_bytes=value.get("peak_rss_bytes") if type(value) is dict else None,
                        stderr_bytes=len(err), exit_code=process.returncode, owned_worker_reaped=True,
                        termination_reason=reason)


def _validate_pass(result, control):
    require(type(result) is dict and set(result) == set(reader._report()) and
            result["schema_version"] == reader.REPORT_VERSION and
            result["evidence_domain"] == control["evidence_domain"] and
            result["scope"] == "checkpoint_metadata_only" and result["execution_authority"] == "none" and
            result["training_eligible"] is False and result["values_audited"] is False and
            result["status"] in ("pass", "refused"), "dispatch_reader_report_invalid")
    if result["status"] != "pass":
        return
    require(result["identity_verified"] is True and result["metadata_compatible"] is True and
            result["control_sha256"] == digest(control) and
            result["source_sha256"] == control["source"]["sha256"] and
            result["source_bytes"] == control["source"]["bytes"] and
            result["request_sha256"] == digest(control["request"]) and
            len(result["model"]) == 83, "reader_pass_binding_mismatch")
    io = result["io"]
    require(io["hash_bytes"] == control["source"]["bytes"] and
            io["metadata_storage_source_bytes"] == 0 and
            io["aggregate_requested_bytes"] <= control["source"]["bytes"] + 8 * 1024**2,
            "reader_pass_io_mismatch")


def dispatch(run_id, request_path, approval_path, request_pin, approval_pin):
    started = time.monotonic()
    output = Path(request_path).parent
    require(Path(request_path).name == "control.json" and Path(approval_path) == output / "approval.json",
            "dispatch_input_paths")
    fd = directory_fd(output)
    consumed = False
    report = dict(schema_version=REPORT_VERSION, status="refused", reason="dispatch_not_completed",
                  scope="checkpoint_metadata_only", execution_authority="none", training_eligible=False,
                  values_audited=False, run_id=run_id, request_sha256=request_pin, approval_sha256=approval_pin,
                  consumed=False, reader=None, resources=None)
    try:
        initial = identity(os.fstat(fd), True)
        require(stat.S_IMODE(initial["mode"]) == 0o700, "output_area_not_private")
        require(_members(fd)[0] == {"control.json", "approval.json"}, "attempt_already_consumed_or_partial")
        request, approval = _read(fd, "control.json"), _read(fd, "approval.json")
        c = validate(request, approval, run_id, request_pin, approval_pin, output)
        check_current(request, output, fd, initial)
        _write(fd, "consumption-receipt.json", canonical(request["receipt"]))
        consumed = True
        report["consumed"] = True
        try:
            result, resources = _run_reader(request, approval, started)
            report["reader"], report["resources"] = result, resources
            _validate_pass(result, c)
            check_current(request, output, fd, initial)
            require(digest(_read(fd, "control.json")) == request_pin and
                    digest(_read(fd, "approval.json")) == approval_pin, "prepared_controls_drift")
            require(time.monotonic() - started <= MAX_SECONDS, "dispatch_time_limit")
            report["status"], report["reason"] = result["status"], result["reason"]
        except Refusal as exc:
            report["reason"] = str(exc)
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
            report["reason"] = "dispatch_worker_or_observer_failed"
        report["resources"] = dict(report["resources"] or {}, elapsed_seconds=round(time.monotonic() - started, 6))
        require(identity(os.stat(output, follow_symlinks=False), True) == initial, "output_directory_replaced")
        _write(fd, "report.json", canonical(report))
        _write(fd, "attempt.log", canonical(dict(status=report["status"], reason=report["reason"],
                    consumed=True, source_values_read=False, execution_authority="none")))
        _members(fd)
        return report
    finally:
        os.close(fd)


def _owned_worker():
    import resource
    def interrupted(*args):
        raise Refusal("dispatch_cancelled")
    signal.signal(signal.SIGTERM, interrupted)
    raw = sys.stdin.buffer.read(1024**2 + 1)
    require(len(raw) <= 1024**2, "dispatch_worker_input_limit")
    value = json.loads(raw)
    reader._fields(value, ("request", "approval"), "dispatch_worker_input_fields")
    r, a = value["request"], value["approval"]
    c = validate(r, a, r["scope"]["run_id"], digest(r), digest(a), Path(r["output"]["path"]))
    fd = directory_fd(Path(r["output"]["path"]))
    try:
        require(_read(fd, "consumption-receipt.json") == r["receipt"], "worker_receipt_missing_or_mismatched")
    finally:
        os.close(fd)
    result = reader.inspect_source_checkpoint(c["source"]["path"], pinned_control=c,
        expected_control_sha256=digest(c), approval=a["reader_approval"],
        expected_approval_sha256=digest(a["reader_approval"]) if a["reader_approval"] else None)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = peak if sys.platform == "darwin" else peak * 1024
    sys.stdout.buffer.write(canonical(dict(reader=result, peak_rss_bytes=peak)))


def main():
    if sys.argv[1:] == ["--owned-worker"]:
        _owned_worker()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("run-id", "request", "approval", "request-sha256", "approval-sha256"):
        parser.add_argument("--" + flag, required=True)
    args = parser.parse_args()
    try:
        result = dispatch(args.run_id, args.request, args.approval, args.request_sha256, args.approval_sha256)
        print(json.dumps({k: result[k] for k in ("status", "reason", "run_id", "consumed", "resources")}, sort_keys=True))
        raise SystemExit(0 if result["status"] == "pass" else 1)
    except (Refusal, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print(json.dumps(dict(status="refused", reason=str(exc) if isinstance(exc, Refusal) else type(exc).__name__)))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
