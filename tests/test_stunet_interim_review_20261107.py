"""Saved metadata arithmetic and failure boundaries; no image/model fixtures."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.diagnostics.review_stunet_interim_20261107 import MAX_BYTES, summarize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/capstone/coordination/LENOVO-STUNET-NATIVE-METADATA-20261107.json"
SHA = "9528af9e5817f74d3a813c096b261d1e80b4ac688773697c272cd4e1f0e971a9"


@pytest.fixture
def export():
    return json.loads(SOURCE.read_bytes())


def review(export):
    raw = json.dumps(export).encode()
    return summarize(raw, hashlib.sha256(raw).hexdigest())


def test_real_export_reproduces_complete_series_and_derived_errors():
    result = summarize(SOURCE.read_bytes(), SHA)
    assert result["status"] == "INTERIM_DESCRIPTIVE_ONLY"
    assert [r["step"] for r in result["series"]] == [2000, 4000, 6000]
    last = result["series"][-1]
    assert last["summary"]["positive_macro_dice"] == pytest.approx(.3471818046280159)
    assert last["summary"]["false_negative_voxels"] == 91076
    assert last["summary"]["positive_false_positive_voxels"] == 148483
    assert last["summary"]["empty_false_positive_voxels"] == 73002
    assert last["summary"]["overlapped_reference_components"] == 36
    assert last["summary"]["missed_reference_components"] == 9
    assert last["size_bands"]["small"]["cases"] == 5
    assert last["size_bands"]["small"]["positive_macro_dice"] == pytest.approx(.047819846313092225)
    assert len(last["cases"]) == 70
    assert result["new_model_calls"] == result["new_optimizer_updates"] == result["mlflow_writes"] == 0
    assert "not established" in result["cross_model_reference_equivalence"]
    assert result == summarize(SOURCE.read_bytes(), SHA)


def test_undefined_precision_and_empty_dice_remain_null(export):
    result = review(export)
    rows = result["series"][-1]["cases"]
    missed = next(r for r in rows if r["case_id"] == "PanTS_00007868")
    assert missed["target_voxels"] > 0 and missed["predicted_voxels"] == 0
    assert missed["dice"] == missed["recall"] == 0
    assert missed["precision"] is None
    empty = next(r for r in rows if not r["target_voxels"] and not r["predicted_voxels"])
    assert empty["dice"] is empty["precision"] is empty["recall"] is None
    assert result["series"][-1]["summary"]["precision_defined_positive_cases"] == 35


def test_within_run_changes_preserve_positive_denominator(export):
    result = review(export)
    delta = result["within_run_changes"][-1]
    assert (delta["better"], delta["worse"], delta["unchanged"]) == (25, 6, 5)
    assert delta["new_complete_misses"] == ["PanTS_00007868"]
    assert "PanTS_00006903" in delta["recovered_complete_misses"]
    assert result["persistent_complete_misses"] == [
        "PanTS_00001823", "PanTS_00002514", "PanTS_00004681", "PanTS_00006755"]


@pytest.mark.parametrize("mutate,error", [
    (lambda p: p["reports"][-1]["cases_as_saved"].pop(), "native cohort"),
    (lambda p: p["reports"][-1]["cases_as_saved"].append(copy.deepcopy(p["reports"][-1]["cases_as_saved"][0])), "native cohort"),
    (lambda p: p["reports"].reverse(), "validation sequence"),
    (lambda p: p.update(ready_sha256="0" * 64), "experiment identity"),
    (lambda p: p["metric_producer_pins_as_recorded"].update({"src\\training\\pants_native_evaluation.py": "0" * 64}), "producer changed"),
    (lambda p: p["reports"][0].update(independent_report_backup_matches=False), "receipt mismatch"),
    (lambda p: p["reports"][0]["summary_as_saved"].update(lesion_dice=.99), "summary"),
    (lambda p: p["reports"][0]["cases_as_saved"][0]["metrics"]["lesion"].update(true_positive=-1), "overlap counts"),
    (lambda p: p["reports"][0]["cases_as_saved"][0]["metrics"]["lesion"].update(dice=.99), "Dice"),
    (lambda p: p["reports"][0]["cases_as_saved"][0]["metrics"].update(voxel_mm3=2.), "geometry"),
    (lambda p: p["reports"][0]["cases_as_saved"][0]["metrics"].update(size_band="small"), "Size band"),
    (lambda p: p["reports"][0]["cases_as_saved"][0]["metrics"].update(detected_components=99), "component counts"),
    (lambda p: p["reports"][0]["cases_as_saved"][0].update(gaps=1), "coverage"),
])
def test_invalid_evidence_refused_even_with_explicit_new_export_hash(export, mutate, error):
    mutate(export)
    with pytest.raises(ValueError, match=error):
        review(export)


def test_native_reference_change_refused(export):
    row = export["reports"][-1]["cases_as_saved"][0]
    counts = row["metrics"]["pancreas"]
    counts["target_voxels"] += 1
    counts["dice"] = 2 * counts["true_positive"] / (counts["target_voxels"] + counts["predicted_voxels"])
    with pytest.raises(ValueError, match="reference changed"):
        review(export)


def test_bound_and_digest_refusal():
    with pytest.raises(ValueError, match="Wrong native export"):
        summarize(SOURCE.read_bytes() + b" ", SHA)
    with pytest.raises(ValueError, match="byte limit"):
        summarize(b"x" * (MAX_BYTES + 1), SHA)


def test_cli_creates_fresh_actual_report_and_preserves_it(tmp_path):
    output = tmp_path / "review.json"
    command = [sys.executable, str(ROOT / "scripts/diagnostics/review_stunet_interim_20261107.py"),
               "--export", str(SOURCE), "--sha256", SHA, "--output", str(output)]
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    first = subprocess.run(command, capture_output=True, env=env, timeout=10)
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    assert json.loads(original)["series"][-1]["summary"]["empty_alarm_cases"] == 26
    second = subprocess.run(command, capture_output=True, env=env, timeout=10)
    assert second.returncode != 0 and b"Preserve existing review" in second.stderr
    assert output.read_bytes() == original
