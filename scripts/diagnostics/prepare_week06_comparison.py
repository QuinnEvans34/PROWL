"""Prepare separate, source-bound development summaries; never rank or launch models."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from scripts.diagnostics.review_completed_kd_20261106 import summarize

ROOT = Path(__file__).resolve().parents[2]
STUNET_RUN = "pants_stunet_base_transfer_12k_20261106_launch02"
STUNET_RECEIPT = "59e8188d60d70840eabb8752f0be5d5c1f818bc51e3cdcf81d16c74c79cf3e68"
STUNET_MLFLOW = "243ccf3f71c34417be60362af35187d1"
MAX_PROGRESS_BYTES = 128 * 1024
MAX_KD_BYTES = 5 * 1024 * 1024
VALIDATE_JS = """
import fs from 'node:fs';
const { validateTrainingProgress } = await import(process.argv[1]);
const value = validateTrainingProgress(JSON.parse(fs.readFileSync(0, 'utf8')));
process.stdout.write(JSON.stringify(value));
"""
ENDPOINT_FIELDS = (
    "step", "cases", "positive_cases", "negative_cases", "positive_macro_dice",
    "positive_macro_recall", "positive_macro_precision", "detected", "complete_misses",
    "negative_alarms", "total_false_negative_voxels", "total_false_positive_voxels",
    "components_detected", "reference_components", "pancreas_macro_dice",
)


def read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Metadata input exceeds byte limit")
    return raw


def validate_progress(raw: bytes, expected_sha256: str, node: str) -> dict:
    if len(raw) > MAX_PROGRESS_BYTES:
        raise ValueError("Training export exceeds byte limit")
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise ValueError("An explicit lowercase SHA256 is required")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Training export SHA256 mismatch")
    # Reuse the UI's admission contract, including full validation denominators.
    completed = subprocess.run(
        [node, "--input-type=module", "-e", VALIDATE_JS,
         (ROOT / "ui/src/lib/trainingProgress.js").as_uri()],
        input=raw, capture_output=True, timeout=10, check=False,
    )
    if completed.returncode:
        raise ValueError("Training export failed the shared progress contract")
    progress = json.loads(completed.stdout)
    source, run = progress["source"], progress["run"]
    expected_cohort = {"training_cases": 1333, "development_cases": 70,
                       "positive_cases": 36, "reference_empty_cases": 34}
    if (source["machine"] != "Lenovo" or source["run_id"] != STUNET_RUN
            or source["receipt_sha256"] != STUNET_RECEIPT
            or source["mlflow_run_id"] != STUNET_MLFLOW
            or run["target_steps"] != 12000 or run["validation_interval"] != 2000
            or progress["cohort"] != expected_cohort):
        raise ValueError("Export is not the authorized STU-Net run identity")
    return progress


def build_packet(kd: dict, progress: dict, export_sha256: str) -> dict:
    """Inputs are admitted by summarize/validate_progress before this projection."""
    points = progress["validations"]
    endpoints = {}
    for name in ("selected", "terminal"):
        original = kd["endpoints"][name]
        endpoints[name] = {
            "arms": {arm: {field: original["summaries"][arm][field]
                            for field in ENDPOINT_FIELDS}
                     for arm in ("control", "treatment")},
            "descriptive_dice_delta": original["positive_macro_dice_delta"],
            "positive_cases_better": original["better"],
            "positive_cases_worse": original["worse"],
            "positive_cases_unchanged": original["unchanged"],
        }
    return {
        "schema": "prowl.week06.comparison-preparation.v1",
        "status": "PREPARATION_ONLY",
        "model_ranking": None,
        "promotion_verdict": None,
        "independent_patient_inference": "withheld; linkage unresolved",
        "new_model_calls": 0, "new_optimizer_updates": 0, "mlflow_writes": 0,
        "completed_kd": {
            "source_sha256": kd["input_report_sha256"], "scope": kd["scope"],
            "planned_steps": 24000, "completed_validation_pairs": len(kd["series"]),
            "series": kd["series"], "endpoints": endpoints,
            "qualification": "completed descriptive review; no practical-acceptance verdict",
            "historical_failures": "original control cleanup failure retained; not rewritten",
        },
        "stunet_observation": {
            "source_sha256": export_sha256, "observed_at": progress["observed_at"],
            "source": progress["source"], "run": progress["run"],
            "cohort_counts": progress["cohort"], "completed_validations": points,
            "latest_complete": points[-1] if points else None,
            "best_observed_only": max(points, key=lambda p: p["lesion_dice"]) if points else None,
            "complete_schedule_observed": [p["step"] for p in points] == list(range(2000, 12001, 2000)),
            "closeout": "NOT_ESTABLISHED_BY_AGGREGATE_EXPORT",
        },
        "comparison_requirements": [
            "STU-Net: complete 12k/six full native validations and selected/terminal per-case errors",
            "STU-Net: verify producing pins, checkpoint/independent backups, MLflow closeout and worker/GPU cleanup",
            "Verify exact case/reference identities and metric conventions; equal counts do not establish alignment",
            "Document changed architecture, initialization, horizon, geometry and input policy; no isolated causal effect",
            "Resolve patient/source/pretraining evidence or explicitly restrict the claim to exposed exploratory development",
            "Review KD-specific saved spatial errors; aggregate totals do not establish anatomical causes",
            "G4 admitted autonomous baseline before selecting the formal required controlled comparison",
            "Freeze prospective hypothesis, factors, cohort, selection/endpoints, guards, budget and failure accounting before new compute",
        ],
        "excluded_from_training_ranking": {
            "universal_four_positive_screen": "publisher-trained inference only; no PROWL training or negative specificity",
            "autonomous_70": "63 scored + seven failures; different CT-only cascade and exposed conditional denominator",
        },
    }


def prepare(kd_path: Path, progress_path: Path, expected_sha256: str, node: str) -> dict:
    kd_raw = read_bounded(kd_path, MAX_KD_BYTES)
    progress_raw = read_bounded(progress_path, MAX_PROGRESS_BYTES)
    kd = summarize(kd_raw)
    progress = validate_progress(progress_raw, expected_sha256, node)
    result = build_packet(kd, progress, expected_sha256)
    if (read_bounded(kd_path, MAX_KD_BYTES) != kd_raw
            or read_bounded(progress_path, MAX_PROGRESS_BYTES) != progress_raw):
        raise ValueError("Input changed during preparation")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kd-report", type=Path, required=True)
    parser.add_argument("--stunet-export", type=Path, required=True)
    parser.add_argument("--stunet-sha256", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve the existing preparation; choose a fresh output")
    result = prepare(args.kd_report, args.stunet_export, args.stunet_sha256, args.node)
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    with args.output.open("x") as stream:
        stream.write(encoded)
    print(json.dumps({"output": str(args.output), "status": result["status"],
                      "kd_validation_pairs": result["completed_kd"]["completed_validation_pairs"],
                      "stunet_validation_points": len(result["stunet_observation"]["completed_validations"])}))


if __name__ == "__main__":
    main()
