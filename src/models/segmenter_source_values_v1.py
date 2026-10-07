"""V01-I: isolated selective invented values; actual source always refused."""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import struct
import subprocess
import sys
import tempfile
import time
from types import MappingProxyType

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT))
from src.models import segmenter_checkpoint_source_inspection_v2 as meta

DOMAIN = "invented_source_values"
MODEL_BYTES = 18805696
READER_PIN = "69f81f52088026b567c4a36ffba7d602e94d5d36ac930cd95a54cffe37e5f06a"
MAX_IPC = 22 * 1024**2
MAX_RSS = 3 * 1024**3
MAX_SECONDS = 120
REPORT_VERSION = "source-values-report-1"
TOKEN = object()
Refusal = meta.Refusal
require, canonical, digest = meta._require, meta._json_bytes, meta.control_sha256


def code_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def limits(file_bytes):
    return dict(model_bytes=MODEL_BYTES, metadata_bytes=8 * 1024**2,
                total_requested_bytes=file_bytes + 8 * 1024**2 + MODEL_BYTES,
                working_bytes=128 * 1024**2, worker_seconds=MAX_SECONDS, report_bytes=1024**2,
                ipc_bytes=MAX_IPC, aggregate_rss_bytes=MAX_RSS)


@dataclass(frozen=True)
class ValuesAudit:
    state: object
    report_json: bytes
    _token: object

    @property
    def report(self):
        return json.loads(self.report_json)


def state_rows(state):
    import torch
    require(type(state) in (dict, MappingProxyType), "state_mapping_type")
    rows, storages = {}, set()
    for key, tensor in sorted(state.items()):
        require(type(tensor) is torch.Tensor and tensor.device.type == "cpu" and
                tensor.dtype == torch.float32 and tensor.layout == torch.strided and
                tensor.is_contiguous() and tensor.storage_offset() == 0 and not tensor.requires_grad and
                not tensor.is_conj() and not tensor.is_neg(), "state_tensor_type")
        storage = tensor.untyped_storage()
        require(storage.nbytes() == tensor.numel() * 4 and storage.data_ptr() not in storages,
                "state_storage_alias_or_extent")
        storages.add(storage.data_ptr())
        require(bool(torch.isfinite(tensor).all()), "nonfinite_state")
        rows[key] = dict(shape=list(tensor.shape), dtype=str(tensor.dtype),
                         sha256=hashlib.sha256(tensor.numpy().tobytes()).hexdigest())
    return rows


def validate(control, pin, report, report_pin, receipt, acceptance, acceptance_pin, approval, approval_pin):
    require(type(control) is dict and control.get("domain") == DOMAIN, "actual_source_values_unqualified")
    require(acceptance is None and acceptance_pin is None and approval is None and approval_pin is None,
            "invented_acceptance_or_approval_refused")
    require(digest(control) == pin and digest(report) == report_pin, "values_control_or_metadata_pin")
    control, report = json.loads(canonical(control)), json.loads(canonical(report))
    meta._fields(control, ("schema_version", "domain", "reader_control", "metadata_report_sha256",
                          "reader_sha256", "code_sha256", "request", "limits"), "values_control_fields")
    require(control["schema_version"] == "source-values-control-1", "values_control_version")
    require(control["reader_sha256"] == READER_PIN == meta.reader_sha256() and
            control["code_sha256"] == code_sha256(), "values_code_pin")
    c = control["reader_control"]
    require(c["evidence_domain"] == meta.DOMAIN, "actual_reader_source_refused")
    meta._validate_control(c["source"]["path"], c, digest(c))
    require(control["limits"] == limits(c["source"]["bytes"]), "values_limit_mismatch")
    meta._fields(control["request"], ("run_id", "consumption_receipt_sha256"), "values_request_fields")
    run_id = control["request"]["run_id"]
    require(type(run_id) is str and run_id.startswith("invented_") and
            meta.re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id) is not None, "values_run_id")
    require(receipt == dict(schema_version="invented-values-receipt-1", run_id=run_id, domain=DOMAIN, state="consumed")
            and digest(receipt) == control["request"]["consumption_receipt_sha256"], "values_receipt_mismatch")
    require(control["metadata_report_sha256"] == report_pin and type(report) is dict and
            set(report) == set(meta._report()) and report["schema_version"] == meta.REPORT_VERSION and
            report["evidence_domain"] == meta.DOMAIN and report["status"] == "pass" and
            report["identity_verified"] is True and report["metadata_compatible"] is True and
            report["execution_authority"] == "none" and report["training_eligible"] is False and
            report["values_audited"] is False and report["scope"] == "checkpoint_metadata_only" and
            report["source_sha256"] == c["source"]["sha256"] and report["source_bytes"] == c["source"]["bytes"] and
            report["control_sha256"] == digest(c) and report["request_sha256"] == digest(c["request"]) and
            set(report["model"]) == set(meta.expected_signature()), "values_metadata_binding")
    return control, report


class _ValueSource(meta._Source):
    """Separate metered value operation; never modify metadata reader's source guard."""
    def __init__(self, control):
        super().__init__(control)
        self.value_bytes = 0
        self.used_values = set()
        self.selected_spans = set()

    def value_span(self, start, count):
        require((start, count) in self.selected_spans and (start, count) not in self.used_values,
                "value_span_unqualified_or_repeated")
        require(type(start) is int and type(count) is int and start >= 0 and count > 0 and
                start + count <= self.control["source"]["bytes"], "value_span_bounds")
        require(self.value_bytes + count <= MODEL_BYTES and self.requested + self.value_bytes + count <=
                limits(self.control["source"]["bytes"])["total_requested_bytes"], "value_read_budget")
        self.check()
        raw = os.pread(self.fd, count, start)
        self.value_bytes += count
        self.used_values.add((start, count))
        require(len(raw) == count, "value_short_read")
        self.check()
        return raw


def _packing(model, auxiliary):
    require(len(model) == 83 and sum(r["logical_bytes"] for r in model.values()) == MODEL_BYTES,
            "values_full_signature_bytes")
    spans = set()
    for key, row in model.items():
        expected = meta.expected_signature()[key]
        stride, n = [], 1
        for size in reversed(expected["shape"]):
            stride.insert(0, n); n *= size
        require(row["shape"] == expected["shape"] and row["dtype"] == "torch.float32" and
                row["source_device"] == "cpu" and row["stride"] == stride and row["storage_offset"] == 0 and
                row["storage_bytes"] == row["logical_bytes"], "values_dense_packing")
        span = (row["storage_file_offset"], row["storage_bytes"])
        require(span not in spans, "values_model_alias")
        require(row["storage_member"] not in auxiliary["aliases"], "values_auxiliary_alias")
        spans.add(span)
    return spans


def _inspect_local(control, metadata_report):
    import torch
    from torch._subclasses.fake_tensor import FakeTensor, FakeTensorMode
    c = control["reader_control"]
    require(sys.byteorder == "little", "values_host_byteorder")
    with _ValueSource(c) as source:
        source_hash = source.hash()
        archive, storages = meta._archive(source)
        byteorder = [row for row in archive["members"] if row["name"] == "byteorder"]
        require(len(byteorder) == 1 and byteorder[0]["bytes"] == 6 and
                source.metadata(byteorder[0]["payload_offset"], 6) == b"little", "values_byteorder")
        with FakeTensorMode(allow_fallback_kernels=False):
            torch.serialization.clear_safe_globals()
            require(torch.serialization.get_safe_globals() == [], "values_safe_globals")
            blob = torch.load(meta._View(source), weights_only=True, map_location="cpu", mmap=False)
        require(torch.serialization.get_safe_globals() == [], "values_safe_globals_changed")
        model, auxiliary = meta._inventory(blob, c, storages, torch, FakeTensor)
        require(model == metadata_report["model"] and auxiliary == metadata_report["auxiliary"], "values_current_metadata_drift")
        source.selected_spans = _packing(model, auxiliary)
        require(MODEL_BYTES * 4 <= control["limits"]["working_bytes"], "values_allocation_budget")
        state = {}
        for key, row in sorted(model.items()):
            raw = source.value_span(row["storage_file_offset"], row["storage_bytes"])
            tensor = torch.frombuffer(bytearray(raw), dtype=torch.float32).clone().reshape(row["shape"])
            require(bool(torch.isfinite(tensor).all()), "values_nonfinite:" + key)
            state[key] = tensor
        require(source.value_bytes == MODEL_BYTES and len(source.used_values) == 83, "values_read_completeness")
        source.check()
        rows = state_rows(state)
        report = dict(schema_version=REPORT_VERSION, domain=DOMAIN, status="pass", scope="invented_values_only",
            execution_authority="none", training_eligible=False, values_audited=True, source_sha256=source_hash,
            source_bytes=c["source"]["bytes"], control_sha256=digest(control),
            metadata_report_sha256=control["metadata_report_sha256"], code_sha256=code_sha256(), reader_sha256=READER_PIN,
            model=rows, state_sha256=digest(rows), io=dict(source.evidence(), model_value_bytes=source.value_bytes,
                total_requested_bytes=source.requested + source.value_bytes, unique_model_reads=83,
                auxiliary_value_bytes=0), allocation=dict(tensor_payload_bytes=MODEL_BYTES,
                conservative_buffer_tensor_ipc_bound_bytes=MODEL_BYTES * 4, working_ceiling_bytes=128 * 1024**2))
    return ValuesAudit(MappingProxyType(state), canonical(report), TOKEN)


def _report_check(report, control=None):
    meta._fields(report, ("schema_version", "domain", "status", "scope", "execution_authority",
        "training_eligible", "values_audited", "source_sha256", "source_bytes", "control_sha256",
        "metadata_report_sha256", "code_sha256", "reader_sha256", "model", "state_sha256", "io", "allocation"),
        "values_report_fields")
    require(report["schema_version"] == REPORT_VERSION and report["domain"] == DOMAIN and
        report["status"] == "pass" and report["scope"] == "invented_values_only" and
        report["execution_authority"] == "none" and report["training_eligible"] is False and
        report["values_audited"] is True and report["code_sha256"] == code_sha256() and
        report["reader_sha256"] == READER_PIN == meta.reader_sha256(), "values_audit_lineage")
    for name in ("source_sha256", "control_sha256", "metadata_report_sha256", "state_sha256"):
        require(type(report[name]) is str and meta.re.fullmatch(r"[0-9a-f]{64}", report[name]), "values_report_pin")
    require(report["source_sha256"] != meta.ACTUAL_CANDIDATE_SHA, "actual_source_audit_refused")
    require(type(report["source_bytes"]) is int and 0 < report["source_bytes"] <= 64 * 1024**2 and
            type(report["model"]) is dict and set(report["model"]) == set(meta.expected_signature()), "values_report_source")
    io = report["io"]
    meta._fields(io, ("hash_bytes", "metadata_source_bytes", "virtual_zero_bytes", "aggregate_requested_bytes",
        "metadata_storage_source_bytes", "model_value_bytes", "total_requested_bytes", "unique_model_reads",
        "auxiliary_value_bytes"), "values_report_io_fields")
    require(all(type(n) is int and n >= 0 for n in io.values()) and io["hash_bytes"] == report["source_bytes"] and
        io["metadata_storage_source_bytes"] == io["auxiliary_value_bytes"] == 0 and
        io["model_value_bytes"] == MODEL_BYTES and io["unique_model_reads"] == 83 and
        io["metadata_source_bytes"] + io["virtual_zero_bytes"] <= 8 * 1024**2 and
        io["aggregate_requested_bytes"] == io["hash_bytes"] + io["metadata_source_bytes"] + io["virtual_zero_bytes"] and
        io["total_requested_bytes"] == io["aggregate_requested_bytes"] + MODEL_BYTES, "values_report_io")
    require(report["allocation"] == dict(tensor_payload_bytes=MODEL_BYTES,
        conservative_buffer_tensor_ipc_bound_bytes=MODEL_BYTES * 4, working_ceiling_bytes=128 * 1024**2),
        "values_report_allocation")
    if control is not None:
        require(report["control_sha256"] == digest(control) and
            report["source_sha256"] == control["reader_control"]["source"]["sha256"] and
            report["source_bytes"] == control["reader_control"]["source"]["bytes"] and
            report["metadata_report_sha256"] == control["metadata_report_sha256"], "values_ipc_binding")


def _decode(raw, control):
    import torch
    require(len(raw) >= 8, "values_ipc_header")
    size = struct.unpack("<Q", raw[:8])[0]
    require(0 < size <= 1024**2 and len(raw) == 8 + size + MODEL_BYTES, "values_ipc_length")
    encoded, payload = bytes(raw[8:8 + size]), memoryview(raw)[8 + size:]
    report = json.loads(encoded)
    require(canonical(report) == encoded, "values_ipc_report")
    _report_check(report, control)
    state, at = {}, 0
    for key, expected in sorted(meta.expected_signature().items()):
        count = math.prod(expected["shape"]) * 4
        part = payload[at:at + count]; at += count
        row = report["model"][key]
        require(row == dict(expected, sha256=hashlib.sha256(part).hexdigest()), "values_ipc_tensor_hash")
        state[key] = torch.frombuffer(bytearray(part), dtype=torch.float32).clone().reshape(expected["shape"])
    require(state_rows(state) == report["model"] and digest(report["model"]) == report["state_sha256"], "values_ipc_state")
    return ValuesAudit(MappingProxyType(state), encoded, TOKEN)


def inspect_values(control, *, control_sha256, metadata_report, metadata_report_sha256,
                   acceptance=None, acceptance_sha256=None, approval=None, approval_sha256=None, receipt):
    c, m = validate(control, control_sha256, metadata_report, metadata_report_sha256, receipt,
                    acceptance, acceptance_sha256, approval, approval_sha256)
    require(os.name == "posix" and sys.platform in ("darwin", "linux"), "values_monitor_platform")
    inputs = canonical(dict(control=c, metadata_report=m, receipt=receipt))
    require(len(inputs) <= 1024**2, "values_worker_input_limit")
    start, process, out, err = time.monotonic(), None, bytearray(), bytearray()
    try:
        parent = meta._sample_rss(os.getpid())
        require(parent <= MAX_RSS, "values_rss_limit")
        process = subprocess.Popen([sys.executable, "-I", str(Path(__file__).absolute()), "--worker"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
            close_fds=True, env={"PATH":"/usr/bin:/bin", "LC_ALL":"C", "TMPDIR":str(Path(tempfile.gettempdir()).resolve()),
                "OMP_NUM_THREADS":"1", "MKL_NUM_THREADS":"1", "TORCH_FORCE_WEIGHTS_ONLY_LOAD":"1"})
        require(parent + meta._sample_rss(process.pid) <= MAX_RSS, "values_rss_limit")
        os.set_blocking(process.stdin.fileno(), False)
        written = 0
        with selectors.DefaultSelector() as sel:
            sel.register(process.stdin, selectors.EVENT_WRITE, "in")
            sel.register(process.stdout, selectors.EVENT_READ, "out")
            sel.register(process.stderr, selectors.EVENT_READ, "err")
            while sel.get_map():
                require(time.monotonic() - start <= MAX_SECONDS, "values_worker_time")
                total = meta._sample_rss(os.getpid())
                if process.poll() is None:
                    try: total += meta._sample_rss(process.pid)
                    except Refusal: require(process.poll() is not None, "values_monitor_unavailable")
                require(total <= MAX_RSS, "values_rss_limit")
                for key, _ in sel.select(.05):
                    if key.data == "in":
                        try:
                            written += os.write(key.fileobj.fileno(), inputs[written:written + 8192])
                        except BlockingIOError:
                            continue
                        except BrokenPipeError as exc:
                            raise Refusal("values_worker_input_refused") from exc
                        if written == len(inputs):
                            sel.unregister(key.fileobj)
                            process.stdin.close()
                        continue
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk: sel.unregister(key.fileobj)
                    else:
                        buffer, cap = (out, MAX_IPC) if key.data == "out" else (err, 4096)
                        require(len(buffer) + len(chunk) <= cap, "values_worker_output")
                        buffer.extend(chunk)
        require(process.wait(timeout=1) == 0, "values_worker_refused:" + err.decode(errors="replace")[:512])
        require(time.monotonic() - start <= 180, "values_whole_time")
        audit = _decode(out, c)
        require(time.monotonic() - start <= 180, "values_whole_time")
        return audit
    finally:
        if process is not None:
            meta._stop(process)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None: stream.close()


def validate_audit(audit):
    require(type(audit) is ValuesAudit and audit._token is TOKEN and type(audit.report_json) is bytes,
            "values_typed_audit_required")
    report = audit.report
    require(canonical(report) == audit.report_json, "values_audit_encoding")
    _report_check(report)
    rows = state_rows(audit.state)
    require({k: dict(shape=r["shape"], dtype=r["dtype"]) for k, r in rows.items()} == meta.expected_signature() and
            rows == report["model"] and
            digest(rows) == report["state_sha256"], "values_audit_mutated")
    return report


def _worker():
    try:
        raw = sys.stdin.buffer.read(1024**2 + 1)
        require(len(raw) <= 1024**2, "values_worker_input_limit")
        v = json.loads(raw)
        meta._fields(v, ("control", "metadata_report", "receipt"), "values_worker_inputs")
        c, m = validate(v["control"], digest(v["control"]), v["metadata_report"], digest(v["metadata_report"]),
                        v["receipt"], None, None, None, None)
        a = _inspect_local(c, m)
        sys.stdout.buffer.write(struct.pack("<Q", len(a.report_json)) + a.report_json)
        for tensor in a.state.values(): sys.stdout.buffer.write(tensor.numpy().tobytes())
        sys.stdout.buffer.flush()
    except Exception as exc:
        text = str(exc) if isinstance(exc, Refusal) else type(exc).__name__
        sys.stderr.buffer.write(text.encode("utf-8", errors="replace")[:512])
        raise SystemExit(1)


if __name__ == "__main__":
    require(sys.argv[1:] == ["--worker"], "values_worker_only")
    _worker()
