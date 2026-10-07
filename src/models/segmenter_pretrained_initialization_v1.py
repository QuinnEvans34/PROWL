"""V02-I: generated values audit → exact backbone plus fresh head, CPU only."""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

from src.models import segmenter_source_values_v1 as values

DOMAIN = "invented_pretrained_init"
POLICY = "exact_backbone_fresh_head"
HEAD_KEYS = ("conv_final.2.conv.bias", "conv_final.2.conv.weight")
VALUES_PIN = "38e1685cb53e9d36a9f449aad9554b4690d695a926227744e1ef85ca174acc8a"
FACTORY_PIN = "d3fff9db229c3641aab2456a54cce64d7ebf08494a9fe1abef241cef7d8b722d"
FACTORY_PATH = Path(__file__).with_name("segresnet.py")
REPORT_VERSION = "pretrained-initialization-report-1"
TOKEN = object()
require, canonical, digest, Refusal = values.require, values.canonical, values.digest, values.Refusal


def code_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def architecture():
    a = values.meta.architecture()
    a["out_channels"] = 3
    return a


def signature():
    s = deepcopy(values.meta.expected_signature())
    for key in HEAD_KEYS: s[key]["shape"][0] = 3
    return s


def limits():
    return dict(working_bytes=128 * 1024**2, report_bytes=1024**2)


@dataclass(frozen=True)
class InitializationAudit:
    state: object
    report_json: bytes
    _token: object

    @property
    def report(self):
        return json.loads(self.report_json)


def _shape_rows(rows):
    return {k: dict(shape=r["shape"], dtype=r["dtype"]) for k, r in rows.items()}


def _select(rows, head):
    return {k: r for k, r in rows.items() if (k in HEAD_KEYS) == head}


def _architecture_check(a):
    expected = architecture()
    require(type(a) is dict and a == expected, "initialization_architecture")
    for key, value in expected.items():
        require(type(a[key]) is type(value), "initialization_architecture_type")
        if type(value) is list:
            require(all(type(n) is int for n in a[key]), "initialization_architecture_type")


def initialize(audit, control, *, control_sha256):
    require(type(control) is dict and control.get("domain") == DOMAIN, "actual_initialization_unqualified")
    require(digest(control) == control_sha256, "initialization_control_pin")
    c = json.loads(canonical(control))
    values.meta._fields(c, ("schema_version", "domain", "values_report_sha256", "values_code_sha256",
        "initializer_sha256", "factory_sha256", "target_architecture", "seed", "policy", "limits"), "initialization_control_fields")
    require(c["schema_version"] == "pretrained-initialization-control-1" and c["policy"] == POLICY and
        type(c["seed"]) is int and c["seed"] == 42 and c["target_architecture"] == architecture() and
        c["limits"] == limits(), "initialization_policy")
    _architecture_check(c["target_architecture"])
    require(c["values_code_sha256"] == VALUES_PIN == values.code_sha256() and
        c["initializer_sha256"] == code_sha256() and c["factory_sha256"] == FACTORY_PIN ==
        hashlib.sha256(FACTORY_PATH.read_bytes()).hexdigest(), "initialization_code_pins")
    source_report = values.validate_audit(audit)
    require(c["values_report_sha256"] == digest(source_report), "initialization_values_report_pin")
    source_rows = values.state_rows(audit.state)
    require(_shape_rows(source_rows) == values.meta.expected_signature(), "initialization_source_signature")
    # Conservative owned tensor/buffer plan; operational RSS is separately qualified.
    require(3 * values.MODEL_BYTES + 2 * 18803724 <= c["limits"]["working_bytes"], "initialization_allocation_budget")
    import torch
    require(torch.get_default_device().type == "cpu" and torch.get_default_dtype() == torch.float32,
            "initialization_ambient_tensor_defaults")
    from src.models.segresnet import build_model
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(c["seed"])
        model = build_model({"model": c["target_architecture"]})
    fresh = model.state_dict()
    fresh_rows = values.state_rows(dict(fresh))
    require(_shape_rows(fresh_rows) == signature(), "initialization_factory_signature")
    head = {k: fresh[k].detach().clone() for k in HEAD_KEYS}
    candidate = {k: (head[k] if k in HEAD_KEYS else audit.state[k]).detach().clone() for k in fresh}
    result = model.load_state_dict(candidate, strict=True)
    require(not result.missing_keys and not result.unexpected_keys, "initialization_strict_load")
    target = {k: t.detach().clone() for k, t in model.state_dict().items()}
    rows = values.state_rows(target)
    require(_shape_rows(rows) == signature() and _select(rows, False) == _select(source_rows, False) and
        _select(rows, True) == _select(fresh_rows, True), "initialization_transfer_mismatch")
    require(values.state_rows(audit.state) == source_rows and values.validate_audit(audit) == source_report,
        "initialization_source_mutated")
    for k in target:
        require(target[k].untyped_storage().data_ptr() != audit.state[k].untyped_storage().data_ptr(), "initialization_source_alias")
    byte_counts = dict(source=18805696, source_head=2176, backbone=18803520, fresh_head=204, target=18803724)
    require(sum(t.numel() * 4 for t in target.values()) == byte_counts["target"], "initialization_target_bytes")
    report = dict(schema_version=REPORT_VERSION, domain=DOMAIN, status="pass", scope="invented_initialization_only",
        execution_authority="none", training_eligible=False, control_sha256=digest(c), code_sha256=code_sha256(),
        values_code_sha256=VALUES_PIN, values_report_sha256=digest(source_report), factory_sha256=FACTORY_PIN,
        source_sha256=source_report["source_sha256"], source_state_sha256=source_report["state_sha256"],
        source_backbone_sha256=digest(_select(source_rows, False)), fresh_head_sha256=digest(_select(fresh_rows, True)),
        target_state_sha256=digest(rows), seed=42, target_architecture=architecture(), policy=POLICY,
        excluded_keys=list(HEAD_KEYS), model=rows, bytes=byte_counts)
    raw = canonical(report)
    require(len(raw) <= c["limits"]["report_bytes"], "initialization_report_limit")
    return InitializationAudit(MappingProxyType(target), raw, TOKEN)


def validate_initialization(audit):
    require(type(audit) is InitializationAudit and audit._token is TOKEN and type(audit.report_json) is bytes,
        "initialization_typed_audit_required")
    r = audit.report
    require(canonical(r) == audit.report_json, "initialization_report_encoding")
    values.meta._fields(r, ("schema_version", "domain", "status", "scope", "execution_authority", "training_eligible",
        "control_sha256", "code_sha256", "values_code_sha256", "values_report_sha256", "factory_sha256",
        "source_sha256", "source_state_sha256", "source_backbone_sha256", "fresh_head_sha256", "target_state_sha256",
        "seed", "target_architecture", "policy", "excluded_keys", "model", "bytes"), "initialization_report_fields")
    require(r["schema_version"] == REPORT_VERSION and r["domain"] == DOMAIN and r["status"] == "pass" and
        r["scope"] == "invented_initialization_only" and r["execution_authority"] == "none" and
        r["training_eligible"] is False and r["seed"] == 42 and r["target_architecture"] == architecture() and
        r["policy"] == POLICY and r["excluded_keys"] == list(HEAD_KEYS) and r["code_sha256"] == code_sha256() and
        r["values_code_sha256"] == VALUES_PIN == values.code_sha256() and r["factory_sha256"] == FACTORY_PIN ==
        hashlib.sha256(FACTORY_PATH.read_bytes()).hexdigest(), "initialization_report_lineage")
    for key in ("control_sha256", "values_report_sha256", "source_sha256", "source_state_sha256",
                "source_backbone_sha256", "fresh_head_sha256", "target_state_sha256"):
        require(type(r[key]) is str and values.meta.re.fullmatch(r"[0-9a-f]{64}", r[key]), "initialization_report_pin")
    require(r["source_sha256"] != values.meta.ACTUAL_CANDIDATE_SHA, "actual_initialization_audit_refused")
    _architecture_check(r["target_architecture"])
    require(r["bytes"] == dict(source=18805696, source_head=2176, backbone=18803520, fresh_head=204, target=18803724),
        "initialization_report_bytes")
    rows = values.state_rows(audit.state)
    require(_shape_rows(rows) == signature() and rows == r["model"] and digest(rows) == r["target_state_sha256"] and
        digest(_select(rows, False)) == r["source_backbone_sha256"] and
        digest(_select(rows, True)) == r["fresh_head_sha256"], "initialization_audit_mutated")
    return r
