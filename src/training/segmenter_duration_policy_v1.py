"""Pure native-count duration policy. No arrays, models, I/O or run authority."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import math


KIND = "segmenter_duration_policy_v1"
BASELINE_KIND = "duration_native_count_baseline_v1"
MAX_VOXELS = 46_219_264
CLASSES = {"pancreas_parenchyma": (1,), "lesion": (2,), "pancreas_lesion_union": (1, 2)}
ROW_FIELDS = {"case_id", "role", "status", "reason", "counts", "reported_metrics"}
COUNT_FIELDS = {"confusion_matrix", "components", "voxel_volume_mm3", "source_boundary_contact"}


class DurationPolicyError(ValueError):
    """Invalid trusted policy/control; screen faults become stopped results."""

    def __init__(self, reason, detail):
        self.reason = reason
        super().__init__(f"{reason}: {detail}")


def _require(ok, reason, detail):
    if not ok:
        raise DurationPolicyError(reason, detail)


def _keys(value, fields, reason):
    _require(type(value) is dict and set(value) == fields, reason, "Exact fields required")


def _pin(value):
    return (type(value) is str and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def record_digest(value):
    """Canonical finite JSON SHA-256; caller supplies independent trusted pins."""
    try:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise DurationPolicyError("json_record", "Finite JSON required") from exc
    return sha256(raw).hexdigest()


def _rules():
    return dict(macro_recall_loss=0.03, case_component_recall_loss=0.10,
                tiny_recall_floor=0.95, interim_case_fp_ratio=1.25,
                terminal_case_fp_ratio=1.10, terminal_mean_fp_ratio=0.80,
                terminal_lesion_dice_ratio=1.20, pancreas_dice_must_not_decline=True)


def _counts(value):
    _keys(value, COUNT_FIELDS, "counts_fields")
    matrix = value["confusion_matrix"]
    _require(type(matrix) is list and len(matrix) == 3
             and all(type(r) is list and len(r) == 3
                     and all(type(v) is int and 0 <= v <= MAX_VOXELS for v in r)
                     for r in matrix), "confusion_counts", "Nonnegative integer 3x3 counts required")
    total = sum(map(sum, matrix))
    _require(0 < total <= MAX_VOXELS, "confusion_counts", "Native voxel bound exceeded")
    volume = value["voxel_volume_mm3"]
    _require(type(volume) in (int, float) and 0 < volume <= 1e9 and math.isfinite(volume),
             "voxel_volume", "Positive finite native mm3 required")
    _require(type(value["source_boundary_contact"]) is bool, "boundary_flag", "Boolean required")
    components = value["components"]
    _require(type(components) is list and 0 < len(components) <= total,
             "components", "All native reference components required")
    for index, c in enumerate(components, 1):
        _keys(c, {"component_id", "reference_voxels", "true_positive"}, "components")
        _require(type(c["component_id"]) is int and c["component_id"] == index
                 and type(c["reference_voxels"]) is int and type(c["true_positive"]) is int
                 and 0 < c["reference_voxels"] <= total
                 and 0 <= c["true_positive"] <= c["reference_voxels"],
                 "components", "Ordered positive reference and bounded TP counts required")
    _require(sum(c["reference_voxels"] for c in components) == sum(matrix[2])
             and sum(c["true_positive"] for c in components) == matrix[2][2],
             "component_totals", "Components must partition the lesion reference/TP")
    _require(sum(matrix[1]) > 0 and sum(matrix[2]) > 0,
             "positive_reference", "This slice requires positive pancreas and lesion references")
    return value


def _fractions(counts):
    matrix = counts["confusion_matrix"]
    result = {}
    for name, classes in CLASSES.items():
        reference = sum(sum(matrix[i]) for i in classes)
        predicted = sum(matrix[i][j] for i in range(3) for j in classes)
        tp = sum(matrix[i][j] for i in classes for j in classes)
        result[name] = dict(target_voxels=reference, predicted_voxels=predicted,
                            true_positive=tp, dice=Fraction(2 * tp, reference + predicted),
                            recall=Fraction(tp, reference), precision=Fraction(tp, predicted) if predicted else Fraction(0),
                            false_positive_ml=Fraction(predicted - tp) * Fraction(str(counts["voxel_volume_mm3"])) / 1000,
                            predicted_reference_ratio=Fraction(predicted, reference))
    return result


def _plain(value):
    if isinstance(value, Fraction):
        return float(value)
    if type(value) is dict:
        return {k: _plain(v) for k, v in value.items()}
    if type(value) is list:
        return [_plain(v) for v in value]
    return value


def _row(row):
    _keys(row, ROW_FIELDS, "outcome_fields")
    _require(type(row["case_id"]) is str and bool(row["case_id"].strip())
             and row["role"] in ("train", "report_only"), "case_role", "Explicit case/role required")
    _require(row["status"] in ("valid", "failed", "empty", "abstained"),
             "outcome_status", "Known status required")
    if row["status"] != "valid":
        _require(type(row["reason"]) is str and bool(row["reason"].strip())
                 and row["counts"] is None and row["reported_metrics"] is None,
                 "failure_record", "Failure reason and null counts/metrics required")
        return None
    _require(row["reason"] is None, "outcome_status", "Valid output cannot carry a failure reason")
    counts = _counts(row["counts"])
    metrics = _fractions(counts)
    if row["reported_metrics"] is not None:
        _require(record_digest(row["reported_metrics"]) == record_digest(_plain(metrics)),
                 "reported_metrics", "Supplied summaries disagree with native counts")
    return metrics


def build_policy(baseline, *, trusted_baseline_sha256, tiny_case_id, boundary_case_id):
    """Bind approved fixed 192-step policy to independently pinned numeric baseline."""
    _require(_pin(trusted_baseline_sha256) and record_digest(baseline) == trusted_baseline_sha256,
             "baseline_pin", "Independent baseline pin differs")
    _keys(baseline, {"schema_version", "kind", "cases"}, "baseline_fields")
    _require(baseline["schema_version"] == "1.0.0" and baseline["kind"] == BASELINE_KIND,
             "baseline_kind", "Versioned native-count baseline required")
    rows = baseline["cases"]
    _require(type(rows) is list and len(rows) == 7, "baseline_membership", "Six train and one report-only required")
    for row in rows:
        _require(_row(row) is not None, "baseline_outcome", "Baseline must contain valid numeric evidence")
    ids = [r["case_id"] for r in rows]
    _require(len(set(ids)) == 7 and [r["role"] for r in rows] == ["train"] * 6 + ["report_only"],
             "baseline_membership", "Exact ordered roles and distinct IDs required")
    _require(tiny_case_id in ids[:6] and boundary_case_id in ids[:6] and tiny_case_id != boundary_case_id,
             "case_markers", "Separate tiny/boundary training IDs required")
    boundary = next(r for r in rows if r["case_id"] == boundary_case_id)
    _require(boundary["counts"]["source_boundary_contact"], "case_markers", "Boundary evidence must be explicit")
    return dict(schema_version="1.0.0", kind=KIND, terminal_step=192,
                checkpoint_steps=[0, 48, 96, 144, 192], screen_steps=[48, 96, 144, 192],
                train_case_ids=ids[:6], report_case_id=ids[6], tiny_case_id=tiny_case_id,
                boundary_case_id=boundary_case_id, baseline_sha256=trusted_baseline_sha256,
                baseline=deepcopy(baseline), rules=_rules(),
                promotion_allowed=False, specificity_claim_allowed=False, execution_authority=False)


def validate_policy(policy, *, trusted_policy_sha256):
    _require(_pin(trusted_policy_sha256) and record_digest(policy) == trusted_policy_sha256,
             "policy_pin", "Independent policy pin differs")
    fields = {"schema_version", "kind", "terminal_step", "checkpoint_steps", "screen_steps",
              "train_case_ids", "report_case_id", "tiny_case_id", "boundary_case_id",
              "baseline_sha256", "baseline", "rules", "promotion_allowed",
              "specificity_claim_allowed", "execution_authority"}
    _keys(policy, fields, "policy_fields")
    expected = build_policy(policy["baseline"], trusted_baseline_sha256=policy["baseline_sha256"],
                            tiny_case_id=policy["tiny_case_id"], boundary_case_id=policy["boundary_case_id"])
    _require(record_digest(policy) == record_digest(expected), "policy_drift", "Fixed approved policy differs")
    return policy


def cadence_plan(policy, *, trusted_policy_sha256):
    validate_policy(policy, trusted_policy_sha256=trusted_policy_sha256)
    return [dict(step=s, checkpoint=True, native_screen=s != 0,
                 expected_exposures_per_train_case=s // 6, report_only=s == 192)
            for s in policy["checkpoint_steps"]]


def _aggregate(rows):
    values = [_fractions(r["counts"]) for r in rows]
    macro, pooled = {}, {}
    for name in CLASSES:
        macro[name] = {key: sum(v[name][key] for v in values) / len(values)
                       for key in ("dice", "recall", "precision", "false_positive_ml")}
        n = sum(v[name]["target_voxels"] for v in values)
        p = sum(v[name]["predicted_voxels"] for v in values)
        tp = sum(v[name]["true_positive"] for v in values)
        pooled[name] = dict(target_voxels=n, predicted_voxels=p, true_positive=tp,
                            dice=Fraction(2 * tp, n + p), recall=Fraction(tp, n),
                            precision=Fraction(tp, p) if p else Fraction(0),
                            false_positive_ml=sum(v[name]["false_positive_ml"] for v in values))
    return dict(case_count=len(rows), macro=macro, pooled=pooled)


def assess_screen(policy, screen, *, trusted_policy_sha256):
    """Invalid/incomplete screen stops; report-only quality never selects a result."""
    validate_policy(policy, trusted_policy_sha256=trusted_policy_sha256)
    terminal = type(screen) is dict and type(screen.get("step")) is int and screen["step"] == 192
    required = [(i, "train") for i in policy["train_case_ids"]]
    if terminal:
        required.append((policy["report_case_id"], "report_only"))
    result = dict(policy_sha256=trusted_policy_sha256, decision="stopped", passed=False,
                  step=screen.get("step") if type(screen) is dict else None,
                  checks={}, ledger=[], per_case={}, aggregates=None, report_only=None,
                  reasons=[], promotion_allowed=False, specificity_claim_allowed=False,
                  execution_authority=False)
    try:
        _keys(screen, {"schema_version", "policy_sha256", "baseline_sha256", "step", "outcomes"}, "screen_fields")
        _require(screen["schema_version"] == "1.0.0" and screen["policy_sha256"] == trusted_policy_sha256
                 and screen["baseline_sha256"] == policy["baseline_sha256"], "screen_identity", "Screen lineage differs")
        _require(type(screen["step"]) is int and screen["step"] in policy["screen_steps"], "screen_step", "Exact screen cadence required")
        _require(type(screen["outcomes"]) is list, "screen_outcomes", "Outcome list required")
        ids = [r.get("case_id") if type(r) is dict else None for r in screen["outcomes"]]
        _require(all(type(i) is str for i in ids) and len(set(ids)) == len(ids)
                 and set(ids).issubset({i for i, _ in required}), "screen_membership", "Duplicate/unexpected outcomes")
    except DurationPolicyError as exc:
        result["reasons"].append(exc.reason)
        result["ledger"] = [dict(case_id=i, role=role, status="not_assessed", reason=exc.reason) for i, role in required]
        return result
    baseline = {r["case_id"]: r for r in policy["baseline"]["cases"]}
    outcomes = {r["case_id"]: r for r in screen["outcomes"]}
    valid = []
    for case_id, role in required:
        row = outcomes.get(case_id)
        entry = dict(case_id=case_id, role=role, status="invalid", reason=None)
        try:
            _require(row is not None, "missing_outcome", "Required case missing")
            metrics = _row(row)
            _require(row["role"] == role, "case_role", "Protected selection role differs")
            if metrics is None:
                entry.update(status=row["status"], reason=row["reason"])
                result["reasons"].append("case_" + row["status"])
            else:
                b = baseline[case_id]["counts"]
                c = row["counts"]
                _require(sum(map(sum, c["confusion_matrix"])) == sum(map(sum, b["confusion_matrix"]))
                         and [sum(r) for r in c["confusion_matrix"]] == [sum(r) for r in b["confusion_matrix"]]
                         and c["voxel_volume_mm3"] == b["voxel_volume_mm3"]
                         and c["source_boundary_contact"] == b["source_boundary_contact"]
                         and [(v["component_id"], v["reference_voxels"]) for v in c["components"]]
                         == [(v["component_id"], v["reference_voxels"]) for v in b["components"]],
                         "reference_drift", "Native grid/reference component evidence changed")
                entry["status"] = "valid"
                result["per_case"][case_id] = dict(role=role, metrics=_plain(metrics),
                    components=[dict(component_id=v["component_id"], reference_voxels=v["reference_voxels"],
                                     true_positive=v["true_positive"], recall=v["true_positive"] / v["reference_voxels"])
                                for v in c["components"]], source_boundary_contact=c["source_boundary_contact"])
                if role == "train":
                    valid.append(row)
                else:
                    result["report_only"] = result["per_case"][case_id]
        except DurationPolicyError as exc:
            entry["reason"] = exc.reason
            result["reasons"].append(exc.reason)
        result["ledger"].append(entry)
    result["checks"]["completion"] = not result["reasons"]
    if result["reasons"]:
        return result  # No successful-subset aggregate is emitted.
    a = _aggregate(valid)
    b = _aggregate(policy["baseline"]["cases"][:6])
    result["aggregates"] = _plain(a)
    checks = result["checks"]
    checks["pancreas_tp_each"] = all(r["counts"]["confusion_matrix"][1][1] > 0 for r in valid)
    checks["pancreas_macro_recall"] = a["macro"]["pancreas_parenchyma"]["recall"] >= b["macro"]["pancreas_parenchyma"]["recall"] - Fraction(3, 100)
    checks["lesion_macro_recall"] = a["macro"]["lesion"]["recall"] >= max(Fraction(4, 5), b["macro"]["lesion"]["recall"] - Fraction(3, 100))
    for r in valid:
        case_id = r["case_id"]
        now, old = _fractions(r["counts"]), _fractions(baseline[case_id]["counts"])
        for name in ("pancreas_parenchyma", "lesion"):
            checks[f"{case_id}:{name}:recall"] = now[name]["recall"] >= max(0, old[name]["recall"] - Fraction(1, 10))
        for c, bc in zip(r["counts"]["components"], baseline[case_id]["counts"]["components"]):
            floor = max(0, Fraction(bc["true_positive"], bc["reference_voxels"]) - Fraction(1, 10))
            if case_id == policy["tiny_case_id"]:
                floor = max(floor, Fraction(19, 20))
            checks[f"{case_id}:component:{c['component_id']}"] = c["true_positive"] > 0 and Fraction(c["true_positive"], c["reference_voxels"]) >= floor
        checks[f"{case_id}:lesion:fp"] = now["lesion"]["false_positive_ml"] <= old["lesion"]["false_positive_ml"] * Fraction(5, 4)
    coverage_passed = all(checks.values())
    if terminal:
        for r in valid:
            case_id = r["case_id"]
            now, old = _fractions(r["counts"]), _fractions(baseline[case_id]["counts"])
            checks[f"{case_id}:terminal_lesion:fp"] = now["lesion"]["false_positive_ml"] <= old["lesion"]["false_positive_ml"] * Fraction(11, 10)
        checks["terminal_pancreas_dice"] = a["macro"]["pancreas_parenchyma"]["dice"] >= b["macro"]["pancreas_parenchyma"]["dice"]
        checks["terminal_lesion_dice"] = a["macro"]["lesion"]["dice"] >= b["macro"]["lesion"]["dice"] * Fraction(6, 5)
        checks["terminal_mean_lesion_fp"] = a["macro"]["lesion"]["false_positive_ml"] <= b["macro"]["lesion"]["false_positive_ml"] * Fraction(4, 5)
    result["passed"] = all(checks.values())
    result["decision"] = ("terminal_pass" if result["passed"] else "terminal_insufficient" if coverage_passed else "stopped") if terminal else ("continue" if coverage_passed else "stopped")
    result["reasons"] = [name for name, passed in checks.items() if not passed]
    return result
