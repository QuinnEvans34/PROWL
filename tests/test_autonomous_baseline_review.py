"""Contradictory saved reports must not silently become a successful baseline."""
from copy import deepcopy
import hashlib
import json

import pytest

from src.operations.autonomous_baseline_review_v1 import FAILURES, MAX_BYTES, read_bound, review
from scripts.diagnostics.review_autonomous_baseline import run, unit_dispositions

REQUEST, READY = "a" * 64, "b" * 64


def fixture():
    metric = dict(reference_voxels=0, predicted_voxels=2, true_positive=0,
                  dice=None, recall=None, false_positive_ml=0.002)
    component = dict(component_id=1, voxels=2, volume_ml=0.002, overlap_voxels=0,
                     any_overlap=False, overlap_fraction=0.)
    coverage = dict(reference_voxels=0, inside_voxels=0, outside_voxels=0, fraction=None)
    row = dict(disposition="COMPLETED", excluded=False, reused=False,
               source_report_sha256={k: "c" * 64 for k in ("score", "result", "input-access")},
               metrics={k: deepcopy(metric) for k in ("lesion", "pancreas_parenchyma", "pancreas_lesion_union")},
               role="exposed_development", model_quality_acceptance=False,
               lesion_reference_state="reference_empty", measurements=dict(voxel_volume_ml=.001),
               unknown_reference_units_assumed_mm=False, reference_units=["mm", "mm"],
               lesion_components=dict(connectivity=26, reference=[], predicted=[component],
                   detection_definition="any shared voxel, descriptive; not IoU threshold or clinical detection",
                   reference_count=0, reference_hit_count=0, false_positive_components=1),
               localization={k: deepcopy(coverage) for k in ("expanded_region_pancreas_coverage", "expanded_region_lesion_coverage")})
    rows = [dict(deepcopy(row), case_id=f"PanTS_{i:08d}", reused=i < 5) for i in range(63)]
    # One positive complete miss, plus 62 empty alarms. Undefined empty Dice stays null.
    first = rows[0]
    first["metrics"]["lesion"].update(reference_voxels=10, dice=0., recall=0.)
    first["lesion_reference_state"] = "positive"
    first["lesion_components"].update(reference=[dict(component_id=1, voxels=10,
        volume_ml=.01, overlap_voxels=0, any_overlap=False, overlap_fraction=0.)], reference_count=1)
    first["localization"]["expanded_region_lesion_coverage"].update(
        reference_voxels=10, inside_voxels=10, fraction=1.)
    rows.extend(dict(case_id=name, disposition=state, excluded=False, metrics=None, dice=None,
                     optimizer_updates=0, model_forwards=0, source_report_sha256={"failure": "d"*64})
                for name, state in FAILURES.items())
    return dict(schema="prowl.autonomous70.saved-closeout.v1",
        identities=dict(request_sha256=REQUEST, ready_sha256=READY, completion_sha256="e"*64),
        scope=dict(role="exposed_development", probability_equivalence="UNQUALIFIED", training=False,
                   model_quality_acceptance=False, hypothesis_verdict="NOT_TESTED", failed_cases_not_imputed=True),
        ordered_cases=rows,
        aggregate=dict(requested=70, completed=63, failed=7, excluded=0, reused=5, new_predictions=58,
            positive_reference_n=1, empty_reference_n=62, positive_macro_lesion_dice=0.,
            positive_any_overlap_n=0, empty_reference_alarm_n=62, reference_components_n=1,
            reference_components_hit_n=0, false_positive_components_n=63),
        verification=dict(evaluation_supervisor=dict(success=True, workers_reaped=True, exit_code=0),
            output_backup_pairs=710, preparation_backup_pairs=12, repository_pins_matched=294,
            backup_audit_receipt_sha256="f"*64))


def admit(document):
    return review(document, request_sha256=REQUEST, ready_sha256=READY)


def test_failures_empty_dice_and_review_queue_remain_distinct():
    result = admit(fixture())
    assert result["aggregate"]["positive_macro_lesion_dice"] == 0
    assert result["aggregate"]["requested"] == 70 and len(result["failures"]) == 7
    assert result["review_queues"]["missed_components"] == ["PanTS_00000000"]
    assert result["cases"][1]["dice"] is None
    assert result["image_review_performed"] is False
    assert result["scope"]["probability_equivalence"] == "UNQUALIFIED"


def test_mixed_saved_reference_units_are_flagged_without_repair():
    document = fixture()
    document["ordered_cases"][0].update(reference_units=["unknown", "mm"],
                                        unknown_reference_units_assumed_mm=True)
    result = admit(document)
    assert result["assumed_reference_unit_cases"] == 1
    assert result["cases"][0]["physical_units_assumed"] is True
    assert document["ordered_cases"][0]["reference_units"] == ["unknown", "mm"]
    report = unit_dispositions(result)
    assert report["requested"] == 70 and report["failures_by_case"] == FAILURES
    assert report["completed_by_reference_units"] == {
        "declared_mm": dict(completed=62, positive=0, reference_empty=62,
                            positive_with_overlap=0, reference_empty_with_alarm=62),
        "assumed_mm": dict(completed=1, positive=1, reference_empty=0,
                           positive_with_overlap=0, reference_empty_with_alarm=0),
    }


@pytest.mark.parametrize("mutation", [
    lambda d: d["ordered_cases"].pop(),
    lambda d: d["ordered_cases"][1].update(case_id="PanTS_00000000"),
    lambda d: d["ordered_cases"][-1].update(disposition="COMPLETED"),
    lambda d: d["ordered_cases"][-1].update(dice=0),
    lambda d: d["ordered_cases"][0]["metrics"]["lesion"].update(true_positive=11),
    lambda d: d["ordered_cases"][1]["metrics"]["lesion"].update(dice=0),
    lambda d: d["ordered_cases"][0]["lesion_components"].update(reference_hit_count=1),
    lambda d: d["ordered_cases"][0]["localization"]["expanded_region_lesion_coverage"].update(inside_voxels=9),
    lambda d: d["ordered_cases"][0].update(reference_units=["unknown", "unknown"]),
    lambda d: d["scope"].update(model_quality_acceptance=True),
    lambda d: d["identities"].update(ready_sha256="0"*64),
    lambda d: d["aggregate"].update(positive_macro_lesion_dice=.5),
    lambda d: d["verification"]["evaluation_supervisor"].update(workers_reaped=False),
])
def test_rejects_changed_cohort_scope_or_contradictory_evidence(mutation):
    document = fixture()
    mutation(document)
    with pytest.raises((ValueError, KeyError)):
        admit(document)


@pytest.mark.parametrize("payload", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b' '* (MAX_BYTES+1)])
def test_rejects_ambiguous_nonfinite_or_oversized_transfer(tmp_path, payload):
    path = tmp_path / "source.json"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        read_bound(path, hashlib.sha256(payload).hexdigest())


def test_cli_bound_hash_and_no_overwrite(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(fixture()))
    pin = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "review"
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        run(source, output, sha256="0"*64, request_sha256=REQUEST, ready_sha256=READY)
    assert not output.exists()
    run(source, output, sha256=pin, request_sha256=REQUEST, ready_sha256=READY)
    original = (output / "review.json").read_bytes()
    with pytest.raises(FileExistsError):
        run(source, output, sha256=pin, request_sha256=REQUEST, ready_sha256=READY)
    assert (output / "review.json").read_bytes() == original
    assert "undefined (empty reference)" in (output / "review.md").read_text()
