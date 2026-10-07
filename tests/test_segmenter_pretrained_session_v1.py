"""New S01 integration checks; generated source/24³ CPU inputs only."""
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch
from monai.networks.nets import SegResNet

from src.training import segmenter_pretrained_session_v1 as c
from test_segmenter_pretrained_initialization_v1 import source as _source_fixture, run as _initialize

COUNTS = dict(updates=0, forwards=0, cold_forwards=0)
LIVE_SESSION = None


@pytest.fixture(scope="module", autouse=True)
def unit_envelope():
    old_threads, old_rng = torch.get_num_threads(), torch.get_rng_state().clone()
    torch.set_num_threads(1)
    with pytest.MonkeyPatch.context() as patch:
        old_forward, old_step = SegResNet.forward, torch.optim.AdamW.step
        def forward(self, *args, **kwargs):
            COUNTS["forwards"] += 1
            assert COUNTS["forwards"] + COUNTS["cold_forwards"] <= 24
            return old_forward(self, *args, **kwargs)
        def step(self, *args, **kwargs):
            COUNTS["updates"] += 1
            assert COUNTS["updates"] <= 12
            return old_step(self, *args, **kwargs)
        patch.setattr(SegResNet, "forward", forward)
        patch.setattr(torch.optim.AdamW, "step", step)
        yield
    print("S01_UNIT_CALL_COUNTS=" + json.dumps(COUNTS, sort_keys=True))
    torch.set_rng_state(old_rng)
    torch.set_num_threads(old_threads)


@pytest.fixture(scope="module")
def audit():
    # Reuse generated fixture preparation, not any old successful test/actual file.
    generator = _source_fixture.__wrapped__()
    try:
        values_audit, _ = next(generator)
        yield _initialize(values_audit)
    finally:
        generator.close()


@pytest.fixture(scope="module")
def binding(audit):
    provider = c.inputs.InventedInputs(24)
    cfg = c.config(size=24, steps=6)
    i, controls = c.make_identity(cfg, provider, c.fixture_context(audit, cfg), audit,
                                 run_id="segmenter-pretrained-unit", device="cpu")
    return i, controls, provider


@pytest.fixture(scope="module")
def saved(binding, audit):
    global LIVE_SESSION
    identity, controls, provider = binding
    s = c.Session(identity, controls, audit)
    before = torch.get_rng_state().clone()
    s.evaluate(provider)
    s.update(provider, exact_permit=c.invented_permit(identity, "1" * 64))
    assert torch.equal(torch.get_rng_state(), before)
    LIVE_SESSION = s
    return c.payload(s), identity


def same_state(a, b):
    return c.baseline.tree_exact(c._state(a), c._state(b)) and c.progress(a) == c.progress(b)


def test_typed_initialization_fresh_optimizer_no_alias_rng(binding, audit):
    i, files, _ = binding
    before = torch.get_rng_state().clone(), audit.report_json
    s = c.Session(i, files, audit)
    assert s.step == 0 and not s.dirty and s.optimizer.state_dict()["state"] == {}
    assert c.initializer.values.state_rows(dict(s.model.state_dict())) == audit.report["model"]
    for name, tensor in s.model.state_dict().items():
        assert tensor.data_ptr() != audit.state[name].data_ptr()
    assert torch.equal(before[0], torch.get_rng_state()) and audit.report_json == before[1]
    assert c.numerical.state_hash(s.model.state_dict()) != c.baseline.INITIAL
    with pytest.raises(ValueError):
        s.import_weights({"prior": "anything"})


def test_same_six_member_sampler_recipe_and_report_only(binding):
    i, _, provider = binding
    cfg = i["config"]
    assert c._recipe(cfg) == c.baseline.config(size=24, steps=6)
    sequence = [c.next_member(cfg, provider.control, step) for step in range(6)]
    assert sequence == [c.baseline.next_member(c._recipe(cfg), provider.control, step) for step in range(6)]
    assert set(name for name, _ in sequence) == set(provider.control["train"])
    assert "invented-validation" not in {name for name, _ in sequence}
    assert c.config()["max_steps"] == 48 and cfg["primary_checkpoint"] == "terminal"


@pytest.mark.parametrize("fault", ["domain", "task", "run", "config", "pin"])
def test_identity_changes_refused_before_allocation(binding, monkeypatch, fault):
    i, files, _ = deepcopy(binding[:2]) + (binding[2],)
    if fault == "domain": i["domain"] = "qualified_real_cache"
    if fault == "task": i["task"] = c.baseline.TASK
    if fault == "run": i["run_id"] = "segmenter-v5-training-unit"
    if fault == "config": i["config"]["primary_checkpoint"] = "best_validation"
    if fault == "pin": i["initialization_sha256"] = "0" * 64
    monkeypatch.setattr(c, "_fresh", lambda *a: pytest.fail("model allocated"))
    with pytest.raises(ValueError):
        c.validate_controls(i, files)


@pytest.mark.parametrize("fault", ["actual", "actual_sha", "accepted", "teacher", "geometry",
                                    "environment", "extra", "noncanonical", "boolean_seed"])
def test_rehashed_control_substitutions_refuse(binding, monkeypatch, fault):
    i, files = deepcopy(binding[:2])
    name = "initialization.json"
    obj = json.loads(files[name])
    if fault == "actual": obj["domain"] = "accepted_suprem_source_values"
    if fault == "actual_sha": obj["source_sha256"] = c.initializer.values.meta.ACTUAL_CANDIDATE_SHA
    if fault == "boolean_seed": obj["seed"] = True
    if fault == "accepted": name = "acceptance.json"; obj = json.loads(files[name]); obj["training_eligible"] = True
    if fault == "teacher": name = "lineage.json"; obj = json.loads(files[name]); obj["teacher_models"] = ["old-model"]
    if fault == "geometry": name = "geometry.json"; obj = json.loads(files[name]); obj["roi_source"] = "reference"
    if fault == "environment": name = "environment.json"; obj = json.loads(files[name]); obj["torch"] = "changed"
    if fault == "extra": name = "source.json"; obj = json.loads(files[name]); obj["permit"] = True
    files[name] = json.dumps(obj, indent=2).encode() if fault == "noncanonical" else c.canonical(obj)
    i[c.CONTROLS[name]] = c.digest(files[name])
    monkeypatch.setattr(c, "_fresh", lambda *a: pytest.fail("model allocated"))
    with pytest.raises(ValueError):
        c.validate_controls(i, files)


def test_changed_dependency_refused(binding, monkeypatch):
    i, files, _ = binding
    changed = dict(c.PINS)
    changed["src/models/segresnet.py"] = "0" * 64
    monkeypatch.setattr(c, "PINS", changed)
    with pytest.raises(ValueError): c.validate_controls(i, files)


def test_untyped_audit_and_actual_provider_refuse_before_allocation(binding, audit, monkeypatch):
    i, files, provider = binding
    monkeypatch.setattr(c, "_fresh", lambda *a: pytest.fail("model allocated"))
    with pytest.raises(ValueError): c.Session(i, files, audit.report)
    with pytest.raises(ValueError):
        c.make_identity(i["config"], object(), {n: files[n] for n in c.CONTEXT}, audit,
                        run_id=i["run_id"], device="cpu")
    with pytest.raises(ValueError): c.invented_permit(i, "not-a-request")


def test_actual_relabelled_typed_audit_refused(binding, audit, monkeypatch):
    report = audit.report
    report["source_sha256"] = c.initializer.values.meta.ACTUAL_CANDIDATE_SHA
    forged = c.initializer.InitializationAudit(audit.state, c.canonical(report), c.initializer.TOKEN)
    monkeypatch.setattr(c, "_fresh", lambda *a: pytest.fail("model allocated"))
    with pytest.raises(ValueError): c.Session(binding[0], binding[1], forged)


def test_permit_and_raw_input_refuse_before_observation(saved, binding, monkeypatch):
    files, identity = saved
    s = c.restore_payload(files, identity)
    provider = binding[2]
    monkeypatch.setattr(provider, "get", lambda *a, **k: pytest.fail("input observed"))
    for permit in (None, c.InventedPermit("0" * 64, "1" * 64, c._TOKEN),
                   c.InventedPermit(c.digest(c.canonical(identity)), "1" * 64, object())):
        with pytest.raises(ValueError): s.update(provider, exact_permit=permit)
    with pytest.raises(ValueError): s.update((np.zeros(1), np.zeros(1)), exact_permit=c.invented_permit(identity, "1" * 64))
    assert s.step == 1 and not s.dirty


def test_unsealed_evaluator_or_changed_batch_cannot_optimize(saved, binding, monkeypatch):
    files, identity = saved
    s = c.restore_payload(files, identity)
    provider = binding[2]
    expected, _ = c.next_member(s.config, s.control, s.step)
    batch = provider.get(expected, role="train", operation="evaluator")
    monkeypatch.setattr(provider, "get", lambda *a, **k: batch)
    with pytest.raises(ValueError): s.update(provider, exact_permit=c.invented_permit(identity, "1" * 64))
    batch.operation = "optimizer"
    batch.control_sha256 = "0" * 64
    with pytest.raises(ValueError): s.update(provider, exact_permit=c.invented_permit(identity, "1" * 64))
    assert not s.dirty and s.step == 1


def test_exact_restore_next_update_and_predictions(saved, binding):
    files, identity = saved
    # Live, uninterrupted state is the oracle; do not compare two identical decoders.
    a, b = LIVE_SESSION, c.restore_payload(files, identity)
    assert same_state(a, b)
    before = torch.get_rng_state().clone()
    permit = c.invented_permit(identity, "1" * 64)
    assert a.update(binding[2], exact_permit=permit) == b.update(binding[2], exact_permit=permit)
    assert same_state(a, b)
    image = binding[2].get("invented-validation", role="validation", operation="inference").image
    assert np.array_equal(a.predict(image), b.predict(image))
    assert torch.equal(before, torch.get_rng_state())
    assert c.progress(a)["exposure"] == {n: sum(r["member_id"] == n for r in a.history) for n in a.control["train"]}


def test_mutation_fault_dirty_and_last_complete_retained(saved, binding, monkeypatch):
    files, identity = saved
    s = c.restore_payload(files, identity)
    old = s.optimizer.step
    def fault():
        old()
        raise RuntimeError("after_optimizer_mutation")
    monkeypatch.setattr(s.optimizer, "step", fault)
    with pytest.raises(RuntimeError, match="after_optimizer_mutation"):
        s.update(binding[2], exact_permit=c.invented_permit(identity, "1" * 64))
    assert s.dirty and s.step == 1
    image = binding[2].get("invented-validation", role="validation", operation="inference").image
    for action in (lambda: c.payload(s), lambda: s.predict(image), lambda: s.evaluate(binding[2]),
                   lambda: s.update(binding[2], exact_permit=c.invented_permit(identity, "1" * 64))):
        with pytest.raises(ValueError): action()
    recovered = c.restore_payload(files, identity)
    assert recovered.step == 1 and not recovered.dirty


@pytest.mark.parametrize("fault", ["nonfinite", "accounting"])
def test_failed_commit_keeps_last_committed_step(saved, binding, monkeypatch, fault):
    files, identity = saved
    s = c.restore_payload(files, identity)
    before = deepcopy(s.history)
    if fault == "nonfinite":
        old = s.optimizer.step
        def broken():
            old()
            with torch.no_grad(): next(s.model.parameters()).view(-1)[0] = float("nan")
        monkeypatch.setattr(s.optimizer, "step", broken)
    else:
        def reject(*a): raise ValueError("prospective accounting failure")
        monkeypatch.setattr(c, "validate_progress", reject)
    with pytest.raises(ValueError):
        s.update(binding[2], exact_permit=c.invented_permit(identity, "1" * 64))
    assert s.dirty and s.step == 1 and s.history == before
    with pytest.raises(ValueError): c.payload(s)


@pytest.mark.parametrize("fault", ["step", "cursor", "exposure", "member", "rate", "metric", "aggregate",
                                    "head", "nan", "optimizer_step", "moment_dtype", "moment_missing",
                                    "optimizer_policy", "rng", "extra", "state_schema", "identity"])
def test_complete_checkpoint_corruption_refuses(saved, fault):
    files, identity = deepcopy(saved)
    if fault in ("step", "cursor", "exposure", "member", "rate", "metric", "aggregate"):
        p = json.loads(files["progress.json"])
        if fault == "step": p["step"] += 1
        if fault == "cursor": p["sampler"]["cursor"] += 1
        if fault == "exposure": p["exposure"]["invented-train-0"] = True
        if fault == "member": p["history"][0]["member_id"] = "invented-validation"
        if fault == "rate": p["history"][0]["learning_rate"] = .003
        if fault == "metric": p["evaluations"][0]["cases"][0]["metrics"]["lesion"]["dice"] = .999
        if fault == "aggregate": p["evaluations"][0]["aggregate"]["train"]["cases"] += 1
        files["progress.json"] = c.canonical(p)
    elif fault == "extra": files["extra.bin"] = b"x"
    elif fault == "identity": identity["run_id"] += "-other"
    else:
        state = torch.load(BytesIO(files["state.pt"]), weights_only=True)
        head = "conv_final.2.conv.weight"
        if fault == "head": state["model"][head] = state["model"][head][:2]
        if fault == "nan": state["model"][head][0, 0, 0, 0, 0] = float("nan")
        if fault == "optimizer_step": state["optimizer"]["state"][0]["step"] += 1
        if fault == "moment_dtype": state["optimizer"]["state"][0]["exp_avg"] = state["optimizer"]["state"][0]["exp_avg"].double()
        if fault == "moment_missing": del state["optimizer"]["state"][0]["exp_avg_sq"]
        if fault == "optimizer_policy": state["optimizer"]["param_groups"][0]["lr"] = .003
        if fault == "rng": state["cpu_rng"] = torch.zeros(1)
        if fault == "state_schema": state["schema_version"] = "segmenter-v5-training-state-1"
        stream = BytesIO(); torch.save(state, stream); files["state.pt"] = stream.getvalue()
    with pytest.raises((ValueError, KeyError, RuntimeError)):
        c.validate_payload(files, identity)


def test_step0_requires_exact_initial_state(binding, audit):
    s = c.Session(binding[0], binding[1], audit)
    files = c.payload(s)
    state = torch.load(BytesIO(files["state.pt"]), weights_only=True)
    state["model"]["conv_final.2.conv.bias"][0] += .001
    stream = BytesIO(); torch.save(state, stream); files["state.pt"] = stream.getvalue()
    with pytest.raises(ValueError): c.restore_payload(files, binding[0])


def test_duplicate_evaluation_budget_and_changed_provider_refuse(saved, binding):
    files, identity = saved
    s = c.restore_payload(files, identity)
    s.evaluations[-1]["step"] = s.step
    with pytest.raises(ValueError): s.evaluate(binding[2])
    s.step = s.config["max_steps"]
    with pytest.raises(ValueError): s.update(binding[2], exact_permit=c.invented_permit(identity, "1" * 64))
    changed = c.inputs.InventedInputs(24)
    changed.control["domain"] = "qualified_real_cache"
    with pytest.raises(ValueError): s.evaluate(changed)


def test_payload_bounds_before_torch_decode(saved, monkeypatch):
    files, identity = saved
    monkeypatch.setattr(torch, "load", lambda *a, **k: pytest.fail("decoded oversized bytes"))
    corrupt = dict(files, **{"state.pt": b"x" * (64 * 1024**2 + 1)})
    with pytest.raises(ValueError): c.decode(corrupt, identity)
    corrupt = dict(files, **{"progress.json": b"x" * (4 * 1024**2 + 1)})
    with pytest.raises(ValueError): c.decode(corrupt, identity)


def test_fresh_process_complete_restore_predictions(saved, binding, tmp_path):
    files, identity = saved
    for name, raw in files.items(): (tmp_path / name).write_bytes(raw)
    script = """
import json, sys
from pathlib import Path
import torch
from src.training import segmenter_pretrained_session_v1 as c
torch.set_num_threads(1)
p=Path(sys.argv[1]); files={x.name:x.read_bytes() for x in p.iterdir()}
i=json.loads(files['identity.json']);s=c.restore_payload(files,i)
provider=c.inputs.InventedInputs(24)
image=provider.get('invented-validation',role='validation',operation='inference').image
prediction=s.predict(image)
def fingerprint(x):
    if isinstance(x,torch.Tensor):
        return dict(shape=list(x.shape),dtype=str(x.dtype),sha256=c.digest(x.numpy().tobytes()))
    if isinstance(x,dict): return {str(k):fingerprint(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [fingerprint(v) for v in x]
    return x
print(json.dumps(dict(step=s.step,model=c.numerical.state_hash(s.model.state_dict()),
    state=c.digest(c.canonical(fingerprint(c._state(s)))),
    progress=c.digest(c.canonical(c.progress(s))),prediction=c.digest(prediction.tobytes()),forwards=1)))
"""
    response = subprocess.run([sys.executable, "-c", script, str(tmp_path)], cwd=c.ROOT,
        env={**os.environ, "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
        capture_output=True, text=True, timeout=30, check=True)
    result = json.loads(response.stdout.strip())
    s = c.restore_payload(files, identity)
    image = binding[2].get("invented-validation", role="validation", operation="inference").image
    def fingerprint(x):
        if isinstance(x, torch.Tensor):
            return dict(shape=list(x.shape), dtype=str(x.dtype), sha256=c.digest(x.numpy().tobytes()))
        if isinstance(x, dict): return {str(k): fingerprint(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)): return [fingerprint(v) for v in x]
        return x
    raw = torch.load(BytesIO(files["state.pt"]), weights_only=True, map_location="cpu")
    assert result == dict(step=1, model=c.numerical.state_hash(s.model.state_dict()),
        state=c.digest(c.canonical(fingerprint(raw))), progress=c.digest(c.canonical(c.progress(s))),
        prediction=c.digest(s.predict(image).tobytes()), forwards=1)
    COUNTS["cold_forwards"] += result["forwards"]
    assert COUNTS["forwards"] + COUNTS["cold_forwards"] <= 24
