"""Derive interim errors from saved native counts; no model, array or tracking access."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import mean

SCHEMA = "prowl-stunet-saved-native-metadata-v1"
ARTIFACT = "pants_stunet_base_transfer_12k_20261106_launch02"
READY = "59e8188d60d70840eabb8752f0be5d5c1f818bc51e3cdcf81d16c74c79cf3e68"
NATIVE_PRODUCER = "6e02fa0da2db3af02bb76b2caff2e498e5ec9b104bc057b7863907e9ed1eb85a"
MAX_BYTES = 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value):
    return type(value) is int and value >= 0


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def close(a, b):
    return finite(a) and finite(b) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)


def digest(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def determinant(matrix):
    a, b, c = [row[:3] for row in matrix[:3]]
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0]))


def voxel_counts(value, capacity):
    n, p, tp = [value[k] for k in ("target_voxels", "predicted_voxels", "true_positive")]
    require(all(integer(x) and x <= capacity for x in (n, p, tp)) and tp <= min(n, p),
            "Invalid overlap counts")
    expected = 2 * tp / (n + p) if n + p else None
    require(value["dice"] is None if expected is None else close(value["dice"], expected),
            "Saved Dice does not reproduce; empty/empty must be null")
    return n, p, tp


def derived_row(row, identity):
    require(row["scope"] == "provided_pancreas_region_exploratory" and row["gaps"] == 0,
            "Wrong scope or incomplete native coverage")
    require(row["tiles"] == identity["profile"]["tiles"] and integer(row["tiles"]) and row["tiles"] > 0,
            "Tile identity changed")
    m = row["metrics"]
    capacity = math.prod(identity["native_shape"])
    voxel_counts(m["pancreas"], capacity)
    n, p, tp = voxel_counts(m["lesion"], capacity)
    require(type(m["reference_positive"]) is bool and m["reference_positive"] == (n > 0),
            "Reference positivity mismatch")
    require(type(m["case_detected"]) is bool and m["case_detected"] == (tp > 0), "Detection mismatch")
    require(type(m["false_alarm_any"]) is bool and m["false_alarm_any"] == (n == 0 and p > 0),
            "Empty alarm mismatch")
    components, hit, predicted = [m[k] for k in
                                 ("reference_components", "detected_components", "predicted_components")]
    require(all(integer(x) for x in (components, hit, predicted))
            and hit <= components <= n and predicted <= p
            and (components > 0) == (n > 0) and (predicted > 0) == (p > 0)
            and (hit > 0) == (tp > 0), "Invalid component counts")
    volume = m["voxel_mm3"]
    require(finite(volume) and volume > 0 and close(volume, abs(determinant(identity["native_affine"]))),
            "Native voxel geometry mismatch")
    require(close(m["target_volume_mm3"], n * volume) and close(m["predicted_volume_mm3"], p * volume),
            "Saved physical volume mismatch")
    band = "empty" if not n else "small" if n * volume < 1000 else "medium" if n * volume <= 10000 else "large"
    require(m["size_band"] == band, "Size band differs from pinned producer")
    require(type(m["case_alert_50mm3"]) is bool and m["case_alert_50mm3"] == (p * volume >= 50),
            "Separate 50mm3 alert mismatch")
    return {
        "case_id": row["case_id"], "size_band": band, "target_voxels": n,
        "predicted_voxels": p, "overlap_voxels": tp, "dice": m["lesion"]["dice"],
        "recall": tp / n if n else None, "precision": tp / p if p else None,
        "false_positive_voxels": p - tp, "false_negative_voxels": n - tp,
        "false_positive_mL": (p - tp) * volume / 1000,
        "false_negative_mL": (n - tp) * volume / 1000,
        "reference_components": components, "overlapped_reference_components": hit,
        "missed_reference_components": components - hit,
        "predicted_reference_volume_ratio": p / n if n else None,
        "target_volume_mm3": n * volume,
    }


def aggregate(rows):
    positive = [r for r in rows if r["target_voxels"] > 0]
    empty = [r for r in rows if r["target_voxels"] == 0]
    precision = [r["precision"] for r in positive if r["precision"] is not None]
    return {
        "cases": len(rows), "positive_cases": len(positive), "empty_cases": len(empty),
        "positive_macro_dice": mean(r["dice"] for r in positive) if positive else None,
        "positive_macro_recall": mean(r["recall"] for r in positive) if positive else None,
        "positive_macro_precision_defined": mean(precision) if precision else None,
        "precision_defined_positive_cases": len(precision),
        "detected_positive_cases": sum(r["overlap_voxels"] > 0 for r in positive),
        "empty_alarm_cases": sum(r["predicted_voxels"] > 0 for r in empty),
        "reference_components": sum(r["reference_components"] for r in rows),
        "overlapped_reference_components": sum(r["overlapped_reference_components"] for r in rows),
        "missed_reference_components": sum(r["missed_reference_components"] for r in rows),
        "positive_false_positive_voxels": sum(r["false_positive_voxels"] for r in positive),
        "empty_false_positive_voxels": sum(r["false_positive_voxels"] for r in empty),
        "false_negative_voxels": sum(r["false_negative_voxels"] for r in rows),
        "false_positive_mL": sum(r["false_positive_mL"] for r in rows),
        "false_negative_mL": sum(r["false_negative_mL"] for r in rows),
        "positive_cases_recall_below_half": sum(r["recall"] < .5 for r in positive),
        "positive_cases_predicted_volume_at_least_2x_reference": sum(
            r["predicted_reference_volume_ratio"] >= 2 for r in positive),
    }


def summarize(raw, expected_sha256):
    require(len(raw) <= MAX_BYTES, "Export exceeds metadata byte limit")
    require(digest(expected_sha256) and hashlib.sha256(raw).hexdigest() == expected_sha256,
            "Wrong native export SHA256")
    p = json.loads(raw)
    require(p["schema"] == SCHEMA and p["artifact_id"] == ARTIFACT and p["ready_sha256"] == READY
            and p["mlflow_run_id"] == "243ccf3f71c34417be60362af35187d1", "Wrong experiment identity")
    require(p["metric_producer_pins_as_recorded"]["src\\training\\pants_native_evaluation.py"] == NATIVE_PRODUCER,
            "Metric producer changed")
    identities = {r["case_id"]: r for r in p["case_identities_from_frozen_inputs"]}
    require(len(identities) == len(p["case_identities_from_frozen_inputs"]) == 70,
            "Invalid identity membership")
    for name, identity in identities.items():
        require(re.fullmatch(r"PanTS_\d{8}", name) is not None, "Invalid alias")
        require(set(identity["source_sha256"]) == {"ct", "pancreas", "lesion"}
                and all(digest(x) for x in identity["source_sha256"].values()), "Missing source identities")
        require(len(identity["native_shape"]) == 3
                and all(integer(x) and x > 0 for x in identity["native_shape"]), "Invalid native shape")
        affine = identity["native_affine"]
        require(len(affine) == 4 and all(len(row) == 4 and all(finite(x) for x in row) for row in affine)
                and affine[3] == [0, 0, 0, 1], "Invalid native affine")
    reports = p["reports"]
    require(1 <= len(reports) <= 6 and [r["step"] for r in reports] == list(range(2000, 2000 * len(reports) + 1, 2000)),
            "Incomplete or unordered validation sequence")
    result = {
        "schema": "prowl.stunet.interim-error-review.v1", "status": "INTERIM_DESCRIPTIVE_ONLY",
        "source_export_sha256": expected_sha256, "observed_at": p["observed_at"],
        "artifact_id": ARTIFACT, "ready_sha256": READY, "scope": p["scope"],
        "new_model_calls": 0, "new_optimizer_updates": 0, "mlflow_writes": 0,
        "derived_not_originally_stored": ["recall=overlap/target", "precision=overlap/predicted; null if no prediction",
            "FP=predicted-overlap", "FN=target-overlap", "missed components=reference-overlapped"],
        "producer_definitions": {"source_sha256": NATIVE_PRODUCER, "components": "26-connected; any-overlap reference hits",
            "size_bands": "total reference lesion volume: small<1000mm3; medium<=10000mm3; large>10000mm3; not per-component size",
            "units": p["input_units_policy"]},
        "cross_model_reference_equivalence": "not established for both final KD arms; no cross-model deltas",
        "independent_patient_inference": "withheld; patient/pretraining linkage unresolved",
        "spatial_causes": "not established by overlap counts; no contours/images reviewed here",
        "series": [], "within_run_changes": [],
    }
    reference = None
    previous = None
    for report in reports:
        step = report["step"]
        require(report["report_name"] == f"native-{step:05d}.json" and digest(report["report_sha256"])
                and p["source_json_sha256"][report["report_name"]] == report["report_sha256"]
                and report["independent_report_backup_matches"] is True, "Report receipt mismatch")
        checkpoint = report["checkpoint"]
        require(checkpoint["name"] == f"checkpoint-{step:05d}.pt"
                and digest(checkpoint["sha256_from_saved_journal"])
                and integer(checkpoint["bytes"]) and checkpoint["bytes"] > 0
                and checkpoint["checkpoint_bytes_not_read"] is True, "Checkpoint receipt mismatch")
        originals = report["cases_as_saved"]
        require(len(originals) == len({r["case_id"] for r in originals}) == 70
                and {r["case_id"] for r in originals} == identities.keys(), "Incomplete/duplicate native cohort")
        rows = [derived_row(r, identities[r["case_id"]]) for r in originals]
        refs = {r["case_id"]: (r["metrics"]["pancreas"]["target_voxels"], r["metrics"]["lesion"]["target_voxels"],
                               r["metrics"]["reference_components"]) for r in originals}
        require(reference is None or reference == refs, "Native reference changed across validations")
        reference = refs
        total = aggregate(rows)
        require(report["denominators"] == {"all_cases": 70, "positive_cases": 36, "empty_cases": 34, "reference_components": 45}
                and total["positive_cases"] == 36 and total["empty_cases"] == 34
                and total["reference_components"] == 45, "Wrong complete validation denominators")
        saved = report["summary_as_saved"]
        require(close(saved["lesion_dice"], total["positive_macro_dice"])
                and saved["positive"] == 36 and saved["empty"] == 34
                and saved["detected"] == total["detected_positive_cases"]
                and saved["alarms"] == total["empty_alarm_cases"], "Saved summary does not reproduce")
        bands = {band: aggregate([r for r in rows if r["size_band"] == band])
                 for band in ("small", "medium", "large", "empty")}
        misses = sorted(r["case_id"] for r in rows if r["target_voxels"] and not r["overlap_voxels"])
        result["series"].append({"step": step, "report_sha256": report["report_sha256"],
            "checkpoint_sha256_from_peer_journal": checkpoint["sha256_from_saved_journal"],
            "summary": total, "size_bands": bands, "complete_miss_ids": misses, "cases": rows})
        if previous:
            before = {r["case_id"]: r for r in previous["cases"]}
            changes = [{"case_id": r["case_id"], "dice_delta": r["dice"] - before[r["case_id"]]["dice"]}
                       for r in rows if r["target_voxels"]]
            result["within_run_changes"].append({"from_step": previous["step"], "to_step": step,
                "better": sum(r["dice_delta"] > 0 for r in changes),
                "worse": sum(r["dice_delta"] < 0 for r in changes),
                "unchanged": sum(r["dice_delta"] == 0 for r in changes),
                "new_complete_misses": sorted(set(misses) - set(previous["complete_miss_ids"])),
                "recovered_complete_misses": sorted(set(previous["complete_miss_ids"]) - set(misses)),
                "largest_gains": sorted(changes, key=lambda r: (-r["dice_delta"], r["case_id"]))[:5],
                "largest_declines": sorted(changes, key=lambda r: (r["dice_delta"], r["case_id"]))[:5]})
        previous = result["series"][-1]
    result["persistent_complete_misses"] = sorted(set.intersection(*(set(r["complete_miss_ids"]) for r in result["series"])))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "Preserve existing review; use a fresh output")
    with args.export.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    result = summarize(raw, args.sha256)
    require(args.export.read_bytes() == raw, "Export changed during review")
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    with args.output.open("x") as stream:
        stream.write(encoded)
    print(json.dumps({"output": str(args.output), "status": result["status"],
                      "validations": len(result["series"]), "cases_per_validation": 70}))


if __name__ == "__main__":
    main()
