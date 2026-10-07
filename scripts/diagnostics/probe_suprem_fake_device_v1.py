"""Generate tiny invented CPU fixtures; observe fake-load devices, never accept a source path."""
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).absolute().parents[2]
TAGS = ("cpu", "cuda:0", "cuda:3", "mps:0")
READER_PIN = "69f81f52088026b567c4a36ffba7d602e94d5d36ac930cd95a54cffe37e5f06a"
SECONDS, RSS, POLL = 15, 3 * 1024**3, .05
OUT_BYTES, ERR_BYTES = 8192, 4096
SCHEMA = "fake-device-probe-report-1"


class Refusal(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise Refusal(reason)


def report(tag):
    return dict(schema_version=SCHEMA, evidence_domain="invented_fake_device", status="refused",
                reason="not_completed", fixture_tag=tag, observation=None, io=None, resources=None,
                execution_authority="none", training_eligible=False, values_audited=False,
                actual_source_access=False)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sample(child=None):
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,rss="], capture_output=True,
                            timeout=1, check=False)
    require(result.returncode == 0 and len(result.stdout) <= 4 * 1024**2, "monitor_unavailable")
    try:
        rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines() if line.strip()]
        require(all(len(x) == 3 and all(n >= 0 for n in x) for x in rows), "monitor_unavailable")
    except ValueError:
        raise Refusal("monitor_unavailable")
    require(any(pid == os.getpid() for pid, _, _ in rows), "monitor_unavailable")
    owned = set() if child is None else {child}
    while True:
        following = owned | {pid for pid, parent, _ in rows if parent in owned}
        if following == owned:
            break
        owned = following
    return sum(rss * 1024 for pid, _, rss in rows if pid in owned or pid == os.getpid())


def validate_report(value, tag):
    require(type(value) is dict and set(value) == set(report(tag)), "worker_report_fields")
    for key in ("schema_version", "evidence_domain", "fixture_tag", "execution_authority"):
        require(value[key] == report(tag)[key], "worker_report_binding")
    require(all(value[k] is False for k in ("training_eligible", "values_audited", "actual_source_access")),
            "worker_report_authority")
    require(value["status"] in ("pass", "refused") and type(value["reason"]) is str and
            0 < len(value["reason"]) < 128 and value["resources"] is None, "worker_report_status")
    if value["status"] == "refused":
        require(value["observation"] is None and value["io"] is None, "partial_worker_report")
        return value
    observation = value["observation"]
    fields = {"shape", "dtype", "stride", "logical_bytes", "serialized_storage_tag", "tensor_device",
              "storage_device", "is_fake_tensor", "storage_file_offset", "storage_bytes", "checks"}
    require(type(observation) is dict and set(observation) == fields, "observation_fields")
    require(observation["shape"] == [2, 3] and observation["stride"] == [3, 1] and
            observation["dtype"] == "torch.float32" and observation["logical_bytes"] == 24 and
            observation["storage_bytes"] == 24 and observation["is_fake_tensor"] is True and
            type(observation["storage_file_offset"]) is int and
            0 < observation["storage_file_offset"] < 65536, "fixture_metadata_mismatch")
    require(observation["serialized_storage_tag"] == tag and
            all(type(observation[k]) is str and len(observation[k]) <= 16
                for k in ("tensor_device", "storage_device")), "fixture_device_mismatch")
    checks = observation["checks"]
    require(type(checks) is dict and set(checks) ==
            {"source_tag_is_cpu", "tensor_is_cpu", "storage_is_meta", "reader2_guard_would_pass"}
            and all(type(x) is bool for x in checks.values()), "check_fields")
    expected = dict(source_tag_is_cpu=tag == "cpu", tensor_is_cpu=observation["tensor_device"] == "cpu",
                    storage_is_meta=observation["storage_device"] == "meta")
    expected["reader2_guard_would_pass"] = all(expected.values())
    require(checks == expected, "check_binding")
    evidence = value["io"]
    require(type(evidence) is dict and set(evidence) == {"aggregate_requested_bytes", "hash_bytes",
            "metadata_source_bytes", "metadata_storage_source_bytes", "virtual_zero_bytes"} and
            all(type(x) is int and x >= 0 for x in evidence.values()), "io_fields")
    require(0 < evidence["hash_bytes"] <= 65536 and evidence["metadata_storage_source_bytes"] == 0 and
            evidence["aggregate_requested_bytes"] == sum(evidence[k] for k in
            ("hash_bytes", "metadata_source_bytes", "virtual_zero_bytes")) and
            evidence["aggregate_requested_bytes"] <= evidence["hash_bytes"] + 128 * 1024,
            "io_binding")
    require(value["reason"] == "invented_device_observations_complete", "worker_pass_reason")
    return value


def probe_fixture(tag):
    """Closed enum only: the worker creates the fixture itself, with no caller file access."""
    require(type(tag) is str and tag in TAGS, "fixture_tag_refused")
    value = report(tag)
    start, process, peak, samples = time.monotonic(), None, 0, 0
    out, err = bytearray(), bytearray()
    try:
        require(os.name == "posix" and sys.platform in ("darwin", "linux"), "monitor_platform")
        peak, samples = sample(), 1
        require(peak <= RSS, "aggregate_rss_limit")
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
               "TMPDIR": str(Path(tempfile.gettempdir()).resolve()), "TORCH_FORCE_WEIGHTS_ONLY_LOAD": "1"}
        process = subprocess.Popen([sys.executable, "-I", str(Path(__file__).resolve()), "--owned-worker"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
            start_new_session=True, cwd=ROOT, env=env)
        process.stdin.write(canonical({"tag": tag}))
        process.stdin.close()
        with selectors.DefaultSelector() as sel:
            for stream, label in ((process.stdout, "out"), (process.stderr, "err")):
                sel.register(stream, selectors.EVENT_READ, label)
            while sel.get_map():
                require(time.monotonic() - start <= SECONDS, "worker_time_limit")
                peak, samples = max(peak, sample(process.pid)), samples + 1
                require(peak <= RSS, "aggregate_rss_limit")
                for key, _ in sel.select(POLL):
                    chunk = os.read(key.fileobj.fileno(), 4096)
                    if not chunk:
                        sel.unregister(key.fileobj)
                    elif key.data == "out":
                        require(len(out) + len(chunk) <= OUT_BYTES, "worker_output_limit")
                        out.extend(chunk)
                    else:
                        require(len(err) + len(chunk) <= ERR_BYTES, "worker_stderr_limit")
                        err.extend(chunk)
        require(process.wait(timeout=1) == 0, "worker_exit_failure")
        value = validate_report(json.loads(out), tag)
    except Refusal as exc:
        value = report(tag)
        value["reason"] = str(exc)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        value = report(tag)
        value["reason"] = "worker_monitor_or_report_failure"
    finally:
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=.2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=1)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        value["resources"] = dict(elapsed_seconds=round(time.monotonic() - start, 6),
            aggregate_sampled_peak_rss_bytes=peak, samples=samples, poll_seconds=POLL,
            owned_worker_reaped=process is None or process.poll() is not None,
            exit_code=None if process is None else process.returncode,
            stderr_bytes=len(err))
    return value


def _fixture_bytes(torch, tag):
    tensor = torch.tensor([[1., 2., 3.], [4., 5., 6.]], dtype=torch.float32, device="cpu")
    registry = list(torch.serialization._package_registry)
    raw = io.BytesIO()
    try:
        torch.serialization.register_package(0, lambda storage: tag if storage.device.type == "cpu" else None,
                                             lambda storage, location: None)
        torch.save({"net": {"weight": tensor}}, raw)
    finally:
        torch.serialization._package_registry[:] = registry
    require(len(raw.getbuffer()) <= 65536, "fixture_file_limit")
    return raw.getvalue()


def _generate_observations(tag):
    require(type(tag) is str and tag in TAGS, "fixture_tag_refused")
    sys.path.insert(0, str(ROOT))
    from src.models import segmenter_checkpoint_source_inspection_v2 as reader
    require(reader.reader_sha256() == READER_PIN, "reader_pin_mismatch")
    import torch
    from torch._subclasses.fake_tensor import FakeTensor, FakeTensorMode
    value = report(tag)
    raw = _fixture_bytes(torch, tag)
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-device-",
                                     dir=Path(tempfile.gettempdir()).resolve()) as folder:
        path = Path(folder) / "invented-device.pth"
        with path.open("xb") as file:
            file.write(raw)
        bounds = reader.limits()
        bounds.update(max_file_bytes=65536, max_metadata_read_bytes=128 * 1024,
                      max_directory_bytes=16384, max_pickle_bytes=16384, max_members=8,
                      max_storages=4, max_storage_bytes=1024, max_report_bytes=8192,
                      max_worker_seconds=SECONDS)
        control = dict(schema_version=reader.CONTROL_VERSION, evidence_domain=reader.DOMAIN,
            source=dict(root=str(path.parent), path=str(path), bytes=len(raw),
                        sha256=hashlib.sha256(raw).hexdigest(), identity=reader._identity_record(path.stat()),
                        root_identity=reader._identity_record(path.parent.stat(), True),
                        volume=dict(mount="invented", uuid="invented", filesystem="invented",
                                    device=path.stat().st_dev, fsid=[0, 0], method="invented")),
            architecture=reader.architecture(), expected_signature=reader.expected_signature(),
            namespace="identity", wrapper="net_optimizer_scheduler_epoch", limits=bounds,
            request=dict(run_id="invented_device_diag", reader_sha256=READER_PIN,
                         consumption_receipt_sha256=hashlib.sha256(b"invented device diagnostic").hexdigest()))
        control = reader._validate_control(path, control, reader.control_sha256(control))
        with reader._Source(control) as source:
            source.hash()
            archive, storages = reader._archive(source)
            require(archive["storage_count"] == 1 and archive["declared_storage_bytes"] == 24,
                    "fixture_storage_mismatch")
            with FakeTensorMode(allow_fallback_kernels=False):
                torch.serialization.clear_safe_globals()
                require(torch.serialization.get_safe_globals() == [], "ambient_safe_globals")
                blob = torch.load(reader._View(source), weights_only=True, map_location="cpu", mmap=False)
            require(torch.serialization.get_safe_globals() == [], "safe_globals_changed")
            require(type(blob) is dict and set(blob) == {"net"} and type(blob["net"]) is dict and
                    set(blob["net"]) == {"weight"}, "fixture_wrapper_mismatch")
            tensor = blob["net"]["weight"]
            require(type(tensor) is FakeTensor, "fixture_not_fake")
            storage = tensor.untyped_storage()
            offset = getattr(storage, "_checkpoint_offset", None)
            require(type(offset) is int and offset in storages and storages[offset]["bytes"] == 24,
                    "fixture_storage_offset")
            observation = dict(shape=list(tensor.shape), dtype=str(tensor.dtype), stride=list(tensor.stride()),
                logical_bytes=tensor.numel() * tensor.element_size(),
                serialized_storage_tag=getattr(storage, "_fake_device", None), tensor_device=str(tensor.device),
                storage_device=str(storage.device), is_fake_tensor=True, storage_file_offset=offset,
                storage_bytes=storage.nbytes())
            checks = dict(source_tag_is_cpu=observation["serialized_storage_tag"] == "cpu",
                          tensor_is_cpu=tensor.device.type == "cpu", storage_is_meta=storage.device.type == "meta")
            checks["reader2_guard_would_pass"] = all(checks.values())
            observation["checks"] = checks
            source.check()
            value.update(status="pass", reason="invented_device_observations_complete",
                         observation=observation, io=source.evidence())
        return validate_report(value, tag)


def _worker():
    raw = sys.stdin.buffer.read(257)
    require(len(raw) <= 256, "worker_input_limit")
    inputs = json.loads(raw)
    require(type(inputs) is dict and set(inputs) == {"tag"}, "worker_input_fields")
    tag = inputs["tag"]
    require(type(tag) is str and tag in TAGS, "fixture_tag_refused")
    try:
        value = _generate_observations(tag)
    except (Refusal, OSError, ValueError, TypeError, RuntimeError, KeyError):
        value = report(tag)
        value["reason"] = "invented_fixture_or_load_refused"
    encoded = canonical(value)
    require(len(encoded) <= OUT_BYTES, "worker_report_limit")
    sys.stdout.buffer.write(encoded)


def main():
    if sys.argv[1:] == ["--owned-worker"]:
        _worker()
        return
    require(sys.argv[1:] == ["--invented-device-probe"], "invented_invocation_required")
    failed = False
    for tag in TAGS:
        value = probe_fixture(tag)
        print(canonical(value).decode(), end="")
        failed = failed or value["status"] != "pass"
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
