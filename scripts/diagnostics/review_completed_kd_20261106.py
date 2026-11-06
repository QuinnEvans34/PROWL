"""Describe the hash-bound, completed KD report without model or tracking writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean


REPORT_SHA256 = "2679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b"
STEPS = list(range(2000, 24001, 2000))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def summarize(raw: bytes) -> dict:
    require(hashlib.sha256(raw).hexdigest() == REPORT_SHA256, "Wrong completed report")
    report = json.loads(raw)
    require(report["status"] == "CLOSED_DESCRIPTIVE_ONLY", "Report not closed")
    require(report["execution_closeout_verified"] is True, "Closeout not verified")
    require(report["patient_independence"] == "unresolved", "Reassess inference policy")
    result = {
        "schema": "prowl.kd.descriptive-review.20261106.v1",
        "input_report_sha256": REPORT_SHA256,
        "scope": report["scope"],
        "independent_patient_inference": "withheld; patient linkage unresolved",
        "new_model_calls": 0,
        "new_optimizer_updates": 0,
        "mlflow_writes": 0,
        "series": [],
        "endpoints": {},
    }
    series = report["series_tracking"]
    for arm in ("control", "treatment"):
        require([x["step"] for x in series[arm]] == STEPS, "Incomplete validation series")
        require(report["completed_native_steps"][arm] == STEPS, "Step identity mismatch")
    for c, t in zip(series["control"], series["treatment"], strict=True):
        result["series"].append({"step": c["step"], "control": c["value"],
                                 "treatment": t["value"], "delta": t["value"] - c["value"],
                                 "control_run_id": c["run_id"], "treatment_run_id": t["run_id"]})
    expected_ids = None
    for name, endpoint in report["endpoints"].items():
        summaries = {}
        details = {}
        for arm in ("control", "treatment"):
            s = endpoint[arm]
            rows = s["cases_detail"]
            ids = {x["case_id"] for x in rows}
            require(len(rows) == len(ids) == 70, "Invalid/duplicate cohort members")
            if expected_ids is None:
                expected_ids = ids
            require(ids == expected_ids, "Endpoint cohort changed")
            positives = [x for x in rows if x["target_voxels"] > 0]
            require(len(positives) == 36, "Positive cohort changed")
            require(math.isclose(mean(x["dice"] for x in positives), s["positive_macro_dice"],
                                 abs_tol=1e-12, rel_tol=0), "Macro Dice does not reproduce")
            require(sum(x["false_positive"] for x in rows) == s["total_false_positive_voxels"],
                    "False-positive total does not reproduce")
            require(sum(x["false_negative"] for x in rows) == s["total_false_negative_voxels"],
                    "False-negative total does not reproduce")
            summaries[arm] = {k: v for k, v in s.items()
                              if k not in ("cases_detail", "bands", "patterns", "flags")}
            summaries[arm]["components_detected"] = sum(x["components_detected"] or 0 for x in rows)
            summaries[arm]["reference_components"] = sum(x["components"] or 0 for x in rows)
            summaries[arm]["complete_miss_ids"] = [x["case_id"] for x in positives if not x["case_detected"]]
            summaries[arm]["cases_missing_more_than_half_annotation"] = s["flags"]["more_than_half_annotation_missed"]
            summaries[arm]["size_bands"] = {
                band: {k: b[k] for k in ("cases", "positive_macro_dice", "positive_macro_recall")}
                for band, b in s["bands"].items()
            }
            details[arm] = {x["case_id"]: x for x in rows}
        paired = []
        for case_id in sorted(expected_ids):
            c, t = details["control"][case_id], details["treatment"][case_id]
            require(c["target_voxels"] == t["target_voxels"], "Reference volume mismatch")
            require(c["components"] == t["components"], "Reference component mismatch")
            if c["target_voxels"]:
                paired.append({"case_id": case_id, "control": c["dice"], "treatment": t["dice"],
                               "dice_delta": t["dice"] - c["dice"]})
        delta = mean(x["dice_delta"] for x in paired)
        require(math.isclose(delta, summaries["treatment"]["positive_macro_dice"] -
                             summaries["control"]["positive_macro_dice"], abs_tol=1e-12, rel_tol=0),
                "Paired delta does not reproduce")
        best_steps = {}
        for arm in ("control", "treatment"):
            best_steps[arm] = max(series[arm], key=lambda x: x["value"])["step"]
            expected_step = best_steps[arm] if name == "selected" else 24000
            require(summaries[arm]["step"] == expected_step, "Endpoint selection mismatch")
        result["endpoints"][name] = {
            "summaries": summaries, "positive_macro_dice_delta": delta,
            "better": sum(x["dice_delta"] > 0 for x in paired),
            "worse": sum(x["dice_delta"] < 0 for x in paired),
            "unchanged": sum(x["dice_delta"] == 0 for x in paired),
            "largest_gains": sorted(paired, key=lambda x: x["dice_delta"], reverse=True)[:5],
            "largest_declines": sorted(paired, key=lambda x: x["dice_delta"])[:5],
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.report.read_bytes())
    # Exclusive creation: never overwrite an earlier review or producing artifact.
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "endpoints": list(result["endpoints"]),
                      "validation_pairs": len(result["series"])}))


if __name__ == "__main__":
    main()
