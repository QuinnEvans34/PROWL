"""Evidence admission and claim boundaries; no clinical arrays or model calls."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.diagnostics.prepare_week06_comparison import (
    MAX_PROGRESS_BYTES, ROOT, build_packet, prepare, read_bounded, validate_progress,
)


@pytest.fixture
def node():
    runtime = os.environ.get("PROWL_TEST_NODE") or shutil.which("node")
    if not runtime:
        pytest.skip("Node runtime required for the shared metadata contract")
    return runtime


@pytest.fixture
def progress():
    return json.loads((ROOT / "configs/training-progress/lenovo-stunet-20261106.json").read_text())


@pytest.fixture
def kd():
    return json.loads((ROOT / "docs/capstone/operations/KD-DESCRIPTIVE-ANALYSIS-20261106.json").read_text())


def admit(progress, node):
    raw = json.dumps(progress).encode()
    sha = hashlib.sha256(raw).hexdigest()
    return validate_progress(raw, sha, node), sha


def test_real_saved_snapshot_is_separate_from_completed_kd(progress, kd, node):
    admitted, sha = admit(progress, node)
    report = build_packet(kd, admitted, sha)
    assert report["status"] == "PREPARATION_ONLY"
    assert report["model_ranking"] is report["promotion_verdict"] is None
    assert report["completed_kd"]["completed_validation_pairs"] == 12
    endpoint = report["completed_kd"]["endpoints"]["selected"]
    assert endpoint["arms"]["treatment"]["components_detected"] == 37
    assert endpoint["descriptive_dice_delta"] == kd["endpoints"]["selected"]["positive_macro_dice_delta"]
    assert not report["stunet_observation"]["complete_schedule_observed"]
    assert report["stunet_observation"]["best_observed_only"]["step"] == 6000
    assert any("equal counts" in x for x in report["comparison_requirements"])
    assert report["new_model_calls"] == report["new_optimizer_updates"] == report["mlflow_writes"] == 0
    assert report == build_packet(kd, admitted, sha)


def test_partial_validation_never_becomes_complete_score(progress, kd, node):
    progress["run"].update(phase="validating", step=8000,
                           validation={"step": 8000, "completed_cases": 69, "total_cases": 70})
    admitted, sha = admit(progress, node)
    report = build_packet(kd, admitted, sha)
    assert report["stunet_observation"]["latest_complete"]["step"] == 6000
    assert not report["stunet_observation"]["complete_schedule_observed"]


def test_even_complete_dashboard_does_not_qualify_closeout_or_comparison(progress, kd, node):
    progress["run"].update(phase="completed", step=12000)
    for step in (8000, 10000, 12000):
        point = copy.deepcopy(progress["validations"][-1])
        point["step"] = step
        progress["validations"].append(point)
    admitted, sha = admit(progress, node)
    report = build_packet(kd, admitted, sha)
    assert report["stunet_observation"]["complete_schedule_observed"]
    assert report["stunet_observation"]["closeout"] == "NOT_ESTABLISHED_BY_AGGREGATE_EXPORT"
    assert report["model_ranking"] is None
    assert len(report["comparison_requirements"]) == 8


@pytest.mark.parametrize("change", [
    lambda p: p["validations"][-1].update(completed_cases=69),
    lambda p: p["validations"][-1].update(lesion_dice=float("nan")),
    lambda p: p["validations"].append(copy.deepcopy(p["validations"][-1])),
    lambda p: p["run"].update(phase="completed", step=12000),
    lambda p: p.update(case_ids=["not-an-aggregate"]),
])
def test_shared_contract_rejects_invalid_or_private_metadata(progress, node, change):
    change(progress)
    with pytest.raises(ValueError, match="shared progress contract"):
        admit(progress, node)


@pytest.mark.parametrize("field,value", [
    ("run_id", "a-different-experiment"),
    ("receipt_sha256", "0" * 64),
    ("mlflow_run_id", "another-run"),
])
def test_well_formed_but_unrelated_identity_refused(progress, node, field, value):
    progress["source"][field] = value
    with pytest.raises(ValueError, match="authorized STU-Net"):
        admit(progress, node)


def test_hash_mismatch_precedes_runtime_execution(progress):
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        validate_progress(json.dumps(progress).encode(), "0" * 64, "must-not-execute")


def test_bounded_inputs(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_bytes(b"x" * (MAX_PROGRESS_BYTES + 1))
    with pytest.raises(ValueError, match="byte limit"):
        read_bounded(path, MAX_PROGRESS_BYTES)
    with pytest.raises(ValueError, match="byte limit"):
        validate_progress(path.read_bytes(), "0" * 64, "must-not-execute")


def test_altered_kd_report_refused_before_progress_runtime(tmp_path):
    kd_path, export = tmp_path / "kd.json", tmp_path / "export.json"
    kd_path.write_text('{}')
    export.write_text('{}')
    with pytest.raises(ValueError, match="Wrong completed report"):
        prepare(kd_path, export, "0" * 64, "must-not-execute")


def test_cli_preserves_existing_output_without_reading_inputs(tmp_path):
    output = tmp_path / "retained.json"
    output.write_text("original review\n")
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/diagnostics/prepare_week06_comparison.py"),
        "--kd-report", str(tmp_path / "absent-kd"), "--stunet-export", str(tmp_path / "absent-export"),
        "--stunet-sha256", "0" * 64, "--node", "must-not-execute", "--output", str(output),
    ], env=env, capture_output=True, timeout=10)
    assert result.returncode != 0
    assert b"Preserve the existing preparation" in result.stderr
    assert output.read_text() == "original review\n"
