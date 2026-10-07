"""Invented integer oracles; no experiment, image, weight or dataset dependency."""
from copy import deepcopy
from fractions import Fraction
import json

import pytest

from src.training import segmenter_duration_policy_v1 as policy


TRAIN = [f"invented-{i}" for i in range(6)]
REPORT = "invented-report"


def row(case_id, role="train", *, fp=100, lesion_tp=100, pancreas_tp=100):
    return dict(case_id=case_id, role=role, status="valid", reason=None, reported_metrics=None,
                counts=dict(confusion_matrix=[[800 - fp, 100, fp], [100 - pancreas_tp, pancreas_tp, 0],
                                               [100 - lesion_tp, 0, lesion_tp]],
                            components=[dict(component_id=1, reference_voxels=100, true_positive=lesion_tp)],
                            voxel_volume_mm3=12., source_boundary_contact=case_id == TRAIN[1]))


def baseline():
    return dict(schema_version="1.0.0", kind=policy.BASELINE_KIND,
                cases=[row(i) for i in TRAIN] + [row(REPORT, "report_only")])


def controls(b=None):
    b = baseline() if b is None else b
    p = policy.build_policy(b, trusted_baseline_sha256=policy.record_digest(b),
                            tiny_case_id=TRAIN[0], boundary_case_id=TRAIN[1])
    return p, policy.record_digest(p)


def screen(p, pin, *, step=48, fp=100):
    rows = [row(i, fp=fp) for i in TRAIN]
    if step == 192:
        rows.append(row(REPORT, "report_only"))
    return dict(schema_version="1.0.0", policy_sha256=pin, baseline_sha256=p["baseline_sha256"],
                step=step, outcomes=rows)


def assess(p, pin, s):
    return policy.assess_screen(p, s, trusted_policy_sha256=pin)


def test_independent_class_union_and_anisotropic_volume_oracle():
    p, pin = controls(); out = assess(p, pin, screen(p, pin))
    m = out["per_case"][TRAIN[0]]["metrics"]
    # Authored matrix: pancreas TP100/ref100/pred200; lesion same;
    # union TP200/ref200/pred400. FP100*2*2*3mm3/1000 =1.2mL/class.
    for name in ("pancreas_parenchyma", "lesion", "pancreas_lesion_union"):
        assert m[name]["dice"] == float(Fraction(2, 3))
        assert m[name]["recall"] == 1
        assert m[name]["precision"] == .5
    assert m["lesion"]["false_positive_ml"] == 1.2
    assert m["pancreas_lesion_union"]["false_positive_ml"] == 2.4
    assert out["aggregates"]["pooled"]["lesion"]["target_voxels"] == 600
    assert out["aggregates"]["pooled"]["lesion"]["false_positive_ml"] == 7.2
    assert out["decision"] == "continue"


def test_192_cadence_and_equal_expected_exposures_are_not_execution_authority():
    p, pin = controls(); plan = policy.cadence_plan(p, trusted_policy_sha256=pin)
    assert [r["step"] for r in plan] == [0, 48, 96, 144, 192]
    assert [r["expected_exposures_per_train_case"] for r in plan] == [0, 8, 16, 24, 32]
    assert [r["step"] for r in plan if r["native_screen"]] == [48, 96, 144, 192]
    assert [r["step"] for r in plan if r["report_only"]] == [192]
    assert p["execution_authority"] is False


@pytest.mark.parametrize("step", [0, 6, 24, 49, 193, 240, True, 48.0])
def test_no_off_cadence_or_later_checkpoint_selection(step):
    p, pin = controls(); out = assess(p, pin, screen(p, pin, step=step))
    assert out["decision"] == "stopped" and out["reasons"] == ["screen_step"]


@pytest.mark.parametrize("fp,expected", [(124, True), (125, True), (126, False)])
def test_exact_interim_fp_growth_limit(fp, expected):
    p, pin = controls(); out = assess(p, pin, screen(p, pin, fp=fp))
    assert out["checks"][f"{TRAIN[0]}:lesion:fp"] is expected
    assert out["decision"] == ("continue" if expected else "stopped")


@pytest.mark.parametrize("fp,expected", [(49, True), (50, True), (51, False)])
def test_exact_terminal_dice_gain_uses_rational_comparison(fp, expected):
    p, pin = controls(); out = assess(p, pin, screen(p, pin, step=192, fp=fp))
    # Base Dice2/3; 20% gain gives4/5. TP100, pred150 at FP50 yields4/5.
    assert out["checks"]["terminal_lesion_dice"] is expected
    assert out["decision"] == ("terminal_pass" if expected else "terminal_insufficient")


@pytest.mark.parametrize("fp,expected", [(79, True), (80, True), (81, False)])
def test_exact_terminal_mean_fp_reduction(fp, expected):
    p, pin = controls(); out = assess(p, pin, screen(p, pin, step=192, fp=fp))
    assert out["checks"]["terminal_mean_lesion_fp"] is expected
    assert out["decision"] == "terminal_insufficient"  # Dice target still not met.


@pytest.mark.parametrize("fp,expected", [(110, True), (111, False)])
def test_terminal_one_case_cannot_hide_fp_growth_in_a_good_mean(fp, expected):
    p, pin = controls(); s = screen(p, pin, step=192, fp=40)
    s["outcomes"][2] = row(TRAIN[2], fp=fp)
    out = assess(p, pin, s)
    assert out["checks"]["terminal_mean_lesion_fp"] is True
    assert out["checks"][f"{TRAIN[2]}:terminal_lesion:fp"] is expected
    assert out["decision"] == ("terminal_pass" if expected else "terminal_insufficient")


@pytest.mark.parametrize("class_name", ["pancreas_parenchyma", "lesion"])
@pytest.mark.parametrize("extra_loss,expected", [(0, True), (1, False)])
def test_exact_three_percentage_point_macro_recall_allowance(class_name, extra_loss, expected):
    p, pin = controls(); s = screen(p, pin)
    for i in (2, 3, 4):
        kwargs = {"pancreas_tp" if class_name == "pancreas_parenchyma" else "lesion_tp": 94}
        s["outcomes"][i] = row(TRAIN[i], **kwargs)
    kwargs = {"pancreas_tp" if class_name == "pancreas_parenchyma" else "lesion_tp": 94 - extra_loss}
    s["outcomes"][4] = row(TRAIN[4], **kwargs)
    out = assess(p, pin, s)
    key = "pancreas_macro_recall" if class_name == "pancreas_parenchyma" else "lesion_macro_recall"
    assert out["checks"][key] is expected


@pytest.mark.parametrize("tp,expected", [(90, True), (89, False)])
@pytest.mark.parametrize("class_name", ["pancreas_parenchyma", "lesion"])
def test_case_recall_floor_even_when_macro_passes(tp, expected, class_name):
    p, pin = controls(); s = screen(p, pin)
    kwargs = {"pancreas_tp" if class_name == "pancreas_parenchyma" else "lesion_tp": tp}
    s["outcomes"][2] = row(TRAIN[2], **kwargs)
    out = assess(p, pin, s)
    assert out["checks"][f"{TRAIN[2]}:{class_name}:recall"] is expected
    assert out["checks"]["pancreas_macro_recall" if class_name == "pancreas_parenchyma" else "lesion_macro_recall"] is True


@pytest.mark.parametrize("tp,expected", [(96, True), (95, True), (94, False)])
def test_tiny_component_override(tp, expected):
    p, pin = controls(); s = screen(p, pin); s["outcomes"][0] = row(TRAIN[0], lesion_tp=tp)
    out = assess(p, pin, s)
    assert out["checks"]["lesion_macro_recall"] is True
    assert out["checks"][f"{TRAIN[0]}:component:1"] is expected


def test_multiple_component_recall_cannot_be_hidden_by_case_recall():
    b = baseline(); b["cases"][2]["counts"]["components"] = [
        dict(component_id=1, reference_voxels=80, true_positive=80),
        dict(component_id=2, reference_voxels=20, true_positive=20)]
    p, pin = controls(b); s = screen(p, pin); r = row(TRAIN[2], lesion_tp=90)
    r["counts"]["components"] = [dict(component_id=1, reference_voxels=80, true_positive=73),
                                   dict(component_id=2, reference_voxels=20, true_positive=17)]
    s["outcomes"][2] = r; out = assess(p, pin, s)
    assert out["checks"][f"{TRAIN[2]}:lesion:recall"] is True
    assert out["checks"][f"{TRAIN[2]}:component:2"] is False
    assert out["decision"] == "stopped"


def test_empty_positive_prediction_is_zero_and_stops_without_omission():
    p, pin = controls(); s = screen(p, pin); s["outcomes"][2] = row(TRAIN[2], fp=0, lesion_tp=0)
    out = assess(p, pin, s); m = out["per_case"][TRAIN[2]]["metrics"]["lesion"]
    assert m["dice"] == m["recall"] == m["precision"] == 0
    assert out["aggregates"]["case_count"] == 6
    assert out["decision"] == "stopped"


@pytest.mark.parametrize("status", ["failed", "empty", "abstained"])
def test_explicit_failure_retains_ledger_and_null_aggregate(status):
    p, pin = controls(); s = screen(p, pin)
    s["outcomes"][2].update(status=status, reason="invented fault", counts=None)
    out = assess(p, pin, s)
    assert out["decision"] == "stopped" and len(out["ledger"]) == 6
    assert out["ledger"][2]["status"] == status and out["aggregates"] is None


def test_report_quality_changes_do_not_change_train_selection():
    p, pin = controls(); a = screen(p, pin, step=192, fp=50); b = deepcopy(a)
    b["outcomes"][-1] = row(REPORT, "report_only", fp=0, lesion_tp=0, pancreas_tp=0)
    first, second = assess(p, pin, a), assess(p, pin, b)
    assert first["decision"] == second["decision"] == "terminal_pass"
    assert first["checks"] == second["checks"] and first["aggregates"] == second["aggregates"]
    assert second["report_only"]["metrics"]["lesion"]["dice"] == 0


@pytest.mark.parametrize("fault", ["missing", "failed", "wrong_role"])
def test_terminal_report_completion_is_required(fault):
    p, pin = controls(); s = screen(p, pin, step=192, fp=50)
    if fault == "missing": s["outcomes"].pop()
    elif fault == "failed": s["outcomes"][-1].update(status="failed", reason="fault", counts=None)
    else: s["outcomes"][-1]["role"] = "train"
    out = assess(p, pin, s)
    assert out["decision"] == "stopped" and len(out["ledger"]) == 7 and out["aggregates"] is None


@pytest.mark.parametrize("fault", ["missing", "duplicate", "unexpected", "report_interim", "wrong_role", "extra_field", "pin", "baseline_pin"])
def test_requested_membership_role_and_lineage_faults(fault):
    p, pin = controls(); s = screen(p, pin)
    if fault == "missing": s["outcomes"].pop()
    elif fault == "duplicate": s["outcomes"].append(deepcopy(s["outcomes"][0]))
    elif fault == "unexpected": s["outcomes"][0]["case_id"] = "unrequested"
    elif fault == "report_interim": s["outcomes"].append(row(REPORT, "report_only"))
    elif fault == "wrong_role": s["outcomes"][0]["role"] = "report_only"
    elif fault == "extra_field": s["path"] = "no file interface"
    elif fault == "pin": s["policy_sha256"] = "0" * 64
    else: s["baseline_sha256"] = "0" * 64
    out = assess(p, pin, s)
    assert out["decision"] == "stopped" and out["aggregates"] is None


@pytest.mark.parametrize("fault", ["bool", "negative", "float_count", "nan", "infinite", "huge_volume", "zero_volume", "wrong_components", "duplicate_component", "reference", "volume", "boundary", "summary", "unknown_count_field"])
def test_invalid_counts_and_reference_drift_stop(fault):
    p, pin = controls(); s = screen(p, pin); c = s["outcomes"][2]["counts"]
    if fault == "bool": c["confusion_matrix"][0][0] = True
    elif fault == "negative": c["confusion_matrix"][0][0] = -1
    elif fault == "float_count": c["confusion_matrix"][0][0] = 700.0
    elif fault == "nan": c["voxel_volume_mm3"] = float("nan")
    elif fault == "infinite": c["voxel_volume_mm3"] = float("inf")
    elif fault == "huge_volume": c["voxel_volume_mm3"] = 10**400
    elif fault == "zero_volume": c["voxel_volume_mm3"] = 0
    elif fault == "wrong_components": c["components"][0]["true_positive"] = 99
    elif fault == "duplicate_component": c["components"].append(deepcopy(c["components"][0]))
    elif fault == "reference":
        c["confusion_matrix"][0][0] -= 1; c["confusion_matrix"][1][1] += 1
    elif fault == "volume": c["voxel_volume_mm3"] = 13
    elif fault == "boundary": c["source_boundary_contact"] = True
    elif fault == "summary": s["outcomes"][2]["reported_metrics"] = {"dice": 1}
    else: c["reference_path"] = "not allowed"
    out = assess(p, pin, s)
    assert out["decision"] == "stopped" and out["aggregates"] is None
    assert out["ledger"][2]["status"] == "invalid"


@pytest.mark.parametrize("fault", ["terminal", "rule", "permission", "bool_terminal", "baseline", "extra"])
def test_policy_drift_refuses_even_with_new_self_pin(fault):
    p, _ = controls()
    if fault == "terminal": p["terminal_step"] = 96
    elif fault == "rule": p["rules"]["macro_recall_loss"] = .5
    elif fault == "permission": p["execution_authority"] = True
    elif fault == "bool_terminal": p["checkpoint_steps"][0] = False
    elif fault == "baseline": p["baseline"]["cases"][0]["counts"]["confusion_matrix"][0][0] += 1
    else: p["new_recipe"] = "not approved"
    with pytest.raises(policy.DurationPolicyError):
        policy.validate_policy(p, trusted_policy_sha256=policy.record_digest(p))


def test_independent_pin_and_immutable_json_roundtrip():
    b = baseline(); original = deepcopy(b); p, pin = controls(b)
    s = screen(p, pin, step=192, fp=50); saved = deepcopy(s); pp = deepcopy(p)
    assert assess(p, pin, s) == assess(json.loads(json.dumps(p)), pin, json.loads(json.dumps(s)))
    assert b == original and p == pp and s == saved
    b["cases"][0]["case_id"] = "mutated caller"
    assert p == pp
    with pytest.raises(policy.DurationPolicyError, match="policy_pin"):
        assess(p, "0" * 64, s)


def test_zero_baseline_fp_requires_zero_candidate_fp():
    b = baseline()
    for r in b["cases"]:
        r["counts"]["confusion_matrix"][0] = [900, 0, 0]
    p, pin = controls(b); s = screen(p, pin)
    s["outcomes"] = deepcopy(b["cases"][:6])
    assert assess(p, pin, s)["decision"] == "continue"
    s["outcomes"][2]["counts"]["confusion_matrix"][0] = [899, 0, 1]
    assert assess(p, pin, s)["decision"] == "stopped"


def test_pancreas_dice_must_not_decline_even_when_lesion_targets_pass():
    p, pin = controls(); s = screen(p, pin, step=192, fp=50)
    for r in s["outcomes"][:6]:
        r["counts"]["confusion_matrix"][0] = [749, 101, 50]
    out = assess(p, pin, s)
    assert out["checks"]["terminal_lesion_dice"] is True
    assert out["checks"]["terminal_pancreas_dice"] is False
    assert out["decision"] == "terminal_insufficient"


def test_macro_and_pooled_recall_have_distinct_denominators():
    b = baseline(); c = b["cases"][2]["counts"]
    c["confusion_matrix"] = [[2 * v for v in r] for r in c["confusion_matrix"]]
    c["components"][0].update(reference_voxels=200, true_positive=200)
    p, pin = controls(b); s = screen(p, pin); s["outcomes"] = deepcopy(b["cases"][:6])
    s["outcomes"][2]["counts"]["confusion_matrix"][2] = [100, 0, 100]
    s["outcomes"][2]["counts"]["components"][0]["true_positive"] = 100
    out = assess(p, pin, s)
    assert out["aggregates"]["macro"]["lesion"]["recall"] == float(Fraction(11, 12))
    assert out["aggregates"]["pooled"]["lesion"]["recall"] == float(Fraction(6, 7))
    assert out["decision"] == "stopped"


def test_zero_tp_component_still_fails_when_its_baseline_recall_was_zero():
    b = baseline(); b["cases"][2] = row(TRAIN[2], lesion_tp=0)
    p, pin = controls(b); s = screen(p, pin); s["outcomes"][2] = row(TRAIN[2], lesion_tp=0)
    out = assess(p, pin, s)
    assert out["checks"]["lesion_macro_recall"] is True
    assert out["checks"][f"{TRAIN[2]}:component:1"] is False


def test_positive_pancreas_tp_is_required_even_with_a_zero_tp_baseline():
    b = baseline(); b["cases"][2] = row(TRAIN[2], pancreas_tp=0)
    p, pin = controls(b); s = screen(p, pin); s["outcomes"][2] = row(TRAIN[2], pancreas_tp=0)
    out = assess(p, pin, s)
    assert out["checks"]["pancreas_macro_recall"] is True
    assert out["checks"]["pancreas_tp_each"] is False


def test_reported_summaries_accept_exact_arithmetic_and_reject_boolean_aliases():
    p, pin = controls(); s = screen(p, pin)
    s["outcomes"][2]["reported_metrics"] = assess(p, pin, s)["per_case"][TRAIN[2]]["metrics"]
    assert assess(p, pin, s)["decision"] == "continue"
    s["outcomes"][2]["reported_metrics"]["lesion"]["recall"] = True
    assert assess(p, pin, s)["ledger"][2]["reason"] == "reported_metrics"


def test_lesion_macro_absolute_point_eight_floor_is_not_relaxed():
    b = baseline()
    for i in range(1, 6): b["cases"][i] = row(TRAIN[i], lesion_tp=70)
    p, pin = controls(b); s = screen(p, pin); s["outcomes"] = deepcopy(b["cases"][:6])
    out = assess(p, pin, s)
    assert out["checks"]["lesion_macro_recall"] is False


@pytest.mark.parametrize("value", [None, [], {"step": 48}])
def test_malformed_screen_returns_a_complete_failure_ledger(value):
    p, pin = controls(); out = assess(p, pin, value)
    assert out["decision"] == "stopped" and len(out["ledger"]) == 6
    assert out["aggregates"] is None


def test_baseline_membership_refusal_and_boundary_marker_refusal():
    b = baseline(); b["cases"][-1]["role"] = "train"
    with pytest.raises(policy.DurationPolicyError, match="baseline_membership"):
        controls(b)
    b = baseline(); b["cases"][1]["counts"]["source_boundary_contact"] = False
    with pytest.raises(policy.DurationPolicyError, match="case_markers"):
        controls(b)
