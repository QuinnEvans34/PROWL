"""CPU-only admission and descriptive review of the saved autonomous70 export.

This verifies transferred metadata, not the unavailable CTs or Windows backups.
It does not qualify numerical equivalence or produce a model acceptance verdict.
"""
import hashlib
import json
import math
import re
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
FAILURES = {
    **{f"PanTS_{n:08d}": "SOURCE_UNIT_ADMISSION_FAILURE"
       for n in (6011, 5780, 1823, 2935, 6901, 6115)},
    "PanTS_00005592": "PREFLIGHT_RESOURCE_LIMIT",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)


def integer(value):
    return type(value) is int and value >= 0


def equal_number(actual, expected):
    if expected is None:
        return actual is None
    return (type(actual) in (int, float) and math.isfinite(actual)
            and math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def finite_tree(value):
    if isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)
    elif isinstance(value, float):
        require(math.isfinite(value), "Nonfinite JSON number")


def read_bound(path, expected_sha256):
    require(digest(expected_sha256), "Explicit export SHA256 required")
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, "Export exceeds metadata size limit")
    require(hashlib.sha256(data).hexdigest() == expected_sha256, "Export SHA256 mismatch")
    def reject_constant(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    document = json.loads(data, object_pairs_hook=unique_object, parse_constant=reject_constant)
    finite_tree(document)
    return document


def check_metric(metric, volume):
    n, p, tp = (metric[k] for k in ("reference_voxels", "predicted_voxels", "true_positive"))
    require(all(integer(x) for x in (n, p, tp)) and tp <= min(n, p), "Impossible voxel counts")
    require(equal_number(metric["dice"], 2 * tp / (n + p) if n else None), "Dice/count disagreement")
    require(equal_number(metric["recall"], tp / n if n else None), "Recall/count disagreement")
    require(equal_number(metric["false_positive_ml"], (p - tp) * volume), "FP volume/count disagreement")
    return n, p, tp


def check_components(components, n, p, tp, volume):
    require(components["connectivity"] == 26, "Unexpected component connectivity")
    require(components["detection_definition"] == "any shared voxel, descriptive; not IoU threshold or clinical detection",
            "Component overlap semantics changed")
    for side, count in (("reference", n), ("predicted", p)):
        items = components[side]
        require([x["component_id"] for x in items] == list(range(1, len(items) + 1)), "Component identities")
        for x in items:
            require(integer(x["voxels"]) and x["voxels"] > 0
                    and integer(x["overlap_voxels"]) and x["overlap_voxels"] <= x["voxels"], "Component counts")
            require(type(x["any_overlap"]) is bool and x["any_overlap"] == (x["overlap_voxels"] > 0), "Component overlap flag")
            require(equal_number(x["overlap_fraction"], x["overlap_voxels"] / x["voxels"])
                    and equal_number(x["volume_ml"], x["voxels"] * volume), "Component arithmetic")
        require(sum(x["voxels"] for x in items) == count
                and sum(x["overlap_voxels"] for x in items) == tp, "Component/voxel totals")
    reference, predicted = components["reference"], components["predicted"]
    hits = sum(x["any_overlap"] for x in reference)
    fp = sum(not x["any_overlap"] for x in predicted)
    require(components["reference_count"] == len(reference)
            and components["reference_hit_count"] == hits
            and components["false_positive_components"] == fp, "Component summary disagreement")
    return len(reference), hits, fp


def check_coverage(item):
    n, inside, outside = (item[k] for k in ("reference_voxels", "inside_voxels", "outside_voxels"))
    require(all(integer(x) for x in (n, inside, outside)) and inside + outside == n, "Coverage counts")
    require(equal_number(item["fraction"], inside / n if n else None), "Coverage fraction")
    return n, outside


def review(document, *, request_sha256, ready_sha256):
    require(document["schema"] == "prowl.autonomous70.saved-closeout.v1", "Unknown saved-report schema")
    identities = document["identities"]
    require(digest(request_sha256) and digest(ready_sha256)
            and identities["request_sha256"] == request_sha256
            and identities["ready_sha256"] == ready_sha256
            and digest(identities["completion_sha256"]), "Report/launch identity mismatch")
    scope = document["scope"]
    require(scope["role"] == "exposed_development" and scope["probability_equivalence"] == "UNQUALIFIED"
            and scope["training"] is False and scope["model_quality_acceptance"] is False
            and scope["hypothesis_verdict"] == "NOT_TESTED" and scope["failed_cases_not_imputed"] is True,
            "Report scope or acceptance changed")
    rows = document["ordered_cases"]
    names = [r["case_id"] for r in rows]
    require(len(rows) == 70 and len(set(names)) == 70
            and all(re.fullmatch(r"PanTS_[0-9]{8}", x) for x in names), "Expected 70 unique case dispositions")
    failed = {r["case_id"]: r["disposition"] for r in rows if r["disposition"] != "COMPLETED"}
    require(failed == FAILURES, "Changed/missing declared admission failures")
    queue = []
    for r in rows:
        require(r["excluded"] is False, "Case excluded from requested denominator")
        pins = r["source_report_sha256"]
        require(isinstance(pins, dict) and pins and all(digest(v) for v in pins.values()), "Missing source report hashes")
        if r["disposition"] != "COMPLETED":
            require(set(pins) == {"failure"} and r["metrics"] is None and r["dice"] is None
                    and r["optimizer_updates"] == 0 and r["model_forwards"] == 0, "Failure metrics imputed")
            continue
        require(set(pins) == {"score", "result", "input-access"}, "Completed source report bindings")
        require(r["role"] == "exposed_development" and r["model_quality_acceptance"] is False
                and type(r["reused"]) is bool, "Case scope/reuse")
        volume = r["measurements"]["voxel_volume_ml"]
        require(type(volume) in (int, float) and math.isfinite(volume) and volume > 0, "Voxel volume")
        require(set(r["metrics"]) == {"lesion", "pancreas_parenchyma", "pancreas_lesion_union"}, "Missing native metrics")
        for metric in r["metrics"].values():
            check_metric(metric, volume)
        n, p, tp = check_metric(r["metrics"]["lesion"], volume)
        require(r["lesion_reference_state"] == ("positive" if n else "reference_empty"), "Reference state")
        count, hits, fp = check_components(r["lesion_components"], n, p, tp, volume)
        loc = r["localization"]
        _, outside_pancreas = check_coverage(loc["expanded_region_pancreas_coverage"])
        lesion_n, outside_lesion = check_coverage(loc["expanded_region_lesion_coverage"])
        require(lesion_n == n, "Coverage/lesion reference disagreement")
        assumed = r["unknown_reference_units_assumed_mm"]
        units = r["reference_units"]
        require(type(assumed) is bool and isinstance(units, list) and len(units) == 2
                and all(unit in ("mm", "unknown") for unit in units)
                and assumed == ("unknown" in units), "Unknown reference-unit policy")
        queue.append(dict(case_id=r["case_id"], positive=n > 0, dice=r["metrics"]["lesion"]["dice"],
                          reference_components=count, components_hit=hits, missed_components=count-hits,
                          false_positive_components=fp, false_positive_voxels=p-tp,
                          false_negative_voxels=n-tp, any_overlap=tp > 0, empty_alarm=n == 0 and p > 0,
                          pancreas_outside_region=outside_pancreas, lesion_outside_region=outside_lesion,
                          physical_units_assumed=assumed, reused=r["reused"], source_report_sha256=pins))
    pos = [r for r in queue if r["positive"]]
    neg = [r for r in queue if not r["positive"]]
    aggregate = dict(requested=70, completed=len(queue), failed=len(failed), excluded=0,
                     reused=sum(r["reused"] for r in queue), new_predictions=sum(not r["reused"] for r in queue),
                     positive_reference_n=len(pos), empty_reference_n=len(neg),
                     positive_macro_lesion_dice=sum(r["dice"] for r in pos)/len(pos) if pos else None,
                     positive_any_overlap_n=sum(r["any_overlap"] for r in pos),
                     empty_reference_alarm_n=sum(r["empty_alarm"] for r in neg),
                     reference_components_n=sum(r["reference_components"] for r in queue),
                     reference_components_hit_n=sum(r["components_hit"] for r in queue),
                     false_positive_components_n=sum(r["false_positive_components"] for r in queue))
    require(all(equal_number(document["aggregate"][k], v) for k, v in aggregate.items()), "Export aggregate disagreement")
    verification = document["verification"]
    owner = verification["evaluation_supervisor"]
    require(owner["success"] is True and owner["workers_reaped"] is True and owner["exit_code"] == 0,
            "Producer cleanup/success not reported")
    require(verification["output_backup_pairs"] == 710 and verification["preparation_backup_pairs"] == 12
            and verification["repository_pins_matched"] == 294
            and digest(verification["backup_audit_receipt_sha256"]), "Missing producer integrity evidence")
    ordered = lambda values, key: [r["case_id"] for r in sorted(values, key=key)]
    return dict(schema="prowl.autonomous70.metadata-review.v1", identities=identities, scope=scope,
                aggregate=aggregate, failures=failed, producer_verification=verification,
                local_verification="Transferred JSON hash and internal arithmetic only; no Windows artifact rehash",
                full_pancreas_region_cases=sum(r["pancreas_outside_region"] == 0 for r in queue),
                full_lesion_region_positive_cases=sum(r["lesion_outside_region"] == 0 for r in pos),
                assumed_reference_unit_cases=sum(r["physical_units_assumed"] for r in queue),
                review_queues=dict(missed_components=ordered([r for r in pos if r["missed_components"]],
                                     lambda r: (-r["missed_components"], r["dice"], r["case_id"])),
                                   lowest_positive_dice=ordered(pos, lambda r: (r["dice"], r["case_id"])),
                                   most_false_positive_voxels=ordered(queue, lambda r: (-r["false_positive_voxels"], r["case_id"]))),
                cases=queue, image_review_performed=False, inference_calls=0, optimizer_updates=0,
                limitations=["Exposed development; not independent generalization or clinical acceptance.",
                             "Probability equivalence remains UNQUALIFIED under the bounded exception.",
                             "Failures remain in the 70-case denominator, without imputed Dice.",
                             "Overlap means any shared voxel, not clinical lesion detection.",
                             f"{sum(r['physical_units_assumed'] for r in queue)} saved reference-unit assumptions limit physical measurements; no unit repair performed.",
                             "Coverage counts do not establish the spatial cause of an error; inspect images next."])


def markdown(result):
    a = result["aggregate"]
    mean_dice = "undefined" if a["positive_macro_lesion_dice"] is None else f"{a['positive_macro_lesion_dice']:.6f}"
    lines = ["# Autonomous baseline metadata review", "", "Descriptive saved-output review; no images inspected.", "",
             f"- Requested 70; completed {a['completed']}; failed {a['failed']} (not excluded or assigned zero Dice).",
             f"- Positive-case lesion Dice {mean_dice} on {a['positive_reference_n']} completed positives.",
             f"- Any overlap {a['positive_any_overlap_n']}/{a['positive_reference_n']}; empty-reference alarms {a['empty_reference_alarm_n']}/{a['empty_reference_n']}.",
             f"- Reference components hit {a['reference_components_hit_n']}/{a['reference_components_n']}; false-positive components {a['false_positive_components_n']}.",
             "", "## Review queue", "", "| Reason | Case | Lesion Dice | Missed components | FP voxels |", "| --- | --- | --- | --- | --- |"]
    cases = {r["case_id"]: r for r in result["cases"]}
    for reason, ids in result["review_queues"].items():
        for name in ids[:5]:
            r = cases[name]
            dice = "undefined (empty reference)" if r["dice"] is None else f"{r['dice']:.6f}"
            lines.append(f"| {reason} | {name} | {dice} | {r['missed_components']} | {r['false_positive_voxels']} |")
    lines.extend(["", "## Limits", ""] + ["- " + x for x in result["limitations"]])
    return "\n".join(lines) + "\n"
