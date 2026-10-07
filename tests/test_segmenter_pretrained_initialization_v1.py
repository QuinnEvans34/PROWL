"""Typed generated-value integration; no actual source or model execution."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import MappingProxyType

import pytest
import torch

from src.models import segmenter_pretrained_initialization_v1 as init
from src.models import segresnet

values, meta = init.values, init.values.meta


def stat_record(path, root=False):
    s = path.stat()
    r = dict(device=s.st_dev, inode=s.st_ino, mode=s.st_mode, owner=s.st_uid)
    if not root: r.update(links=s.st_nlink, mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)
    return r


def control(a):
    return dict(schema_version="pretrained-initialization-control-1", domain=init.DOMAIN,
        values_report_sha256=values.digest(a.report), values_code_sha256=init.VALUES_PIN,
        initializer_sha256=init.code_sha256(), factory_sha256=init.FACTORY_PIN,
        target_architecture=init.architecture(), seed=42, policy=init.POLICY, limits=init.limits())


def run(a, c=None):
    c = control(a) if c is None else c
    return init.initialize(a, c, control_sha256=values.digest(c))


@pytest.fixture(autouse=True)
def restored():
    rng, safe = torch.get_rng_state().clone(), torch.serialization.get_safe_globals()
    yield
    torch.set_rng_state(rng); torch.serialization.clear_safe_globals(); torch.serialization.add_safe_globals(safe)


@pytest.fixture(scope="module")
def source():
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-", dir=Path(tempfile.gettempdir()).resolve()) as area:
        path = Path(area) / "invented-initialization.pth"
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(711)
            model = segresnet.build_model({"model": meta.architecture()})
        expected = {k: v.detach().clone() for k, v in model.state_dict().items()}
        torch.save(dict(net={"module." + k: v for k, v in expected.items()}, optimizer={}, scheduler={}, epoch=0), path)
        rc = dict(schema_version=meta.CONTROL_VERSION, evidence_domain=meta.DOMAIN,
            source=dict(root=str(path.parent), path=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), identity=stat_record(path),
                root_identity=stat_record(path.parent, True), volume=dict(mount="invented", uuid="invented",
                filesystem="invented", device=path.stat().st_dev, fsid=[0, 0], method="invented")),
            architecture=meta.architecture(), expected_signature=meta.expected_signature(), namespace="uniform_module",
            wrapper="net_optimizer_scheduler_epoch", limits=meta.limits(), request=dict(run_id="invented_init_meta",
                reader_sha256=meta.reader_sha256(), consumption_receipt_sha256=hashlib.sha256(b"invented receipt").hexdigest()))
        report = meta._inspect_local(path, rc, meta.control_sha256(rc)); assert report["status"] == "pass", report
        receipt = dict(schema_version="invented-values-receipt-1", run_id="invented_init_values", domain=values.DOMAIN, state="consumed")
        vc = dict(schema_version="source-values-control-1", domain=values.DOMAIN, reader_control=rc,
            metadata_report_sha256=values.digest(report), reader_sha256=values.READER_PIN, code_sha256=values.code_sha256(),
            request=dict(run_id=receipt["run_id"], consumption_receipt_sha256=values.digest(receipt)), limits=values.limits(path.stat().st_size))
        a = values.inspect_values(vc, control_sha256=values.digest(vc), metadata_report=report,
            metadata_report_sha256=values.digest(report), receipt=receipt)
        yield a, expected


@pytest.fixture(scope="module")
def initialized(source):
    return run(source[0])


def test_independent_factory_signature_and_bytes(source):
    a, expected = source
    assert len(expected) == 83 and sum(t.numel() * 4 for t in expected.values()) == 18805696
    assert {k: dict(shape=list(t.shape), dtype=str(t.dtype)) for k, t in expected.items()} == meta.expected_signature()
    with torch.random.fork_rng(devices=[]):
        fresh = segresnet.build_model({"model": init.architecture()}).state_dict()
    assert init.signature() == {k: dict(shape=list(t.shape), dtype=str(t.dtype)) for k, t in fresh.items()}
    assert sum(t.numel() * 4 for t in fresh.values()) == 18803724


def test_exact_full_transfer_fresh_head_rng_and_owned_state(source, monkeypatch):
    a, expected = source; before = values.state_rows(a.state), a.report_json, torch.get_rng_state().clone()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(42); fresh = segresnet.build_model({"model": init.architecture()}).state_dict()
        head = {k: fresh[k].clone() for k in init.HEAD_KEYS}
    monkeypatch.setattr(torch.nn.Module, "__call__", lambda *a, **kw: pytest.fail("model forward"))
    result = run(a); r = init.validate_initialization(result)
    assert len(result.state) == 83
    for key, tensor in result.state.items():
        assert torch.equal(tensor, head[key] if key in init.HEAD_KEYS else expected[key]), key
        assert tensor.untyped_storage().data_ptr() != a.state[key].untyped_storage().data_ptr()
    assert torch.equal(result.state["conv_final.0.weight"], expected["conv_final.0.weight"])
    assert values.state_rows(a.state) == before[0] and a.report_json == before[1]
    assert torch.equal(torch.get_rng_state(), before[2])
    assert r["bytes"] == dict(source=18805696, source_head=2176, backbone=18803520, fresh_head=204, target=18803724)
    assert r["execution_authority"] == "none" and not r["training_eligible"]


def test_one_strict_load_complete_candidate(source, monkeypatch):
    original, calls = torch.nn.Module.load_state_dict, []
    def load(self, state, strict=True, **kw):
        calls.append((set(state), strict))
        return original(self, state, strict=strict, **kw)
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", load)
    run(source[0]); assert calls == [(set(init.signature()), True)]


@pytest.mark.parametrize("which", ["domain", "version", "policy", "seed", "seed_bool", "architecture",
    "extra", "limit", "values_pin", "initializer_pin", "factory_pin", "report_pin", "architecture_bool"])
def test_control_refuses_before_factory(source, monkeypatch, which):
    a = source[0]; c = control(a)
    if which == "domain": c["domain"] = "accepted_pretrained_source"
    elif which == "version": c["schema_version"] = "unknown"
    elif which == "policy": c["policy"] = "copy_head"
    elif which == "seed": c["seed"] = 43
    elif which == "seed_bool": c["seed"] = True
    elif which == "architecture": c["target_architecture"]["out_channels"] = 32
    elif which == "extra": c["approved"] = True
    elif which == "limit": c["limits"]["working_bytes"] += 1
    elif which == "values_pin": c["values_code_sha256"] = "0" * 64
    elif which == "initializer_pin": c["initializer_sha256"] = "0" * 64
    elif which == "factory_pin": c["factory_sha256"] = "0" * 64
    elif which == "report_pin": c["values_report_sha256"] = "0" * 64
    elif which == "architecture_bool": c["target_architecture"]["in_channels"] = True
    monkeypatch.setattr(segresnet, "build_model", lambda *a: pytest.fail("factory used"))
    with pytest.raises(values.Refusal): run(a, c)


def test_control_pin_mismatch_before_factory(source, monkeypatch):
    monkeypatch.setattr(segresnet, "build_model", lambda *a: pytest.fail("factory used"))
    with pytest.raises(values.Refusal, match="control_pin"):
        init.initialize(source[0], control(source[0]), control_sha256="0" * 64)


@pytest.mark.parametrize("ambient", ["device", "dtype"])
def test_ambient_defaults_refuse_before_factory(source, monkeypatch, ambient):
    if ambient == "device": monkeypatch.setattr(torch, "get_default_device", lambda: torch.device("meta"))
    else: monkeypatch.setattr(torch, "get_default_dtype", lambda: torch.float64)
    monkeypatch.setattr(segresnet, "build_model", lambda *a: pytest.fail("factory used"))
    with pytest.raises(values.Refusal, match="ambient_tensor_defaults"): run(source[0])


@pytest.mark.parametrize("kind", ["mapping", "token", "mutated", "nonfinite", "actual_report", "shape", "alias"])
def test_bad_typed_source_rejected_before_factory(source, monkeypatch, kind):
    a = source[0]; state, report, token = dict(a.state), a.report, values.TOKEN
    if kind == "mapping": bad = {"state": a.state, "report": a.report}
    else:
        key = "conv_final.2.conv.bias"
        if kind == "token": token = object()
        elif kind == "mutated": state[key] = state[key].clone() + 1
        elif kind == "nonfinite": state[key] = torch.full_like(state[key], float("nan"))
        elif kind == "actual_report": report["domain"] = "accepted_suprem_source_values"
        elif kind == "shape": state[key] = state[key].reshape(1, 32)
        elif kind == "alias":
            groups = {}
            for k, t in state.items(): groups.setdefault(tuple(t.shape), []).append(k)
            x, y = next(ks[:2] for ks in groups.values() if len(ks) > 1); state[y] = state[x]
        bad = values.ValuesAudit(MappingProxyType(state), values.canonical(report), token)
    c = control(a)
    monkeypatch.setattr(segresnet, "build_model", lambda *a: pytest.fail("factory used"))
    with pytest.raises(values.Refusal): run(bad, c)


def test_constructor_failure_preserves_rng(source, monkeypatch):
    before = torch.get_rng_state().clone()
    def fail(*a): torch.rand(7); raise RuntimeError("invented constructor fault")
    monkeypatch.setattr(segresnet, "build_model", fail)
    with pytest.raises(RuntimeError, match="constructor fault"): run(source[0])
    assert torch.equal(before, torch.get_rng_state())


def test_wrong_factory_shape_before_strict_load(source, monkeypatch):
    original = segresnet.build_model
    def wrong(config):
        c = deepcopy(config); c["model"]["out_channels"] = 4; return original(c)
    monkeypatch.setattr(segresnet, "build_model", wrong)
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", lambda *a, **kw: pytest.fail("unqualified strict load"))
    with pytest.raises(values.Refusal, match="factory_signature"): run(source[0])


def test_strict_load_wrong_result_and_failed_transfer_refused(source, monkeypatch):
    from torch.nn.modules.module import _IncompatibleKeys
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", lambda *a, **kw: _IncompatibleKeys([], ["extra"]))
    with pytest.raises(values.Refusal, match="strict_load"): run(source[0])
    monkeypatch.setattr(torch.nn.Module, "load_state_dict", lambda *a, **kw: _IncompatibleKeys([], []))
    with pytest.raises(values.Refusal, match="transfer_mismatch"): run(source[0])


def test_repeat_initialization_exact_without_shared_storage(source, initialized):
    second = run(source[0])
    assert second.report_json == initialized.report_json
    for key, t in second.state.items():
        assert torch.equal(t, initialized.state[key]) and t.data_ptr() != initialized.state[key].data_ptr()


def test_readonly_mapping_and_mutated_output_refused(initialized):
    with pytest.raises(TypeError): initialized.state["new"] = torch.zeros(1)
    with pytest.raises(values.Refusal): init.validate_initialization(dict(state=initialized.state, report=initialized.report))
    changed = dict(initialized.state); k = init.HEAD_KEYS[0]; changed[k] = changed[k].clone() + 1
    with pytest.raises(values.Refusal, match="mutated"):
        init.validate_initialization(init.InitializationAudit(MappingProxyType(changed), initialized.report_json, init.TOKEN))


@pytest.mark.parametrize("field", ["domain", "training_eligible", "policy", "excluded_keys", "fresh_head_sha256",
    "source_backbone_sha256", "target_state_sha256", "bytes", "model", "extra", "source_sha256"])
def test_output_report_tampering_refused(initialized, field):
    r = initialized.report
    if field == "domain": r[field] = "actual"
    elif field == "training_eligible": r[field] = True
    elif field == "policy": r[field] = "copy_head"
    elif field == "excluded_keys": r[field] = []
    elif field in ("fresh_head_sha256", "source_backbone_sha256", "target_state_sha256"): r[field] = "0" * 64
    elif field == "bytes": r[field]["target"] += 1
    elif field == "model": r[field].pop(next(iter(r[field])))
    elif field == "extra": r["permit"] = True
    elif field == "source_sha256": r[field] = meta.ACTUAL_CANDIDATE_SHA
    with pytest.raises(values.Refusal):
        init.validate_initialization(init.InitializationAudit(initialized.state, values.canonical(r), init.TOKEN))


def test_noncanonical_or_wrong_token_output_refused(initialized):
    with pytest.raises(values.Refusal):
        init.validate_initialization(init.InitializationAudit(initialized.state, initialized.report_json, object()))
    with pytest.raises(values.Refusal, match="encoding"):
        init.validate_initialization(init.InitializationAudit(initialized.state, json.dumps(initialized.report).encode(), init.TOKEN))
