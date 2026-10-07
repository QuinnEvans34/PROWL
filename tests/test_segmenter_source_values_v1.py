"""Generated full-sized checkpoints only; never touch a retained candidate."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
from types import MappingProxyType

import pytest
import torch

from src.models import segmenter_source_values_v1 as values
from src.models.segresnet import build_model

meta = values.meta


def stat_record(path, root=False):
    s = os.stat(path, follow_symlinks=False)
    row = dict(device=s.st_dev, inode=s.st_ino, mode=s.st_mode, owner=s.st_uid)
    if not root:
        row.update(links=s.st_nlink, mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)
    return row


def controls(path, namespace="identity"):
    c = dict(schema_version=meta.CONTROL_VERSION, evidence_domain=meta.DOMAIN,
        source=dict(root=str(path.parent), path=str(path), bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), identity=stat_record(path),
            root_identity=stat_record(path.parent, True), volume=dict(mount="invented", uuid="invented",
            filesystem="invented", device=path.stat().st_dev, fsid=[0, 0], method="invented")),
        architecture=meta.architecture(), expected_signature=meta.expected_signature(), namespace=namespace,
        wrapper="net_optimizer_scheduler_epoch", limits=meta.limits(), request=dict(run_id="invented_values_meta",
            reader_sha256=meta.reader_sha256(), consumption_receipt_sha256=hashlib.sha256(b"invented receipt").hexdigest()))
    report = meta._inspect_local(path, c, meta.control_sha256(c))
    assert report["status"] == "pass", report
    receipt = dict(schema_version="invented-values-receipt-1", run_id="invented_values", domain=values.DOMAIN, state="consumed")
    v = dict(schema_version="source-values-control-1", domain=values.DOMAIN, reader_control=c,
        metadata_report_sha256=values.digest(report), reader_sha256=values.READER_PIN, code_sha256=values.code_sha256(),
        request=dict(run_id=receipt["run_id"], consumption_receipt_sha256=values.digest(receipt)),
        limits=values.limits(path.stat().st_size))
    return v, report, receipt


def run(c, m, r, native=False, **kw):
    if native:
        return values.inspect_values(c, control_sha256=values.digest(c), metadata_report=m,
            metadata_report_sha256=values.digest(m), receipt=r, **kw)
    c, m = values.validate(c, values.digest(c), m, values.digest(m), r,
        kw.get("acceptance"), kw.get("acceptance_sha256"), kw.get("approval"), kw.get("approval_sha256"))
    return values._inspect_local(c, m)


@pytest.fixture(autouse=True)
def globals_restored():
    rng, safe = torch.get_rng_state().clone(), torch.serialization.get_safe_globals()
    yield
    torch.set_rng_state(rng)
    torch.serialization.clear_safe_globals()
    torch.serialization.add_safe_globals(safe)


@pytest.fixture(scope="module")
def fixture():
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-", dir=Path(tempfile.gettempdir()).resolve()) as area:
        path = Path(area) / "invented-generated.pth"
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(2134)
            model = build_model({"model": meta.architecture()})
        state = dict(model.state_dict())
        # Nonfinite optimizer payload is intentionally not materialized by V01-I.
        blob = dict(net=state, optimizer={"state": torch.full((64,), float("nan")), "betas": (.9, .999)},
            scheduler={"milestones": (1, (2, 3))}, epoch=2)
        torch.save(blob, path)
        c, m, r = controls(path)
        yield path, state, blob, c, m, r


@pytest.fixture(scope="module")
def audit(fixture):
    return run(*fixture[3:])


def encoded(a):
    return bytearray(struct.pack("<Q", len(a.report_json)) + a.report_json +
        b"".join(t.numpy().tobytes() for k, t in sorted(a.state.items())))


def test_full_native_selective_read_and_caller_isolation(fixture, monkeypatch):
    path, expected, blob, c, m, r = fixture
    before = path.read_bytes(), deepcopy(c), torch.get_rng_state().clone(), torch.serialization.get_safe_globals()
    monkeypatch.setattr(socket, "socket", lambda *a, **kw: pytest.fail("network used"))
    monkeypatch.setattr(torch.nn.Module, "__call__", lambda *a, **kw: pytest.fail("model forward"))
    a = run(c, m, r, native=True)
    report = values.validate_audit(a)
    assert len(a.state) == 83 and sum(t.numel() * 4 for t in a.state.values()) == 18805696
    for key, tensor in expected.items():
        assert torch.equal(a.state[key], tensor)
        assert a.state[key].data_ptr() != tensor.data_ptr()
    assert report["io"]["hash_bytes"] == path.stat().st_size
    assert report["io"]["model_value_bytes"] == 18805696
    assert report["io"]["unique_model_reads"] == 83
    assert report["io"]["metadata_storage_source_bytes"] == report["io"]["auxiliary_value_bytes"] == 0
    assert report["execution_authority"] == "none" and report["training_eligible"] is False
    assert path.read_bytes() == before[0] and c == before[1]
    assert torch.equal(torch.get_rng_state(), before[2]) and torch.serialization.get_safe_globals() == before[3]


def test_exact_read_spans_no_auxiliary_values(fixture, monkeypatch):
    c, m, r = fixture[3:]
    original, calls = values._ValueSource.value_span, []
    def read(self, start, count):
        calls.append((start, count))
        return original(self, start, count)
    monkeypatch.setattr(values._ValueSource, "value_span", read)
    a = run(c, m, r)
    assert set(calls) == {(x["storage_file_offset"], x["storage_bytes"]) for x in m["model"].values()}
    assert len(calls) == 83 and sum(n for _, n in calls) == 18805696
    assert a.report["io"]["total_requested_bytes"] <= c["limits"]["total_requested_bytes"]


@pytest.mark.parametrize("which", ["domain", "reader_domain", "candidate_hash", "candidate_path", "code_pin",
    "reader_pin", "extra_control", "limits", "run_id", "receipt", "metadata_status", "metadata_domain",
    "metadata_source", "metadata_authority", "metadata_values", "metadata_model", "metadata_pin"])
def test_refusal_before_source_open(fixture, monkeypatch, which):
    c, m, r = deepcopy(fixture[3:])
    if which == "domain": c["domain"] = "accepted_suprem_source_values"
    elif which == "reader_domain": c["reader_control"]["evidence_domain"] = meta.ACTUAL_DOMAIN
    elif which == "candidate_hash": c["reader_control"]["source"]["sha256"] = meta.ACTUAL_CANDIDATE_SHA
    elif which == "candidate_path": c["reader_control"]["source"]["path"] = str(meta.candidate_locator())
    elif which == "code_pin": c["code_sha256"] = "0" * 64
    elif which == "reader_pin": c["reader_sha256"] = "0" * 64
    elif which == "extra_control": c["permit"] = True
    elif which == "limits": c["limits"]["model_bytes"] += 1
    elif which == "run_id": c["request"]["run_id"] = "actual_values"
    elif which == "receipt": r["state"] = "pending"
    elif which == "metadata_status": m["status"] = "refused"
    elif which == "metadata_domain": m["evidence_domain"] = meta.ACTUAL_DOMAIN
    elif which == "metadata_source": m["source_sha256"] = "0" * 64
    elif which == "metadata_authority": m["execution_authority"] = "training"
    elif which == "metadata_values": m["values_audited"] = True
    elif which == "metadata_model": m["model"].pop(next(iter(m["model"])))
    elif which == "metadata_pin": c["metadata_report_sha256"] = "0" * 64
    if which.startswith("metadata_") and which != "metadata_pin": c["metadata_report_sha256"] = values.digest(m)
    monkeypatch.setattr(values.os, "open", lambda *a, **kw: pytest.fail("source opened"))
    with pytest.raises(values.Refusal): run(c, m, r, native=True)


@pytest.mark.parametrize("field", ["approval", "approval_sha256", "acceptance", "acceptance_sha256"])
def test_no_invented_approval_or_acceptance(fixture, monkeypatch, field):
    monkeypatch.setattr(values.os, "open", lambda *a, **kw: pytest.fail("source opened"))
    with pytest.raises(values.Refusal, match="invented_acceptance_or_approval_refused"):
        run(*fixture[3:], native=True, **{field: {"approved": True}})


def test_pin_mismatch_precedes_source(fixture, monkeypatch):
    c, m, r = fixture[3:]
    monkeypatch.setattr(values.os, "open", lambda *a, **kw: pytest.fail("source opened"))
    with pytest.raises(values.Refusal, match="values_control_or_metadata_pin"):
        values.inspect_values(c, control_sha256="0" * 64, metadata_report=m, metadata_report_sha256=values.digest(m), receipt=r)


@pytest.mark.parametrize("kind", ["nan_head", "inf_backbone", "larger_storage", "offset", "model_alias", "aux_alias", "uniform_module"])
def test_payload_value_or_packing_policy(fixture, kind, monkeypatch):
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-", dir=Path(tempfile.gettempdir()).resolve()) as area:
        state = dict(fixture[1]); key = "conv_final.2.conv.bias"
        if kind == "nan_head": state[key] = torch.full_like(state[key], float("nan"))
        elif kind == "inf_backbone":
            key = next(k for k in state if not k.startswith("conv_final")); state[key] = torch.full_like(state[key], float("inf"))
        elif kind in ("larger_storage", "offset"):
            n = state[key].numel(); backing = torch.zeros(n + 1); state[key] = backing[(1 if kind == "offset" else 0):][:n]
        elif kind == "model_alias":
            groups = {}
            for k, t in state.items(): groups.setdefault(tuple(t.shape), []).append(k)
            a, b = next(ks[:2] for ks in groups.values() if len(ks) >= 2); state[b] = state[a]
        namespace = "identity"
        if kind == "uniform_module": state = {"module." + k: t for k, t in state.items()}; namespace = "uniform_module"
        blob = dict(net=state, optimizer={}, scheduler={}, epoch=0)
        if kind == "aux_alias": blob["optimizer"]["state"] = state[key]
        path = Path(area) / "invented-policy.pth"; torch.save(blob, path)
        c, m, r = controls(path, namespace)
        if kind in ("larger_storage", "offset", "model_alias", "aux_alias"):
            monkeypatch.setattr(values._ValueSource, "value_span", lambda *a: pytest.fail("unqualified value read"))
        if kind == "uniform_module":
            a = run(c, m, r); assert set(a.state) == set(fixture[1])
        else:
            with pytest.raises(values.Refusal, match="values_(nonfinite|dense_packing|model_alias|auxiliary_alias)"):
                run(c, m, r)


def test_value_span_bounds_repetition_shortread_and_budget(fixture, monkeypatch):
    c = fixture[3]["reader_control"]
    with values._ValueSource(c) as source:
        start, count = 0, 4; source.selected_spans = {(start, count)}
        assert len(source.value_span(start, count)) == count
        with pytest.raises(values.Refusal, match="repeated"): source.value_span(start, count)
    with values._ValueSource(c) as source:
        source.selected_spans = {(c["source"]["bytes"], 4)}
        with pytest.raises(values.Refusal, match="bounds"): source.value_span(c["source"]["bytes"], 4)
    with values._ValueSource(c) as source:
        source.selected_spans = {(0, 4)}; source.value_bytes = values.MODEL_BYTES
        with pytest.raises(values.Refusal, match="budget"): source.value_span(0, 4)
    with values._ValueSource(c) as source:
        source.selected_spans = {(0, 4)}
        monkeypatch.setattr(values.os, "pread", lambda *a: b"x")
        with pytest.raises(values.Refusal, match="short_read"): source.value_span(0, 4)


def test_non_pickle_ipc_exact_hashes_and_owned_buffers(audit, fixture):
    raw = encoded(audit); restored = values._decode(raw, fixture[3]); values.validate_audit(restored)
    assert type(restored.report_json) is bytes
    for key, tensor in audit.state.items():
        assert torch.equal(tensor, restored.state[key]) and tensor.data_ptr() != restored.state[key].data_ptr()
    raw[-1] ^= 1
    with pytest.raises(values.Refusal, match="tensor_hash"): values._decode(raw, fixture[3])


@pytest.mark.parametrize("change", ["domain", "authority", "extra", "source", "io", "allocation", "model", "state_hash"])
def test_ipc_report_tampering(audit, fixture, change):
    report = deepcopy(audit.report)
    if change == "domain": report["domain"] = meta.ACTUAL_DOMAIN
    elif change == "authority": report["training_eligible"] = True
    elif change == "extra": report["permit"] = True
    elif change == "source": report["source_bytes"] += 1
    elif change == "io": report["io"]["auxiliary_value_bytes"] = 4
    elif change == "allocation": report["allocation"]["working_ceiling_bytes"] += 1
    elif change == "model": report["model"].pop(next(iter(report["model"])))
    elif change == "state_hash": report["state_sha256"] = "0" * 64
    header = values.canonical(report)
    raw = struct.pack("<Q", len(header)) + header + b"".join(t.numpy().tobytes() for _, t in sorted(audit.state.items()))
    with pytest.raises(values.Refusal): values._decode(raw, fixture[3])


@pytest.mark.parametrize("raw", [b"", b"abc", struct.pack("<Q", 1024**2 + 1), struct.pack("<Q", 0)])
def test_ipc_length_limits(raw, fixture):
    with pytest.raises(values.Refusal): values._decode(raw, fixture[3])


def test_typed_audit_mutation_and_mapping(audit):
    with pytest.raises(TypeError): audit.state["new"] = torch.zeros(1)
    with pytest.raises(values.Refusal): values.validate_audit(dict(state=audit.state, report=audit.report))
    with pytest.raises(values.Refusal): values.validate_audit(values.ValuesAudit(audit.state, audit.report_json, object()))
    changed = dict(audit.state); key = next(iter(changed)); changed[key] = changed[key].clone(); changed[key].view(-1)[0] += 1
    with pytest.raises(values.Refusal, match="mutated"):
        values.validate_audit(values.ValuesAudit(MappingProxyType(changed), audit.report_json, values.TOKEN))


def test_typed_signature_is_independently_checked(audit):
    changed = dict(audit.state); key = "conv_final.2.conv.bias"; changed[key] = changed[key].reshape(1, 32)
    report = audit.report; report["model"] = values.state_rows(changed); report["state_sha256"] = values.digest(report["model"])
    with pytest.raises(values.Refusal, match="mutated"):
        values.validate_audit(values.ValuesAudit(MappingProxyType(changed), values.canonical(report), values.TOKEN))


def test_noncanonical_typed_report_refused(audit):
    raw = json.dumps(audit.report, indent=2).encode()
    with pytest.raises(values.Refusal, match="encoding"):
        values.validate_audit(values.ValuesAudit(audit.state, raw, values.TOKEN))


def test_known_actual_source_hash_refused_in_typed_audit(audit):
    report = audit.report; report["source_sha256"] = meta.ACTUAL_CANDIDATE_SHA
    with pytest.raises(values.Refusal, match="actual_source_audit_refused"):
        values.validate_audit(values.ValuesAudit(audit.state, values.canonical(report), values.TOKEN))


def test_resource_monitor_refusal_precedes_worker(fixture, monkeypatch):
    monkeypatch.setattr(meta, "_sample_rss", lambda pid: values.MAX_RSS + 1)
    monkeypatch.setattr(values.subprocess, "Popen", lambda *a, **kw: pytest.fail("worker launched"))
    with pytest.raises(values.Refusal, match="rss_limit"): run(*fixture[3:], native=True)


@pytest.mark.parametrize("fault", ["timeout", "stdin_stall", "rss", "stderr", "stdout"])
def test_owned_worker_stopped_on_resource_fault(fixture, monkeypatch, fault):
    # Only substitute this new owned worker; retain actual pipes/process cleanup.
    original = values.subprocess.Popen; owned = []
    code = "import sys,time;sys.stdin.buffer.read();time.sleep(10)"
    if fault == "stdin_stall": code = "import time;time.sleep(10)"
    if fault in ("stderr", "stdout"):
        code = "import sys;sys.stdin.buffer.read();sys." + fault + ".buffer.write(b'x'*" + str(8192 if fault == "stderr" else values.MAX_IPC + 1) + ");sys." + fault + ".flush()"
    def launch(args, **kw):
        p = original([values.sys.executable, "-I", "-c", code], **kw); owned.append(p); return p
    monkeypatch.setattr(meta, "_sample_rss", lambda pid: 1 if fault != "rss" or pid == os.getpid() else values.MAX_RSS + 1)
    monkeypatch.setattr(values.subprocess, "Popen", launch)
    if fault in ("timeout", "stdin_stall"):
        ticks = iter(range(0, 10000, 500))
        monkeypatch.setattr(values.time, "monotonic", lambda: next(ticks))
    with pytest.raises(values.Refusal): run(*fixture[3:], native=True)
    assert len(owned) == 1 and owned[0].poll() is not None


def test_host_byteorder_refuses_before_source(fixture, monkeypatch):
    monkeypatch.setattr(values.sys, "byteorder", "big")
    monkeypatch.setattr(values.os, "open", lambda *a, **kw: pytest.fail("source opened"))
    with pytest.raises(values.Refusal, match="host_byteorder"): run(*fixture[3:])
