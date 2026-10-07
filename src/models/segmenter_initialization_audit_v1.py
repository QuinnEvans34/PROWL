"""Invented-only, in-memory initialization audit. No deserializer or execution grant.

All tensors must already be supplied on CPU. Controls describe invented evidence;
their pins establish consistency, not source authenticity or training permission.
"""
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import math

import torch


DOMAIN = "invented_weights_only"
HEAD_KEYS = ("conv_final.2.conv.bias", "conv_final.2.conv.weight")
REPORT_VERSION = "segmenter-initialization-audit-report-1"
_CATEGORIES = {
    "prior_project_checkpoint_import_denied",
    "capstone_diagnostic_checkpoint_import_denied",
    "third_party_weights_not_approved_for_this_run",
}


def architecture(out_channels=3):
    return dict(in_channels=1, out_channels=out_channels, init_filters=16,
                norm="group", num_groups=8, blocks_down=[1, 2, 2, 4],
                blocks_up=[1, 1, 1], dropout_prob=0)


def limits():
    return dict(max_tensors=1024, max_key_bytes=512,
                max_tensor_bytes=64 * 1024**2, max_control_bytes=1024**2)


class _Refusal(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise _Refusal(reason)


def _fields(value, names, reason):
    _require(type(value) is dict and set(value) == set(names), reason)


def _text(value, reason, maximum=4096):
    _require(type(value) is str and 0 < len(value) <= maximum and
             all(ord(c) >= 32 for c in value), reason)


def _sha(value, reason):
    _require(type(value) is str and len(value) == 64 and
             all(c in "0123456789abcdef" for c in value), reason)


def _json_walk(value, depth=0, count=None):
    count = [0] if count is None else count
    count[0] += 1
    _require(depth <= 16 and count[0] <= 8192, "control_structure_limit")
    if type(value) is dict:
        _require(len(value) <= 4096 and all(type(k) is str for k in value),
                 "invalid_json_object")
        for k, v in value.items():
            _json_walk(k, depth + 1, count)
            _json_walk(v, depth + 1, count)
    elif type(value) is list:
        _require(len(value) <= 4096, "control_structure_limit")
        for v in value:
            _json_walk(v, depth + 1, count)
    elif type(value) is str:
        _require(len(value) <= 1024**2, "control_size_limit")
    elif type(value) is float:
        _require(math.isfinite(value), "nonfinite_json")
    else:
        _require(value is None or type(value) in (bool, int), "invalid_json_value")


def _canonical(value):
    _json_walk(value)
    try:
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, UnicodeError, OverflowError) as error:
        raise _Refusal("invalid_json_encoding") from error
    _require(len(raw) <= 1024**2, "control_size_limit")
    return raw


def control_sha256(value):
    """Canonical JSON control hash; no file access or authenticity attestation."""
    return hashlib.sha256(_canonical(value)).hexdigest()


def _pin(value, expected):
    _sha(expected, "invalid_control_pin")
    observed = control_sha256(value)
    _require(observed == expected, "control_pin_mismatch")
    return observed


def _architecture(value, channels):
    _fields(value, architecture(), "invalid_architecture_fields")
    for k in ("in_channels", "out_channels", "init_filters", "num_groups"):
        _require(type(value[k]) is int, "invalid_architecture_type")
    for k in ("blocks_down", "blocks_up"):
        _require(type(value[k]) is list and all(type(v) is int for v in value[k]),
                 "invalid_architecture_type")
    _require(type(value["norm"]) is str and
             type(value["dropout_prob"]) in (int, float), "invalid_architecture_type")
    _require(value == architecture(channels), "architecture_mismatch")


def _reference(value):
    _fields(value, ("reference", "sha256"), "invalid_evidence_reference")
    _text(value["reference"], "invalid_evidence_reference")
    _require(value["reference"].startswith("invented:"), "real_evidence_refused")
    _sha(value["sha256"], "invalid_evidence_hash")


def _file(value):
    _fields(value, ("uri", "sha256", "bytes"), "invalid_file_identity")
    _text(value["uri"], "invalid_file_uri")
    _require(value["uri"].startswith("invented/") and
             "\\" not in value["uri"] and ":" not in value["uri"] and
             all(p not in ("", ".", "..") for p in value["uri"].split("/")),
             "real_or_unsafe_file_uri_refused")
    _sha(value["sha256"], "invalid_file_hash")
    _require(type(value["bytes"]) is int and 0 < value["bytes"] <= 64 * 1024**2,
             "invalid_file_bytes")


def _signature(value):
    _require(type(value) is dict and 0 < len(value) <= 1024, "invalid_signature")
    for k, row in value.items():
        _text(k, "invalid_signature_key", 512)
        try:
            _require(len(k.encode("utf-8")) <= 512, "key_size_limit")
        except UnicodeError as error:
            raise _Refusal("invalid_key_encoding") from error
        _fields(row, ("shape", "dtype"), "invalid_signature_row")
        shape = row["shape"]
        _require(type(shape) is list and len(shape) <= 5 and
                 all(type(v) is int and v > 0 for v in shape), "invalid_signature_shape")
        _require(row["dtype"] == "torch.float32", "invalid_signature_dtype")
    _require(sum(math.prod(v["shape"]) * 4 for v in value.values()) <= 64 * 1024**2,
             "tensor_size_limit")


def _controls(candidate, policy, inventory):
    _fields(candidate, ("schema_version", "evidence_domain", "classification", "file",
                        "source", "rights", "overlap", "architecture",
                        "state_signature", "state_sha256"), "invalid_candidate_fields")
    _require(candidate["schema_version"] == "segmenter-initialization-candidate-1",
             "candidate_version_mismatch")
    _require(candidate["evidence_domain"] == DOMAIN, "real_evidence_refused")
    _require(candidate["classification"] == "licensed_third_party_general_pretraining",
             "source_classification_denied")
    _file(candidate["file"])
    source = candidate["source"]
    _fields(source, ("repository", "artifact", "revision", "citation", "retrieval"),
             "invalid_source_fields")
    for k in ("repository", "artifact", "revision", "citation"):
        _text(source[k], "missing_source_provenance")
    _reference(source["retrieval"])
    rights = candidate["rights"]
    _fields(rights, ("status", "code", "checkpoint", "data"), "invalid_rights_fields")
    _require(rights["status"] == "permitted", "rights_unqualified")
    for k in ("code", "checkpoint", "data"):
        _reference(rights[k])
    overlap = candidate["overlap"]
    _fields(overlap, ("status", "evidence"), "invalid_overlap_fields")
    _require(overlap["status"] == "reviewed_separate", "overlap_unqualified")
    _reference(overlap["evidence"])
    _architecture(candidate["architecture"], 32)
    _signature(candidate["state_signature"])
    _sha(candidate["state_sha256"], "invalid_source_state_hash")

    _fields(policy, ("schema_version", "evidence_domain", "architecture", "seed",
                     "head_keys", "namespace", "candidate_file", "limits",
                     "fresh_state_signature", "fresh_state_sha256"), "invalid_policy_fields")
    _require(policy["schema_version"] == "segmenter-initialization-policy-1" and
             policy["evidence_domain"] == DOMAIN, "policy_domain_or_version_mismatch")
    _architecture(policy["architecture"], 3)
    _require(type(policy["seed"]) is int and policy["seed"] == 42, "seed_policy_mismatch")
    _require(type(policy["head_keys"]) is list and policy["head_keys"] == list(HEAD_KEYS),
             "head_policy_mismatch")
    _require(policy["namespace"] in ("identity", "uniform_module"), "namespace_policy_mismatch")
    _fields(policy["limits"], limits(), "invalid_limits_fields")
    _require(all(type(v) is int for v in policy["limits"].values()) and
             policy["limits"] == limits(), "limits_policy_mismatch")
    _file(policy["candidate_file"])
    _require(policy["candidate_file"] == candidate["file"], "candidate_identity_mismatch")
    _signature(policy["fresh_state_signature"])
    _sha(policy["fresh_state_sha256"], "invalid_fresh_state_hash")

    _fields(inventory, ("schema_version", "evidence_domain", "files"), "invalid_inventory_fields")
    _require(inventory["schema_version"] == "segmenter-initialization-inventory-1" and
             inventory["evidence_domain"] == DOMAIN, "inventory_domain_or_version_mismatch")
    rows = inventory["files"]
    _require(type(rows) is list and 0 < len(rows) <= 256, "inventory_count_limit")
    uris = set()
    matches = []
    for row in rows:
        _fields(row, ("uri", "sha256", "bytes", "category", "weight_import_allowed"),
                 "invalid_inventory_row")
        _file({k: row[k] for k in ("uri", "sha256", "bytes")})
        _require(row["uri"] not in uris, "inventory_duplicate_uri")
        uris.add(row["uri"])
        _require(type(row["category"]) is str and row["category"] in _CATEGORIES and
                 row["weight_import_allowed"] is False,
                 "inventory_import_policy_mismatch")
        if row["sha256"] == candidate["file"]["sha256"]:
            _require(row["category"] == "third_party_weights_not_approved_for_this_run",
                     "historical_or_capstone_hash_denied")
        if row["uri"] == candidate["file"]["uri"]:
            matches.append(row)
    _require(len(matches) == 1 and all(matches[0][k] == candidate["file"][k]
                                    for k in ("sha256", "bytes")), "candidate_not_in_inventory")
    _require(matches[0]["category"] == "third_party_weights_not_approved_for_this_run",
             "historical_or_capstone_hash_denied")


def describe_state(state):
    """Return a complete signature/content hash of bounded dense float32 CPU tensors.

    This helper does not validate initialization provenance or grant execution.
    Tensor content is read only after all headers and aggregate bounds pass.
    """
    _require(type(state) in (dict, OrderedDict) and 0 < len(state) <= 1024,
             "invalid_tensor_mapping")
    signature = {}
    total = 0
    for k, value in state.items():
        _text(k, "invalid_tensor_key", 512)
        try:
            _require(len(k.encode("utf-8")) <= 512, "key_size_limit")
        except UnicodeError as error:
            raise _Refusal("invalid_key_encoding") from error
        _require(type(value) is torch.Tensor, "non_tensor_value")
        _require(value.device.type == "cpu", "non_cpu_tensor")
        _require(value.layout == torch.strided and value.dtype == torch.float32 and
                 not value.is_quantized and not value.is_conj() and not value.is_neg(),
                 "unsupported_tensor_type")
        shape = list(value.shape)
        _require(len(shape) <= 5 and all(v > 0 for v in shape), "unsupported_tensor_shape")
        total += value.numel() * value.element_size()
        _require(total <= 64 * 1024**2, "tensor_size_limit")
        signature[k] = dict(shape=shape, dtype=str(value.dtype))
    for value in state.values():
        _require(value.is_contiguous(), "noncontiguous_tensor")
        _require(torch.isfinite(value).all().item(), "nonfinite_tensor")
    h = hashlib.sha256()
    for k in sorted(state):
        h.update(_canonical(dict(name=k, **signature[k])))
        h.update(memoryview(state[k].detach().numpy()).cast("B"))
    return dict(signature=signature, sha256=h.hexdigest(), tensor_bytes=total)


def _normalize(state, namespace):
    normalized = {}
    for k, value in state.items():
        if namespace == "uniform_module":
            _require(k.startswith("module."), "mixed_or_missing_module_prefix")
            name = k[len("module."):]
            _require(name and not name.startswith("module."), "repeated_module_prefix")
        else:
            _require(not k.startswith("module."), "undeclared_module_prefix")
            name = k
        _require(name not in normalized, "namespace_collision")
        normalized[name] = value
    return normalized


def _prepare(source, fresh, candidate, policy, inventory, report):
    _controls(candidate, policy, inventory)
    report["source_file"] = deepcopy(candidate["file"])
    observed_source = describe_state(source)
    observed_fresh = describe_state(fresh)
    report["source_signature"] = observed_source["signature"]
    report["destination_signature"] = observed_fresh["signature"]
    report["source_state_sha256"] = observed_source["sha256"]
    report["fresh_state_sha256"] = observed_fresh["sha256"]
    normalized = _normalize(source, policy["namespace"])
    report["normalized_source_signature"] = {
        k: dict(shape=list(v.shape), dtype=str(v.dtype)) for k, v in normalized.items()
    }
    report["missing_keys"] = sorted(set(fresh) - set(normalized))
    report["unexpected_keys"] = sorted(set(normalized) - set(fresh))
    for k in sorted(set(normalized) & set(fresh)):
        expected = list(fresh[k].shape)
        if k in HEAD_KEYS:
            expected = [32] if k.endswith("bias") else [32, 16, 1, 1, 1]
        if list(normalized[k].shape) != expected or normalized[k].dtype != fresh[k].dtype:
            report["mismatched_keys"].append(k)
    _require(not report["missing_keys"] and not report["unexpected_keys"],
             "tensor_inventory_mismatch")
    _require(not report["mismatched_keys"], "tensor_shape_or_dtype_mismatch")
    _require(all(k in fresh for k in HEAD_KEYS), "destination_head_absent")
    _require(list(fresh[HEAD_KEYS[0]].shape) == [3] and
             list(fresh[HEAD_KEYS[1]].shape) == [3, 16, 1, 1, 1], "destination_head_shape_mismatch")
    _require(observed_source["signature"] == candidate["state_signature"] and
             observed_source["sha256"] == candidate["state_sha256"], "source_state_binding_mismatch")
    _require(observed_fresh["signature"] == policy["fresh_state_signature"] and
             observed_fresh["sha256"] == policy["fresh_state_sha256"], "fresh_state_binding_mismatch")
    report["head_before_sha256"] = describe_state({k: fresh[k] for k in HEAD_KEYS})["sha256"]
    # Every validation is complete before any tensor is cloned or replacement is returned.
    merged = {k: (fresh[k] if k in HEAD_KEYS else normalized[k]).detach().clone()
              for k in sorted(fresh)}
    initialized = describe_state(merged)
    report["initialized_state_sha256"] = initialized["sha256"]
    report["head_after_sha256"] = describe_state({k: merged[k] for k in HEAD_KEYS})["sha256"]
    report["loaded_keys"] = sorted(set(fresh) - set(HEAD_KEYS))
    report["replaced_keys"] = list(HEAD_KEYS)
    report["status"] = "pass"
    report["reason"] = None
    return merged


def prepare_initialization(source_state, fresh_destination_state, *, candidate_manifest,
                           expected_candidate_sha256, policy, expected_policy_sha256,
                           historical_inventory, expected_inventory_sha256):
    """Return (complete cloned CPU state, report), or (None, refusal report).

    There is no model mutation, I/O, deserialization, RNG use or optimizer here.
    Only invented evidence is accepted. Real initialization needs a later reader,
    source qualification and versioned consumer; this report grants no authority.
    """
    report = dict(schema_version=REPORT_VERSION, evidence_domain=DOMAIN,
                  execution_authority="none", status="refused", reason=None,
                  control_sha256=dict(candidate=None, policy=None, inventory=None),
                  source_file=None, source_signature={}, destination_signature={},
                  normalized_source_signature={}, source_state_sha256=None,
                  fresh_state_sha256=None, initialized_state_sha256=None,
                  head_before_sha256=None, head_after_sha256=None, loaded_keys=[],
                  replaced_keys=[], missing_keys=[], unexpected_keys=[], mismatched_keys=[])
    try:
        for name, value, pin in (
            ("candidate", candidate_manifest, expected_candidate_sha256),
            ("policy", policy, expected_policy_sha256),
            ("inventory", historical_inventory, expected_inventory_sha256),
        ):
            report["control_sha256"][name] = _pin(value, pin)
        result = _prepare(source_state, fresh_destination_state, candidate_manifest,
                          policy, historical_inventory, report)
    except _Refusal as error:
        report["reason"] = str(error)
        return None, report
    return result, report
