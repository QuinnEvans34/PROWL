"""SUP-01 invented CPU state only: no forwards, updates, files or real weights."""
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import socket

import pytest
import torch

from src.models import segmenter_initialization_audit_v1 as audit
from src.models.segresnet import build_model


def invented_hash(label):
    return hashlib.sha256(("invented:" + label).encode()).hexdigest()


def reference(label):
    return dict(reference="invented:" + label, sha256=invented_hash(label))


def controls(source, fresh, namespace="identity"):
    observed = audit.describe_state(source)
    destination = audit.describe_state(fresh)
    file = dict(uri="invented/source.pth", sha256=invented_hash("source-file"), bytes=4096)
    candidate = dict(
        schema_version="segmenter-initialization-candidate-1", evidence_domain=audit.DOMAIN,
        classification="licensed_third_party_general_pretraining", file=file,
        source=dict(repository="invented:repository", artifact="invented:artifact",
                    revision="invented-revision-1", citation="Invented source for tests",
                    retrieval=reference("retrieval")),
        rights=dict(status="permitted", code=reference("code-license"),
                    checkpoint=reference("checkpoint-license"), data=reference("data-terms")),
        overlap=dict(status="reviewed_separate", evidence=reference("overlap-review")),
        architecture=audit.architecture(32), state_signature=observed["signature"],
        state_sha256=observed["sha256"],
    )
    policy = dict(
        schema_version="segmenter-initialization-policy-1", evidence_domain=audit.DOMAIN,
        architecture=audit.architecture(), seed=42, head_keys=list(audit.HEAD_KEYS),
        namespace=namespace, candidate_file=deepcopy(file), limits=audit.limits(),
        fresh_state_signature=destination["signature"], fresh_state_sha256=destination["sha256"],
    )
    inventory = dict(schema_version="segmenter-initialization-inventory-1",
                     evidence_domain=audit.DOMAIN, files=[dict(
                         **file, category="third_party_weights_not_approved_for_this_run",
                         weight_import_allowed=False)])
    return dict(candidate_manifest=candidate, policy=policy, historical_inventory=inventory,
                expected_candidate_sha256=audit.control_sha256(candidate),
                expected_policy_sha256=audit.control_sha256(policy),
                expected_inventory_sha256=audit.control_sha256(inventory))


def repin(kwargs):
    for field, pin in (("candidate_manifest", "expected_candidate_sha256"),
                       ("policy", "expected_policy_sha256"),
                       ("historical_inventory", "expected_inventory_sha256")):
        kwargs[pin] = audit.control_sha256(kwargs[field])


@pytest.fixture(autouse=True, scope="module")
def cpu_thread_budget():
    old = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(old)


@pytest.fixture
def small():
    source = {"encoder.weight": torch.full((2, 2), 7.),
              "conv_final.0.weight": torch.full((16,), 9.),
              "conv_final.0.bias": torch.full((16,), 11.),
              audit.HEAD_KEYS[0]: torch.full((32,), 99.),
              audit.HEAD_KEYS[1]: torch.full((32, 16, 1, 1, 1), 99.)}
    fresh = {"encoder.weight": torch.full((2, 2), .25),
             "conv_final.0.weight": torch.ones(16), "conv_final.0.bias": torch.zeros(16),
             audit.HEAD_KEYS[0]: torch.tensor([.1, .2, .3]),
             audit.HEAD_KEYS[1]: torch.full((3, 16, 1, 1, 1), .5)}
    return source, fresh, controls(source, fresh)


@pytest.fixture(scope="module")
def complete():
    # Construct two fresh networks, never run them. Forking preserves the caller RNG.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(777)
        source_model = build_model(dict(model=audit.architecture(32)))
        torch.manual_seed(42)
        destination = build_model(dict(model=audit.architecture()))
    source = {k: torch.full_like(v, (n + 1) / 1000)
              for n, (k, v) in enumerate(source_model.state_dict().items())}
    fresh = destination.state_dict()
    return source, fresh, controls(source, fresh)


def assert_unchanged(before, after):
    assert list(before) == list(after)
    for k in before:
        assert torch.equal(before[k], after[k]), k


def refused(source, fresh, kwargs, reason=None, monkeypatch=None):
    before_source = {k: v.detach().clone() for k, v in source.items()
                     if type(v) is torch.Tensor and v.device.type == "cpu" and
                     v.layout == torch.strided and v.numel() < 10000 and not v.is_quantized}
    before_fresh = {k: v.clone() for k, v in fresh.items()}
    before_controls = deepcopy(kwargs)
    rng = torch.get_rng_state().clone()
    if monkeypatch:
        monkeypatch.setattr(torch.Tensor, "clone", lambda *a, **k: pytest.fail("Cloned before refusal"))
    result, report = audit.prepare_initialization(source, fresh, **kwargs)
    assert result is None and report["status"] == "refused"
    assert report["execution_authority"] == "none" and report["initialized_state_sha256"] is None
    assert not report["loaded_keys"] and not report["replaced_keys"]
    if reason:
        assert report["reason"] == reason
    for k, v in before_source.items():
        # Nonfinite-value fixtures need an equal-NaN comparison.
        assert torch.allclose(v, source[k], rtol=0, atol=0, equal_nan=True), k
    assert_unchanged(before_fresh, fresh)
    assert kwargs == before_controls and torch.equal(rng, torch.get_rng_state())
    json.dumps(report, allow_nan=False)
    return report


def test_complete_factory_transfer_and_exact_fresh_head(complete):
    source, fresh, kwargs = complete
    assert audit.describe_state(fresh)["sha256"] == "3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add"
    before = audit.describe_state(source), audit.describe_state(fresh), deepcopy(kwargs)
    rng = torch.get_rng_state().clone()
    result, report = audit.prepare_initialization(source, fresh, **kwargs)
    assert report["status"] == "pass" and report["execution_authority"] == "none"
    assert set(result) == set(fresh) and report["replaced_keys"] == list(audit.HEAD_KEYS)
    assert report["loaded_keys"] == sorted(set(fresh) - set(audit.HEAD_KEYS))
    for k, value in result.items():
        assert torch.equal(value, fresh[k] if k in audit.HEAD_KEYS else source[k]), k
        assert value.data_ptr() != (fresh[k] if k in audit.HEAD_KEYS else source[k]).data_ptr()
        assert not value.requires_grad
    assert torch.equal(result["conv_final.0.weight"], source["conv_final.0.weight"])
    assert report["head_before_sha256"] == report["head_after_sha256"]
    with torch.random.fork_rng(devices=[]):
        model = build_model(dict(model=audit.architecture()))
    incompatible = model.load_state_dict(result, strict=True)
    assert not incompatible.missing_keys and not incompatible.unexpected_keys
    assert audit.describe_state(model.state_dict())["sha256"] == report["initialized_state_sha256"]
    assert before == (audit.describe_state(source), audit.describe_state(fresh), kwargs)
    assert torch.equal(rng, torch.get_rng_state())
    assert json.loads(json.dumps(report)) == report


def test_repeat_order_independence_and_returned_state_isolation(small):
    source, fresh, kwargs = small
    first, a = audit.prepare_initialization(source, fresh, **kwargs)
    reverse = OrderedDict(reversed(list(source.items())))
    again, b = audit.prepare_initialization(reverse, OrderedDict(reversed(list(fresh.items()))), **kwargs)
    assert a == b and audit.describe_state(first) == audit.describe_state(again)
    first["encoder.weight"].zero_()
    first[audit.HEAD_KEYS[0]].zero_()
    assert source["encoder.weight"].min().item() == 7
    assert fresh[audit.HEAD_KEYS[0]][0].item() == pytest.approx(.1)


def test_declared_uniform_module_prefix(small):
    source, fresh, _ = small
    source = {"module." + k: v for k, v in source.items()}
    kwargs = controls(source, fresh, "uniform_module")
    result, report = audit.prepare_initialization(source, fresh, **kwargs)
    assert report["status"] == "pass"
    assert torch.equal(result["encoder.weight"], source["module.encoder.weight"])
    assert set(report["source_signature"]) == set(source)
    assert set(report["normalized_source_signature"]) == set(fresh)


@pytest.mark.parametrize("fault", ["missing", "extra", "shape", "head_missing", "head_shape",
                                  "fresh_head_shape", "normalization_missing"])
def test_complete_inventory_required_before_any_clone(small, fault, monkeypatch):
    source, fresh, kwargs = small
    key = "encoder.weight"
    if fault == "missing":
        source.pop(key)
    elif fault == "extra":
        source["unknown.weight"] = torch.ones(1)
    elif fault == "shape":
        source[key] = torch.ones(3, 2)
    elif fault == "head_missing":
        source.pop(audit.HEAD_KEYS[0])
    elif fault == "head_shape":
        source[audit.HEAD_KEYS[1]] = torch.ones(3, 16, 1, 1, 1)
    elif fault == "fresh_head_shape":
        fresh[audit.HEAD_KEYS[0]] = torch.ones(4)
    else:
        source.pop("conv_final.0.weight")
    report = refused(source, fresh, kwargs, monkeypatch=monkeypatch)
    if fault in ("missing", "extra", "head_missing", "normalization_missing"):
        assert report["missing_keys"] or report["unexpected_keys"]
    else:
        assert report["mismatched_keys"] or report["reason"] == "destination_head_shape_mismatch"


@pytest.mark.parametrize("fault", ["dtype", "nan", "inf", "non_tensor", "sparse", "meta",
                                  "noncontiguous", "rank", "empty", "quantized", "negative_view"])
def test_unsupported_tensors_refused(small, fault):
    source, fresh, kwargs = small
    k = "encoder.weight"
    if fault == "dtype":
        source[k] = source[k].double()
    elif fault in ("nan", "inf"):
        source[k][0, 0] = float(fault)
    elif fault == "non_tensor":
        source[k] = [[7., 7.], [7., 7.]]
    elif fault == "sparse":
        source[k] = source[k].to_sparse()
    elif fault == "meta":
        source[k] = torch.empty(2, 2, device="meta")
    elif fault == "noncontiguous":
        source[k] = source[k].T
    elif fault == "rank":
        source[k] = torch.ones(1, 1, 1, 1, 1, 1)
    elif fault == "empty":
        source[k] = torch.ones(0)
    elif fault == "negative_view":
        source[k] = torch._neg_view(source[k])
    else:
        source[k] = torch.quantize_per_tensor(source[k], .1, 0, torch.qint8)
    refused(source, fresh, kwargs)


@pytest.mark.parametrize("fault", ["mixed", "collision", "repeated", "undeclared", "non_string",
                                  "long_ascii", "long_utf8", "bad_unicode"])
def test_namespace_and_keys_refused(small, fault):
    source, fresh, kwargs = small
    if fault in ("mixed", "collision", "repeated"):
        source = {"module." + k: v for k, v in source.items()}
        kwargs = controls(source, fresh, "uniform_module")
        if fault == "mixed":
            source["encoder.weight"] = source.pop("module.encoder.weight")
        elif fault == "collision":
            source["encoder.weight"] = source["module.encoder.weight"]
        else:
            source["module.module.encoder.weight"] = source.pop("module.encoder.weight")
    else:
        name = {"undeclared": "module.encoder.weight", "non_string": 7,
                "long_ascii": "x" * 513, "long_utf8": "é" * 300,
                "bad_unicode": "\ud800"}[fault]
        source[name] = source.pop("encoder.weight")
    refused(source, fresh, kwargs)


@pytest.mark.parametrize("pin", ["expected_candidate_sha256", "expected_policy_sha256",
                                "expected_inventory_sha256"])
def test_changed_control_pins_refused_before_tensor_access(small, pin):
    source, fresh, kwargs = small
    kwargs[pin] = "0" * 64
    refused(source, fresh, kwargs, "control_pin_mismatch")


@pytest.mark.parametrize("fault", ["classification", "real_domain", "file_uri", "file_hash",
                                  "file_bytes_bool", "repository", "rights", "overlap",
                                  "real_reference", "revision", "seed", "head_keys", "architecture",
                                  "architecture_bool", "namespace", "limit", "limit_bool",
                                  "signature_bool", "signature_dtype", "candidate_file", "extra"])
def test_rebound_invalid_controls_still_refused(small, fault):
    source, fresh, kwargs = small
    c, p = kwargs["candidate_manifest"], kwargs["policy"]
    if fault == "classification": c["classification"] = "prior_project_trained"
    elif fault == "real_domain": c["evidence_domain"] = "real_weights"
    elif fault == "file_uri": c["file"]["uri"] = "pretrained_weights/real.pth"
    elif fault == "file_hash": c["file"]["sha256"] = "not-a-hash"
    elif fault == "file_bytes_bool": c["file"]["bytes"] = True
    elif fault == "repository": c["source"].pop("repository")
    elif fault == "rights": c["rights"]["status"] = "unknown"
    elif fault == "overlap": c["overlap"]["status"] = "unresolved"
    elif fault == "real_reference": c["rights"]["checkpoint"]["reference"] = "https://example.invalid/license"
    elif fault == "revision": c["source"]["revision"] = ""
    elif fault == "seed": p["seed"] = 43
    elif fault == "head_keys": p["head_keys"] = ["conv_final"]
    elif fault == "architecture": p["architecture"]["init_filters"] = 32
    elif fault == "architecture_bool": p["architecture"]["in_channels"] = True
    elif fault == "namespace": p["namespace"] = "guess"
    elif fault == "limit": p["limits"]["max_tensor_bytes"] += 1
    elif fault == "limit_bool": p["limits"]["max_control_bytes"] = True
    elif fault == "signature_bool": c["state_signature"]["encoder.weight"]["shape"][0] = True
    elif fault == "signature_dtype": c["state_signature"]["encoder.weight"]["dtype"] = "torch.float64"
    elif fault == "candidate_file": p["candidate_file"]["sha256"] = invented_hash("other")
    else: c["optimizer"] = {}
    repin(kwargs)
    refused(source, fresh, kwargs)


@pytest.mark.parametrize("fault", ["prior", "capstone", "unknown", "same_hash_alias", "other_sha",
                                  "duplicate_uri", "import_flag", "bad_category", "row_extra",
                                  "bad_count", "real_domain"])
def test_inventory_denylist_and_exact_candidate(small, fault):
    source, fresh, kwargs = small
    inv = kwargs["historical_inventory"]
    row = inv["files"][0]
    if fault in ("prior", "capstone"):
        row["category"] = ("prior_project_checkpoint_import_denied" if fault == "prior"
                           else "capstone_diagnostic_checkpoint_import_denied")
    elif fault == "unknown": row["uri"] = "invented/unknown.pth"
    elif fault == "same_hash_alias":
        inv["files"].append(dict(row, uri="invented/renamed-old.pth",
                                 category="prior_project_checkpoint_import_denied"))
    elif fault == "other_sha": row["sha256"] = invented_hash("other")
    elif fault == "duplicate_uri": inv["files"].append(deepcopy(row))
    elif fault == "import_flag": row["weight_import_allowed"] = True
    elif fault == "bad_category": row["category"] = []
    elif fault == "row_extra": row["optimizer"] = {}
    elif fault == "bad_count": inv["files"] = [dict(row, uri=f"invented/{n}.pth") for n in range(257)]
    else: inv["evidence_domain"] = "real_weights"
    repin(kwargs)
    refused(source, fresh, kwargs)


@pytest.mark.parametrize("mapping", ["source", "fresh"])
def test_content_tampering_with_identical_shapes_fails(small, mapping):
    source, fresh, kwargs = small
    (source if mapping == "source" else fresh)["encoder.weight"][0, 0] += 1
    refused(source, fresh, kwargs, mapping + "_state_binding_mismatch")


def test_fresh_head_drift_fails_without_source_head_substitution(small):
    source, fresh, kwargs = small
    fresh[audit.HEAD_KEYS[0]][0] += 1
    refused(source, fresh, kwargs, "fresh_state_binding_mismatch")


@pytest.mark.parametrize("fault", ["tensor_count", "tensor_bytes", "control_bytes", "recursive",
                                  "non_json", "nonfinite_json"])
def test_limits_fail_before_clone_or_content_scan(small, fault, monkeypatch):
    source, fresh, kwargs = small
    if fault == "tensor_count":
        source = {f"key{n}": torch.ones(1) for n in range(1025)}
    elif fault == "tensor_bytes":
        # One allocated element, huge logical size: reject its header before scanning/cloning.
        source["encoder.weight"] = torch.ones(1).expand(64 * 1024**2 // 4 + 1)
    elif fault == "control_bytes": kwargs["candidate_manifest"]["source"]["citation"] = "x" * 1024**2
    elif fault == "recursive": kwargs["candidate_manifest"]["source"]["citation"] = kwargs["candidate_manifest"]
    elif fault == "non_json": kwargs["candidate_manifest"]["source"]["citation"] = object()
    else: kwargs["candidate_manifest"]["source"]["citation"] = float("nan")
    monkeypatch.setattr(torch.Tensor, "clone", lambda *a, **k: pytest.fail("Unexpected clone"))
    if fault == "tensor_bytes":
        monkeypatch.setattr(torch, "isfinite", lambda *a, **k: pytest.fail("Scanned oversized tensor"))
    result, report = audit.prepare_initialization(source, fresh, **kwargs)
    assert result is None and report["status"] == "refused"
    assert report["initialized_state_sha256"] is None
    if fault == "tensor_bytes": assert report["reason"] == "tensor_size_limit"


def test_no_io_deserialization_model_computation_or_optimizer(small, monkeypatch):
    source, fresh, kwargs = small
    def forbidden(*a, **k):
        pytest.fail("Forbidden operation during initialization audit")
    import builtins
    from pathlib import Path
    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(torch, "load", forbidden)
    monkeypatch.setattr(torch, "save", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(torch.nn.Module, "_call_impl", forbidden)
    monkeypatch.setattr(torch.Tensor, "backward", forbidden)
    monkeypatch.setattr(torch.optim, "AdamW", forbidden)
    monkeypatch.setattr(torch.optim.Optimizer, "step", forbidden)
    result, report = audit.prepare_initialization(source, fresh, **kwargs)
    assert result is not None and report["status"] == "pass"


def test_missing_both_heads_cannot_be_bound_as_complete(small):
    source, fresh, _ = small
    for k in audit.HEAD_KEYS:
        source.pop(k)
        fresh.pop(k)
    kwargs = controls(source, fresh)
    refused(source, fresh, kwargs, "destination_head_absent")


def test_control_pin_is_canonical_and_strict_json(small):
    _, _, kwargs = small
    c = kwargs["candidate_manifest"]
    wire = (json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode()
    assert audit.control_sha256(c) == hashlib.sha256(wire).hexdigest()
    with pytest.raises(ValueError): audit.control_sha256({"bad": float("inf")})


def test_bound_source_and_destination_cannot_both_drop_backbone(small):
    source, fresh, kwargs = small
    source.pop("encoder.weight")
    fresh.pop("encoder.weight")
    refused(source, fresh, kwargs, "source_state_binding_mismatch")


def test_inputs_with_autograd_metadata_return_detached_clones(small):
    source, fresh, kwargs = small
    for value in source.values():
        value.requires_grad_(True)
    result, report = audit.prepare_initialization(source, fresh, **kwargs)
    assert report["status"] == "pass"
    assert all(not value.requires_grad and value.grad is None for value in result.values())
    assert all(value.requires_grad and value.grad is None for value in source.values())


@pytest.mark.parametrize("field", ["candidate_manifest", "policy", "historical_inventory"])
def test_wrong_top_level_type_is_a_structured_refusal(small, field):
    source, fresh, kwargs = small
    kwargs[field] = []
    repin(kwargs)
    refused(source, fresh, kwargs)


@pytest.mark.parametrize("field", ["code", "checkpoint", "data"])
def test_each_rights_reference_is_required(small, field):
    source, fresh, kwargs = small
    kwargs["candidate_manifest"]["rights"].pop(field)
    repin(kwargs)
    refused(source, fresh, kwargs, "invalid_rights_fields")


def test_inventory_zero_import_flag_is_not_boolean_false(small):
    source, fresh, kwargs = small
    kwargs["historical_inventory"]["files"][0]["weight_import_allowed"] = 0
    repin(kwargs)
    refused(source, fresh, kwargs, "inventory_import_policy_mismatch")
